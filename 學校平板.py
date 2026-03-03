import re
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# =========================
# 基本設定
# =========================
APP_TITLE = (
    "蘭州國中114學年度 第1學期 平板借用系統\n"
    "Lanzhou Junior High School 114th Academic Year Semester 1: Tablet Borrowing System"
)

ADMIN_PASSWORD = "1234"  # 管理員密碼

TOTAL_TABLETS = 101
MAX_SINGLE_BORROW = 50

FONT_TITLE = ("標楷體", 24, "bold")
FONT_HEADER = ("標楷體", 20, "bold")
FONT = ("標楷體", 18)

BG_COLOR = "#F4F6F8"
CARD_COLOR = "#FFFFE0"

TEACHERS = [
    "本孚","幃捷","舒婷","珊瑩","郁均","李安","佳佳","孟璇","婉湄","逸銓",
    "惠如","百育","峻維","品妤","彥宏","勇宏","盈盈","斐雁","淨瑜","俊萱",
    "裕貞","慧娟","晉邦","迪文"
]

CLASSES= ["701","702","703","704","705","801","802","803","804","901","902","903"]

# =========================
# 密碼檢查函式
# =========================
def check_admin():
    pwd = simpledialog.askstring("權限驗證", "請輸入管理員密碼：", show='*')
    if pwd == ADMIN_PASSWORD:
        return True
    elif pwd is None: 
        return False
    else:
        messagebox.showerror("權限不足", "密碼錯誤，無法執行此操作！")
        return False

# =========================
# Google Sheet 連線
# =========================
def connect_google_sheets():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        base = os.path.dirname(os.path.abspath(__file__))
        creds_path = os.path.join(base, "service_account.json")
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        client = gspread.authorize(creds)

        return (
            client.open("ipadinnout").worksheet("借用平板"),
            client.open("ipadinnout").worksheet("問題平板")
        )
    except Exception as e:
        messagebox.showerror("連線失敗", f"無法連接 Google Sheets，請確認網路或金鑰檔案。\n錯誤訊息: {e}")
        exit()

sheet, problem_sheet = connect_google_sheets()

# =========================
# 工具函式
# =========================
def get_all_records():
    records = sheet.get_all_values()[1:]
    for r in records:
        while len(r) < 9:
            r.append("")
    return records

def get_available_codes():
    all_codes = {f"Lcjh-{i:02}" for i in range(TOTAL_TABLETS)}
    broken = set(r[0] for r in problem_sheet.get_all_values()[1:] if r and r[0].strip() != "")
    borrowed = set()
    for r in get_all_records():
        if r[0].strip() != "" and r[4].strip() == "" and r[7].strip() != "":
            borrowed.update(r[7].split(","))
    return sorted(all_codes - borrowed - broken)

def get_remaining_tablets():
    return len(get_available_codes())

def has_active_borrow(teacher):
    return any(r[0] == teacher and r[4].strip() == "" and r[0].strip() != "" for r in get_all_records())

def assign_codes(n):
    avail = get_available_codes()
    return avail[:n] if len(avail) >= n else None

# =========================
# 主視窗與版面設定
# =========================
root = tk.Tk()
root.title("平板借用系統")
root.state("zoomed")
root.configure(bg=BG_COLOR)

canvas = tk.Canvas(root, bg=BG_COLOR)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)
content = tk.Frame(canvas, bg=BG_COLOR)
canvas.create_window((0, 0), window=content, anchor="nw")
content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# =========================
# 標題區
# =========================
def update_time():
    now = datetime.now()
    time_label.config(text=now.strftime("%Y-%m-%d %H:%M:%S"))
    # 每分鐘的第 0 秒自動刷新一次表格，更新逾期紅字狀態
    if now.second == 0:
        refresh_borrow_table()
    root.after(1000, update_time)

time_label = tk.Label(content, font=("標楷體", 18), fg="gray", bg=BG_COLOR)
time_label.pack(pady=5)
tk.Label(content, text=APP_TITLE, font=FONT_TITLE, bg=BG_COLOR).pack(pady=10)
update_time()

