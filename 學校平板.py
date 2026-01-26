# =========================
# 蘭州國中 平板借用系統
# 完整 400+ 行版本（部分歸還更新剩餘台數、全數歸還刪除紀錄）
# =========================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import re

# =========================
# 基本設定
# =========================
APP_TITLE = "蘭州國中114學年度 第1學期 平板借用系統"
TOTAL_TABLETS = 101
MAX_SINGLE_BORROW = 50
MAX_BORROW_RECORDS = 7  # 借用列表最多 7 筆

FONT_TITLE = ("Arial", 20, "bold")
FONT_HEADER = ("Arial", 16, "bold")
FONT = ("Arial", 16)

BG_COLOR = "#F4F6F8"
CARD_COLOR = "#FFFFFF"

# =========================
# 教師與班級資料
# =========================
TEACHERS = [
    "本孚","幃捷","舒婷","珊瑩","郁均","李安","佳佳","孟璇","婉湄","逸銓",
    "惠如","百育","峻維","品妤","彥宏","勇宏","盈盈","斐雁","淨瑜","俊萱",
    "裕貞","慧娟","晉邦","迪文"
]

CLASSES = [
    "701","702","703","704","705",
    "801","802","803","804",
    "901","902","903"
]

# =========================
# Google Sheet 連線
# =========================
def connect_google_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    base = os.path.dirname(os.path.abspath(__file__))
    creds_path = os.path.join(base, "service_account.json")
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    return client.open("ipadinnout").sheet1

sheet = connect_google_sheet()

# =========================
# 主視窗
# =========================
root = tk.Tk()
root.title(APP_TITLE)
root.state("zoomed")

# =========================
# Canvas 可滾動
# =========================
canvas = tk.Canvas(root, bg=BG_COLOR)
canvas.pack(side="left", fill="both", expand=True)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")
canvas.configure(yscrollcommand=scrollbar.set)
content = tk.Frame(canvas, bg=BG_COLOR)
canvas.create_window((0,0), window=content, anchor="nw")

def on_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
    canvas.itemconfig("all", width=canvas.winfo_width())

content.bind("<Configure>", on_configure)
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
canvas.bind_all("<MouseWheel>", _on_mousewheel)

# =========================
# 時間顯示
# =========================
def update_time():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_label.config(text=now)
    root.after(1000, update_time)

# =========================
# 標題區
# =========================
header = tk.Frame(content, bg=BG_COLOR)
header.pack(fill="x", pady=10)
time_label = tk.Label(header, font=("Arial", 14), fg="gray", bg=BG_COLOR)
time_label.pack()
title_label = tk.Label(header, text=APP_TITLE, font=FONT_TITLE, bg=BG_COLOR)
title_label.pack(pady=(5,10))
update_time()

# =========================
# 工具函式
# =========================
def get_all_records():
    return sheet.get_all_values()[1:]

def get_remaining_tablets():
    records = get_all_records()
    borrowed = 0
    broken = 0
    for r in records:
        if len(r) < 3:
            continue
        if r[0] == "問題平板":
            broken += 1
        else:
            try:
                total_borrowed = int(r[2])
                returned = int(r[8]) if len(r) > 8 and r[8].isdigit() else 0
                borrowed += total_borrowed - returned
            except:
                continue
    return max(TOTAL_TABLETS - borrowed - broken, 0)  # 不可為負

def has_active_borrow(teacher):
    for r in get_all_records():
        if len(r) >= 3 and r[0] == teacher and (int(r[2]) - (int(r[8]) if len(r) > 8 and r[8].isdigit() else 0)) > 0:
            return True
    return False

def borrow_records_count():
    count = 0
    for r in get_all_records():
        if len(r) >= 3 and r[0] != "問題平板":
            total_borrowed = int(r[2])
            returned = int(r[8]) if len(r) > 8 and r[8].isdigit() else 0
            if total_borrowed - returned > 0:
                count += 1
    return count

# =========================
# 借用卡片
# =========================
borrow_card = tk.Frame(content, bg=CARD_COLOR, padx=20, pady=15)
borrow_card.pack(fill="x", padx=20, pady=10)
tk.Label(borrow_card, text="借用人", font=FONT_HEADER, bg=CARD_COLOR).pack(anchor="w")
teacher_var = tk.StringVar()
teacher_cb = ttk.Combobox(borrow_card, values=TEACHERS + ["其他"], state="readonly", font=FONT, textvariable=teacher_var)
teacher_cb.pack(fill="x")
other_teacher_entry = tk.Entry(borrow_card, font=FONT, state="disabled")
other_teacher_entry.pack(fill="x", pady=5)
def on_teacher_change(e=None):
    if teacher_var.get() == "其他":
        other_teacher_entry.config(state="normal")
        other_teacher_entry.focus()
    else:
        other_teacher_entry.delete(0, tk.END)
        other_teacher_entry.config(state="disabled")
teacher_cb.bind("<<ComboboxSelected>>", on_teacher_change)

