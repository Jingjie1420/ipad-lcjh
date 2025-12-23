import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# =========================
# 字體設定
# =========================
FONT_TITLE = ("Arial", 20, "bold")
FONT_HEADER = ("Arial", 16, "bold")
FONT = ("Arial", 16)

BG_COLOR = "#F4F6F8"
CARD_COLOR = "#FFFFFF"
BTN_COLOR = "#4A90E2"

TOTAL_TABLETS = 103
ALL_TABLETS = [f"Lcjh-{i:02d}" for i in range(TOTAL_TABLETS)]

TEACHERS = [
    "本孚","幃捷","舒婷","珊瑩","郁均","李安","佳佳","孟璇","婉湄","逸銓",
    "惠如","百育","峻維","品妤","彥宏","勇宏","盈盈","斐雁","淨瑜","俊萱",
    "裕貞","慧娟","晉邦","迪文"
]

# =========================
# Google Sheet
# =========================
def connect_google_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    base = os.path.dirname(os.path.abspath(__file__))
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        os.path.join(base, "service_account.json"), scope
    )
    return gspread.authorize(creds).open("ipadinnout").sheet1

sheet = connect_google_sheet()

# =========================
# 左上角時間
# =========================
def update_time():
    time_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    root.after(1000, update_time)

# =========================
# 問題平板當天防呆
# =========================
def is_broken_today(code):
    today = datetime.now().strftime("%Y-%m-%d")
    for r in sheet.get_all_values()[1:]:
        if r[0] == "問題平板" and r[6] == code and r[2][:10] == today:
            return True
    return False

# =========================
# 計算借用中剩餘台數
# =========================
def get_remaining_tablets():
    records = sheet.get_all_values()[1:]
    borrowed = sum(int(r[1]) for r in records if r[0] != "問題平板" and r[4] == "")
    broken = sum(1 for r in records if r[0] == "問題平板")
    return TOTAL_TABLETS - borrowed - broken

# =========================
# 借用中紀錄表格
# =========================
def refresh_borrow_table():
    for row in borrow_table.get_children():
        borrow_table.delete(row)

    records = sheet.get_all_values()[1:]
    for idx, row in enumerate(records, start=2):
        if row[0] != "問題平板" and row[4] == "":
            end_time_str = row[3]
            try:
                end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
                is_overdue = datetime.now() > end_time
            except:
                is_overdue = False

            remaining = get_remaining_tablets()
            borrow_table.insert(
                "", "end", iid=idx,
                values=(row[0], row[1], TOTAL_TABLETS, remaining, row[3]),
                tags=("overdue",) if is_overdue else ()
            )

    borrow_table.tag_configure("overdue", foreground="red")

# =========================
# 借用
# =========================
def submit_borrow():
    teacher = teacher_combobox.get().strip()
    count = count_entry.get().strip()

    if not teacher or not count:
        messagebox.showerror("錯誤", "請填寫借用人與台數")
        return
    if not count.isdigit() or not (1 <= int(count) <= get_remaining_tablets()):
        messagebox.showerror("錯誤", f"台數必須為 1~{get_remaining_tablets()}")
        return

    start = datetime.now()
    end = start + timedelta(minutes=45)

    sheet.append_row([
        teacher, count,
        start.strftime("%Y-%m-%d %H:%M:%S"),
        end.strftime("%Y-%m-%d %H:%M:%S"),
        "", "", ""
    ])

    count_entry.delete(0, tk.END)
    refresh_borrow_table()