# =========================
# 借用區
# =========================
borrow_card = tk.Frame(content, bg=CARD_COLOR, padx=20, pady=15, relief="groove", bd=2)
borrow_card.pack(fill="x", padx=50, pady=10)

tk.Label(borrow_card, text="📝 借用登記", font=FONT_HEADER, bg=CARD_COLOR).grid(row=0, column=0, columnspan=2, pady=10)

tk.Label(borrow_card, text="借用教師：", font=FONT, bg=CARD_COLOR).grid(row=1, column=0, sticky="e", pady=5)
teacher_var = tk.StringVar()
teacher_combo = ttk.Combobox(borrow_card, values=TEACHERS+["其他"], state="readonly", font=FONT, textvariable=teacher_var, width=15)
teacher_combo.grid(row=1, column=1, sticky="w", pady=5)

tk.Label(borrow_card, text="輸入姓名(其他)：", font=FONT, bg=CARD_COLOR).grid(row=2, column=0, sticky="e", pady=5)
other_teacher = tk.Entry(borrow_card, font=FONT, state="disabled", width=17)
other_teacher.grid(row=2, column=1, sticky="w", pady=5)

def on_teacher(*args):
    if teacher_var.get() == "其他":
        other_teacher.config(state="normal")
        other_teacher.focus()
    else:
        other_teacher.config(state="disabled")
        other_teacher.delete(0, tk.END)
teacher_var.trace_add("write", on_teacher)

tk.Label(borrow_card, text="借用班級：", font=FONT, bg=CARD_COLOR).grid(row=3, column=0, sticky="e", pady=5)
class_var = tk.StringVar()
class_combo = ttk.Combobox(borrow_card, values=CLASSES, state="readonly", font=FONT, textvariable=class_var, width=15)
class_combo.grid(row=3, column=1, sticky="w", pady=5)

tk.Label(borrow_card, text="借用台數：", font=FONT, bg=CARD_COLOR).grid(row=4, column=0, sticky="e", pady=5)
count_entry = tk.Entry(borrow_card, font=FONT, width=17)
count_entry.grid(row=4, column=1, sticky="w", pady=5)

remaining_label = tk.Label(borrow_card, font=FONT, bg=CARD_COLOR, fg="blue")
remaining_label.grid(row=5, column=0, columnspan=2, pady=5)

def submit_borrow():
    # 密碼檢查
    if not check_admin(): return

    teacher = other_teacher.get().strip() if teacher_var.get() == "其他" else teacher_var.get()
    
    if not teacher:
        return messagebox.showerror("錯誤", "請選擇或輸入借用教師姓名！")
    if not class_var.get():
        return messagebox.showerror("錯誤", "請選擇借用班級！")
    if not count_entry.get().isdigit():
        return messagebox.showerror("錯誤", "借用台數必須是正確的數字！")

    count = int(count_entry.get())
    if count <= 0 or count > MAX_SINGLE_BORROW:
        return messagebox.showerror("錯誤", f"借用台數不合理 (最多 {MAX_SINGLE_BORROW} 台)！")

    submit_btn.config(state="disabled", text="雲端處理中，請稍候...")
    root.update()

    try:
        if has_active_borrow(teacher):
            messagebox.showerror("錯誤", f"教師 {teacher} 尚有未歸還的平板，請先歸還後再借！")
            return
        
        codes = assign_codes(count)
        if not codes:
            messagebox.showerror("錯誤", "目前剩餘的平板台數不足！")
            return

        now = datetime.now()
        new_row_data = [
            teacher, class_var.get(), count,
            now.strftime("%Y-%m-%d %H:%M:%S"),
            "", (now+timedelta(minutes=55)).strftime("%Y-%m-%d %H:%M:%S"), # 改為 55 分鐘
            "", ",".join(codes), count
        ]

        sheet.append_row(new_row_data, table_range="A1")
        messagebox.showinfo("成功", f"借用成功！\n已為您登記借用 {count} 台平板。")
        
        count_entry.delete(0, tk.END)
        teacher_combo.set('')
        class_combo.set('')
        refresh_borrow_table()

    except Exception as e:
         messagebox.showerror("錯誤", f"寫入資料時發生錯誤：{e}")
    finally:
         submit_btn.config(state="normal", text="確認送出借用")