tk.Label(borrow_card, text="班級", font=FONT_HEADER, bg=CARD_COLOR).pack(anchor="w", pady=(10,0))
class_var = tk.StringVar()
class_cb = ttk.Combobox(borrow_card, values=CLASSES, state="readonly", font=FONT, textvariable=class_var)
class_cb.pack(fill="x")
tk.Label(borrow_card, text=f"借用台數（上限 {MAX_SINGLE_BORROW}）", font=FONT_HEADER, bg=CARD_COLOR).pack(anchor="w", pady=(10,0))
count_entry = tk.Entry(borrow_card, font=FONT)
count_entry.pack(fill="x")
remaining_label = tk.Label(borrow_card, text=f"目前剩餘台數：{get_remaining_tablets()}", font=FONT, bg=CARD_COLOR, fg="blue")
remaining_label.pack(anchor="e", pady=5)

# =========================
# 借用送出
# =========================
def submit_borrow():
    if borrow_records_count() >= MAX_BORROW_RECORDS:
        messagebox.showerror("錯誤", f"借用資料筆數不可超過 {MAX_BORROW_RECORDS} 筆")
        return
    teacher = teacher_var.get()
    if teacher == "其他":
        teacher = other_teacher_entry.get().strip()
    classroom = class_var.get()
    count = count_entry.get().strip()
    if not teacher or not classroom:
        messagebox.showerror("錯誤", "借用人與班級不可空白")
        return
    if has_active_borrow(teacher):
        messagebox.showerror("錯誤", "此借用人尚有未歸還紀錄")
        return
    if not count.isdigit():
        messagebox.showerror("錯誤", "台數必須為數字")
        return
    count = int(count)
    if count < 1 or count > MAX_SINGLE_BORROW:
        messagebox.showerror("錯誤", "單次借用台數超過限制")
        return
    remaining = get_remaining_tablets()
    if count > remaining:
        messagebox.showerror("錯誤", f"班級剩餘可借台數不足（剩餘 {remaining} 台）")
        return
    start = datetime.now()
    end = start + timedelta(minutes=45)
    sheet.append_row([
        teacher, classroom, count,
        start.strftime("%Y-%m-%d %H:%M:%S"), "",  # 歸還時間
        end.strftime("%Y-%m-%d %H:%M:%S"), "",  # 簽名, 實際歸還
    ])
    count_entry.delete(0, tk.END)
    refresh_borrow_table()
    refresh_problem_table()

tk.Button(borrow_card, text="送出借用", font=FONT, command=submit_borrow).pack(pady=10)
tk.Button(borrow_card, text="刷新借用列表", font=FONT, command=lambda: refresh_borrow_table()).pack(pady=5)
root.bind("<Return>", lambda e: submit_borrow())

# =========================
# 借用中表格
# =========================
borrow_card2 = tk.Frame(content, bg=CARD_COLOR, padx=15, pady=10)
borrow_card2.pack(fill="both", expand=True, padx=20, pady=10)
borrow_table = ttk.Treeview(
    borrow_card2, columns=("teacher","class","borrowed","remain","end"), show="headings", height=10
)
borrow_table.pack(fill="both", expand=True)
for col, txt in zip(
    ("teacher","class","borrowed","remain","end"),
    ("借用人","班級","借出台數","未歸還","到期時間")
):
    borrow_table.heading(col, text=txt)

def refresh_borrow_table():
    borrow_table.delete(*borrow_table.get_children())
    now = datetime.now()
    for idx, r in enumerate(get_all_records(), start=2):
        if len(r) < 3 or r[0] == "問題平板":
            continue
        try:
            borrowed = int(r[2])
            returned = int(r[8]) if len(r) > 8 and r[8].isdigit() else 0
            remain = borrowed - returned
            if remain <= 0:
                continue  # 全數歸還，不顯示
            end_time = datetime.strptime(r[5], "%Y-%m-%d %H:%M:%S")
            item_id = str(idx)
            borrow_table.insert("", "end", iid=item_id, values=(r[0], r[1], borrowed, remain, r[5]))
            if now >= end_time:
                borrow_table.item(item_id, tags=("overdue",))
        except:
            continue
    borrow_table.tag_configure("overdue", background="#FFCCCC")
    remaining_label.config(text=f"目前剩餘台數：{get_remaining_tablets()}")