# =========================
# 歸還（支援部分歸還）
# =========================
def return_tablet_dialog(row):
    dialog = tk.Toplevel(root)
    dialog.title("歸還平板")

    borrow_count = sheet.cell(row, 2).value
    max_return = int(borrow_count)

    tk.Label(dialog, text="歸還台數:", font=FONT).pack(padx=10, pady=5)
    return_count = tk.Entry(dialog, font=FONT)
    return_count.insert(0, str(max_return))
    return_count.pack(padx=10, pady=5)

    tk.Label(dialog, text="簽名:", font=FONT).pack(padx=10, pady=5)
    signature = tk.Entry(dialog, font=FONT)
    signature.pack(padx=10, pady=5)

    def confirm_return():
        val = return_count.get().strip()
        if not val.isdigit():
            messagebox.showerror("錯誤", "歸還台數必須是數字")
            return

        return_num = int(val)
        if return_num < 1 or return_num > max_return:
            messagebox.showerror("錯誤", f"歸還台數需介於 1~{max_return}")
            return

        remain = max_return - return_num

        if remain == 0:
            sheet.update_cell(row, 5, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        else:
            sheet.update_cell(row, 2, str(remain))

        dialog.destroy()
        refresh_borrow_table()

    tk.Button(dialog, text="確認歸還", font=FONT, command=confirm_return).pack(pady=10)

# =========================
# 續借
# =========================
def extend_borrow(row):
    current_end = sheet.cell(row, 4).value
    new_end = datetime.strptime(current_end, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=45)
    sheet.update_cell(row, 4, new_end.strftime("%Y-%m-%d %H:%M:%S"))
    refresh_borrow_table()

# =========================
# 問題平板
# =========================
def submit_broken():
    code = broken_entry.get().strip()
    if not code:
        return
    if is_broken_today(code):
        messagebox.showerror("錯誤", "今天已填過此編號")
        return

    sheet.append_row([
        "問題平板", 1,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "", "", "", code
    ])

    broken_entry.delete(0, tk.END)
    refresh_borrow_table()

def remove_broken(code):
    rows = sheet.get_all_values()
    for i in range(1, len(rows)):
        if rows[i][0] == "問題平板" and rows[i][6] == code:
            sheet.delete_rows(i + 1)
            break
    refresh_borrow_table()

# =========================
# UI
# =========================
root = tk.Tk()
root.title("蘭州國中114學年度 第1學期 平板借用系統")
root.geometry("800x900")
root.configure(bg=BG_COLOR)

# =========================
# 上方標題列
# =========================
top_bar = tk.Frame(root, bg=BG_COLOR)
top_bar.pack(fill="x", pady=5)

time_label = tk.Label(top_bar, bg=BG_COLOR, fg="gray", font=("Arial", 14))
time_label.pack(anchor="center", pady=(0,0))

title_label = tk.Label(top_bar, text="蘭州國中114學年度 第1學期 平板借用系統",
                       font=FONT_TITLE, bg=BG_COLOR)
title_label.pack(anchor="center", pady=(5, 0))

update_time()

# =========================
# 借用卡片
# =========================
card1 = tk.Frame(root, bg=CARD_COLOR, padx=20, pady=15)
card1.pack(fill="x", padx=20, pady=(60,10))

tk.Label(card1, text="借用人", font=FONT_HEADER, bg=CARD_COLOR).pack(anchor="w")
teacher_combobox = ttk.Combobox(card1, values=TEACHERS, font=FONT)
teacher_combobox.pack(fill="x")

tk.Label(card1, text="借用台數", font=FONT_HEADER, bg=CARD_COLOR).pack(anchor="w")
count_entry = tk.Entry(card1, font=FONT)
count_entry.pack(fill="x")

tk.Button(card1, text="送出借用", font=FONT, command=submit_borrow).pack(pady=10)

tk.Label(card1, text="問題平板編號", font=FONT_HEADER, bg=CARD_COLOR).pack(anchor="w")
broken_entry = tk.Entry(card1, font=FONT)
broken_entry.pack(fill="x")
tk.Button(card1, text="送出問題平板", font=FONT, command=submit_broken).pack(pady=5)

# =========================
# 借用中紀錄表格
# =========================
card2 = tk.Frame(root, bg=CARD_COLOR, padx=15, pady=10)
card2.pack(fill="both", expand=True, padx=20, pady=10)

tk.Label(card2, text="借用中紀錄", font=FONT_HEADER, bg=CARD_COLOR).pack(anchor="w")

# 調整 Treeview 文字大小
style = ttk.Style()
style.configure("Treeview", font=("Arial", 16))
style.configure("Treeview.Heading", font=("Arial", 16, "bold"))

borrow_table = ttk.Treeview(card2, columns=("borrower","count","total","remaining","end_time"),
                            show="headings", height=10)
borrow_table.pack(fill="both", expand=True)

borrow_table.heading("borrower", text="借用人")
borrow_table.heading("count", text="借出台數")
borrow_table.heading("total", text="總台數")
borrow_table.heading("remaining", text="剩餘台數")
borrow_table.heading("end_time", text="到期時間")

borrow_table.column("borrower", width=150, anchor="center")
borrow_table.column("count", width=80, anchor="center")
borrow_table.column("total", width=80, anchor="center")
borrow_table.column("remaining", width=80, anchor="center")
borrow_table.column("end_time", width=150, anchor="center")

button_frame = tk.Frame(card2, bg=CARD_COLOR)
button_frame.pack(fill="x", pady=5)

return_btn = tk.Button(button_frame, text="歸還", font=FONT, bg="#D9534F", fg="white")
return_btn.pack(side="left", padx=5)

extend_btn = tk.Button(button_frame, text="續借", font=FONT, bg="#5BC0DE", fg="white")
extend_btn.pack(side="left", padx=5)

def on_return():
    selected = borrow_table.selection()
    if selected:
        return_tablet_dialog(int(selected[0]))

return_btn.config(command=on_return)

def on_extend():
    selected = borrow_table.selection()
    if selected:
        extend_borrow(int(selected[0]))

extend_btn.config(command=on_extend)

def on_row_double_click(event):
    selected = borrow_table.selection()
    if selected:
        dialog = tk.Toplevel(root)
        dialog.title("操作選擇")

        tk.Label(dialog, text="請選擇操作", font=FONT_HEADER).pack(padx=10, pady=10)

        tk.Button(dialog, text="歸還", font=FONT, bg="#D9534F", fg="white",
                  command=lambda: [return_tablet_dialog(int(selected[0])), dialog.destroy()]).pack(padx=10, pady=5, fill="x")
        tk.Button(dialog, text="續借", font=FONT, bg="#5BC0DE", fg="white",
                  command=lambda: [extend_borrow(int(selected[0])), dialog.destroy()]).pack(padx=10, pady=5, fill="x")

borrow_table.bind("<Double-1>", on_row_double_click)

refresh_borrow_table()

# =========================
# 問題平板列表
# =========================
card3 = tk.Frame(root, bg=CARD_COLOR, padx=15, pady=10)
card3.pack(fill="both", expand=True, padx=20, pady=10)

tk.Label(card3, text="問題平板列表", font=FONT_HEADER, bg=CARD_COLOR).pack(anchor="w")

header2 = tk.Frame(card3, bg=CARD_COLOR)
header2.pack(fill="x")

tk.Label(header2, text="平板編號", font=FONT_HEADER, bg=CARD_COLOR).grid(row=0, column=0, padx=5)
tk.Label(header2, text="操作", font=FONT_HEADER, bg=CARD_COLOR).grid(row=0, column=1, padx=5)

broken_list = tk.Frame(card3, bg=CARD_COLOR)
broken_list.pack(fill="both", expand=True)

root.mainloop()