submit_btn = tk.Button(borrow_card, text="確認送出借用", font=FONT, bg="#4CAF50", fg="white", command=submit_borrow)
submit_btn.grid(row=6, column=0, columnspan=2, pady=15)

# =========================
# 借用表格操作區
# =========================
table_frame = tk.Frame(content, bg=BG_COLOR)
table_frame.pack(fill="both", expand=True, padx=50, pady=10)

tk.Label(table_frame, text="📊 目前借用狀態", font=FONT_HEADER, bg=BG_COLOR).pack(anchor="w", pady=5)

borrow_table = ttk.Treeview(table_frame, columns=("t","c","n","e"), show="headings", height=8)
borrow_table.pack(fill="both", expand=True)

for k,v in zip(("t","c","n","e"),("借用教師","借用班級","借用台數","預計歸還時間")):
    borrow_table.heading(k, text=v)
    borrow_table.column(k, anchor="center")

# 設定逾期紅字標籤
borrow_table.tag_configure("overdue", foreground="red")

action_frame = tk.Frame(table_frame, bg=BG_COLOR)
action_frame.pack(fill="x", pady=10)

def return_tablet():
    selected = borrow_table.selection()
    if not selected:
        return messagebox.showwarning("警告", "請先點選上方表格中要歸還的資料！")
    
    # 密碼檢查
    if not check_admin(): return

    item = borrow_table.item(selected[0])
    teacher = item['values'][0]
    
    if not messagebox.askyesno("確認歸還", f"確定要歸還教師【{teacher}】的平板嗎？"):
        return
        
    return_btn.config(state="disabled", text="歸還中...")
    root.update()
    
    try:
        records = sheet.get_all_values()
        for i, r in enumerate(records):
            if i == 0: continue 
            if len(r) > 4 and r[0].strip() == str(teacher) and r[4].strip() == "":
                row_index = i + 1
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.update_cell(row_index, 5, now_str)
                messagebox.showinfo("成功", f"教師【{teacher}】的平板已歸還成功！")
                refresh_borrow_table()
                break
    except Exception as e:
        messagebox.showerror("錯誤", f"歸還發生錯誤：{e}")
    finally:
        return_btn.config(state="normal", text="✅ 歸還已選取的平板")

def renew_tablet():
    selected = borrow_table.selection()
    if not selected:
        return messagebox.showwarning("警告", "請先點選上方表格中要續借的資料！")
    
    # 密碼檢查
    if not check_admin(): return

    item = borrow_table.item(selected[0])
    teacher = item['values'][0]
    
    if not messagebox.askyesno("確認續借", f"確定要將教師【{teacher}】的借用時間延長 55 分鐘嗎？"):
        return
        
    renew_btn.config(state="disabled", text="續借中...")
    root.update()
    
    try:
        records = sheet.get_all_values()
        for i, r in enumerate(records):
            if i == 0: continue
            if len(r) > 5 and r[0].strip() == str(teacher) and r[4].strip() == "":
                row_index = i + 1
                try:
                    old_time = datetime.strptime(r[5], "%Y-%m-%d %H:%M:%S")
                    new_time = old_time + timedelta(minutes=55) # 改為 55 分鐘
                except:
                    new_time = datetime.now() + timedelta(minutes=55) # 改為 55 分鐘
                    
                sheet.update_cell(row_index, 6, new_time.strftime("%Y-%m-%d %H:%M:%S"))
                messagebox.showinfo("成功", f"已為教師【{teacher}】延長 55 分鐘！")
                refresh_borrow_table()
                break
    except Exception as e:
        messagebox.showerror("錯誤", f"續借發生錯誤：{e}")
    finally:
        renew_btn.config(state="normal", text="⏳ 續借 (+55分鐘)")