# =========================
# 歸還彈窗（部分歸還會扣除剩餘台數）
# =========================
def return_selected():
    item = borrow_table.focus()
    if not item:
        return
    row = int(item)
    orig_count = int(sheet.cell(row, 3).value)

    popup = tk.Toplevel(root)
    popup.title("歸還平板")
    popup.geometry("300x250")
    popup.grab_set()

    tk.Label(popup, text=f"原借用台數：{orig_count}", font=FONT).pack(pady=5)
    tk.Label(popup, text="實際歸還台數：", font=FONT).pack(pady=5)
    actual_var = tk.StringVar(value=str(orig_count))
    actual_entry = tk.Entry(popup, textvariable=actual_var, font=FONT)
    actual_entry.pack()
    tk.Label(popup, text="簽名：", font=FONT).pack(pady=5)
    sign_var = tk.StringVar()
    sign_entry = tk.Entry(popup, textvariable=sign_var, font=FONT)
    sign_entry.pack()

    def confirm_return():
        actual = actual_var.get().strip()
        sign = sign_var.get().strip()
        if not actual.isdigit() or int(actual) < 1:
            messagebox.showerror("錯誤", "歸還台數必須為正整數")
            return
        if not sign:
            messagebox.showerror("錯誤", "簽名不可空白")
            return

        actual_int = int(actual)
        already_returned = int(sheet.cell(row, 8).value or 0)

        # 更新簽名與歸還時間
        sheet.update_cell(row, 7, sign)
        sheet.update_cell(row, 5, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        remaining = orig_count - (already_returned + actual_int)
        if remaining > 0:
            # 部分歸還 → 更新已歸還欄位
            sheet.update_cell(row, 8, already_returned + actual_int)
        else:
            # 全數歸還 → 刪除該筆借用紀錄
            sheet.delete_rows(row)

        refresh_borrow_table()
        popup.destroy()

    tk.Button(popup, text="確認歸還", font=FONT, command=confirm_return).pack(pady=10)

# =========================
# 續借功能
# =========================
def extend_selected():
    item = borrow_table.focus()
    if not item:
        return
    row = int(item)
    old_end = sheet.cell(row, 6).value
    new_end = datetime.strptime(old_end, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=45)
    sheet.update_cell(row, 6, new_end.strftime("%Y-%m-%d %H:%M:%S"))
    refresh_borrow_table()

btn_frame = tk.Frame(borrow_card2, bg=CARD_COLOR)
btn_frame.pack(pady=5)
tk.Button(btn_frame, text="歸還", font=FONT, command=return_selected).pack(side="left", padx=5)
tk.Button(btn_frame, text="續借", font=FONT, command=extend_selected).pack(side="left", padx=5)

# =========================
# 問題平板登記
# =========================
problem_card = tk.Frame(content, bg=CARD_COLOR, padx=20, pady=15)
problem_card.pack(fill="x", padx=20, pady=10)
tk.Label(problem_card, text="問題平板（Lcjh-00 ~ Lcjh-100）", font=FONT_HEADER, bg=CARD_COLOR).pack(anchor="w")
problem_entry = tk.Entry(problem_card, font=FONT)
problem_entry.pack(fill="x", pady=5)

def submit_problem():
    code = problem_entry.get().strip()
    match = re.fullmatch(r"Lcjh-(\d{1,3})", code)
    if not match:
        messagebox.showerror("錯誤", "請輸入正確格式 Lcjh-xx（00~100）")
        return
    number = int(match.group(1))
    if number < 0 or number > 100:
        messagebox.showerror("錯誤", "平板編號必須介於 00~100")
        return
    records = get_all_records()
    if any(len(r)>6 and r[0]=="問題平板" and r[6]==code for r in records):
        messagebox.showerror("錯誤", "此平板已登記")
        return
    sheet.append_row(["問題平板", "", "", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", code, ""])
    problem_entry.delete(0, tk.END)
    refresh_problem_table()
    refresh_borrow_table()

tk.Button(problem_card, text="登記問題平板", font=FONT, command=submit_problem).pack(pady=5)
problem_table = ttk.Treeview(problem_card, columns=("code","time"), show="headings", height=5)
problem_table.pack(fill="x")
problem_table.heading("code", text="平板編號")
problem_table.heading("time", text="時間")
def remove_problem():
    item = problem_table.focus()
    if not item:
        return
    row = int(item)
    sheet.delete_rows(row)
    refresh_problem_table()
    refresh_borrow_table()
tk.Button(problem_card, text="消除問題平板", font=FONT, command=remove_problem).pack(pady=5)
def refresh_problem_table():
    problem_table.delete(*problem_table.get_children())
    for idx, r in enumerate(get_all_records(), start=2):
        if len(r) > 6 and r[0] == "問題平板":
            problem_table.insert("", "end", iid=str(idx), values=(r[6], r[3]))

# =========================
# 借用到期提醒
# =========================
def check_overdue():
    now = datetime.now()
    for idx, r in enumerate(get_all_records(), start=2):
        if len(r) < 6 or r[0] == "問題平板":
            continue
        returned = int(r[8]) if len(r) > 8 and r[8].isdigit() else 0
        if returned < int(r[2]):
            end_time = datetime.strptime(r[5], "%Y-%m-%d %H:%M:%S")
            if now >= end_time:
                messagebox.showwarning(
                    "借用到期提醒",
                    f"借用人：{r[0]}\n班級：{r[1]}\n台數：{r[2]}\n借用已到期！"
                )
    root.after(60000, check_overdue)

check_overdue()
refresh_borrow_table()
refresh_problem_table()
root.mainloop()