def refresh_borrow_table():
    borrow_table.delete(*borrow_table.get_children())
    try:
        now = datetime.now()
        for r in get_all_records():
            if r[0].strip() != "" and r[4].strip() == "": 
                due_time_str = r[5]
                is_overdue = False
                try:
                    due_dt = datetime.strptime(due_time_str, "%Y-%m-%d %H:%M:%S")
                    if now > due_dt:
                        is_overdue = True
                except:
                    pass
                
                if is_overdue:
                    borrow_table.insert("", "end", values=(r[0], r[1], r[2], r[5]), tags=("overdue",))
                else:
                    borrow_table.insert("", "end", values=(r[0], r[1], r[2], r[5]))
                    
        remaining_label.config(text=f"🟢 目前剩餘平板台數：{get_remaining_tablets()} 台")
    except Exception as e:
        messagebox.showerror("錯誤", f"更新表格失敗：{e}")

return_btn = tk.Button(action_frame, text="✅ 歸還已選取的平板", font=("標楷體", 16), bg="#2196F3", fg="white", command=return_tablet)
return_btn.pack(side="left", padx=10)

renew_btn = tk.Button(action_frame, text="⏳ 續借 (+55分鐘)", font=("標楷體", 16), bg="#FF9800", fg="white", command=renew_tablet)
renew_btn.pack(side="left", padx=10)

refresh_btn = tk.Button(action_frame, text="🔄 手動更新表格", font=("標楷體", 16), command=refresh_borrow_table)
refresh_btn.pack(side="right", padx=10)

# =========================
# 問題平板登記區
# =========================
problem_frame = tk.Frame(content, bg="#FFCDD2", padx=20, pady=15, relief="groove", bd=2)
problem_frame.pack(fill="x", padx=50, pady=20)

tk.Label(problem_frame, text="⚠️ 登記問題平板", font=FONT_HEADER, bg="#FFCDD2").pack(pady=5)
tk.Label(problem_frame, text="請輸入平板編號 (例如 5 或 Lcjh-05)：", font=("標楷體", 16), bg="#FFCDD2").pack()

problem_entry = tk.Entry(problem_frame, font=FONT, justify="center", width=15)
problem_entry.pack(pady=5)

def submit_problem():
    # 密碼檢查
    if not check_admin(): return

    raw_code = problem_entry.get().strip()
    if not raw_code:
        return messagebox.showerror("錯誤", "請輸入編號！")

    if raw_code.isdigit():
        num = int(raw_code)
        if 0 <= num <= 100:
            code = f"Lcjh-{num:02}"
        else:
            return messagebox.showerror("錯誤", "編號超出範圍 (0 到 100)")
    else:
        code = raw_code 

    if not re.fullmatch(r"Lcjh-(0\d|[1-9]\d|100)", code):
        return messagebox.showerror("錯誤", "格式錯誤！")

    problem_btn.config(state="disabled", text="登記中...")
    root.update()

    try:
        problem_sheet.append_row([code, datetime.now().strftime("%Y-%m-%d %H:%M:%S")], table_range="A1")
        messagebox.showinfo("成功", f"已成功將 {code} 登記為問題平板！")
        problem_entry.delete(0, tk.END)
        refresh_borrow_table()
    except Exception as e:
        messagebox.showerror("錯誤", f"登記失敗：{e}")
    finally:
        problem_btn.config(state="normal", text="確認登記問題平板")

problem_btn = tk.Button(problem_frame, text="確認登記問題平板", font=FONT, bg="#F44336", fg="white", command=submit_problem)
problem_btn.pack(pady=10)

# =========================
# 啟動應用程式
# =========================
try:
    refresh_borrow_table()
except Exception as e:
    messagebox.showerror("錯誤", f"讀取初始資料失敗：{e}")
    
root.mainloop()