import tkinter as tk
from tkinter import ttk, messagebox
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import os

# =====================
# UI 設定
# =====================
BG = "#F4F6F8"
CARD = "#FFFFFF"
BTN = "#4A90E2"
FONT_TITLE = ("Arial", 16, "bold")
FONT = ("Arial", 12)
MAX_TABLETS = 50

TEACHERS = [
    "本孚","幃捷","舒婷","珊瑩","郁均","李安","佳佳","孟璇","婉湄","逸銓",
    "惠如","百育","峻維","品妤","彥宏","勇宏","盈盈","斐雁","淨瑜","俊萱",
    "裕貞","慧娟","晉邦","迪文"
]

# =====================
# Google Sheets
# =====================
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

# =====================
# 借用中清單
# =====================
def refresh_borrow_list():
    for w in borrow_frame.winfo_children():
        w.destroy()

    rows = sheet.get_all_values()[1:]
    r = 0

    for idx, row in enumerate(rows, start=2):
        if len(row) < 6 or row[4] != "":
            continue

        info = f"{row[0]}｜{row[1]} 台｜到 {row[3]}"
        tk.Label(borrow_frame, text=info, bg=CARD).grid(row=r, column=0, sticky="w", pady=4)

        tk.Button(
            borrow_frame, text="續借",
            bg="#5CB85C", fg="white", width=6,
            command=lambda i=idx: renew(i)
        ).grid(row=r, column=1, padx=3)

        tk.Button(
            borrow_frame, text="歸還",
            bg="#D9534F", fg="white", width=6,
            command=lambda i=idx: return_with_sign(i)
        ).grid(row=r, column=2, padx=3)

        r += 1

# =====================
# 新借用（1~50 防呆）
# =====================
def submit_data():
    teacher = combo_teacher.get()
    count_text = entry_count.get().strip()

    if teacher == "" or count_text == "":
        messagebox.showwarning("錯誤", "請選擇借用人並輸入台數")
        return

    try:
        count = int(count_text)
        if not (1 <= count <= MAX_TABLETS):
            raise ValueError
    except:
        messagebox.showerror("錯誤", "台數必須是 1～50 的整數")
        return

    start = datetime.now()
    end = start + timedelta(minutes=45)

    sheet.append_row([
        teacher,
        count,
        start.strftime("%Y-%m-%d %H:%M:%S"),
        end.strftime("%Y-%m-%d %H:%M:%S"),
        "",
        ""
    ])

    entry_count.delete(0, tk.END)
    refresh_borrow_list()
    messagebox.showinfo("成功", "借用完成（45 分鐘）")

# =====================
# 續借（複製成新一行）
# =====================
def renew(row):
    teacher = sheet.cell(row, 1).value
    count = sheet.cell(row, 2).value

    start = datetime.now()
    end = start + timedelta(minutes=45)

    sheet.append_row([
        teacher,
        count,
        start.strftime("%Y-%m-%d %H:%M:%S"),
        end.strftime("%Y-%m-%d %H:%M:%S"),
        "",
        ""
    ])

    refresh_borrow_list()
    messagebox.showinfo("續借完成", f"{teacher} 已續借 45 分鐘")

# =====================
# 歸還 + 簽名
# =====================
def return_with_sign(row):
    win = tk.Toplevel(root)
    win.title("歸還簽名")
    win.geometry("300x180")
    win.configure(bg=BG)

    tk.Label(win, text="請輸入簽名", bg=BG, font=FONT).pack(pady=10)
    entry = tk.Entry(win, font=FONT)
    entry.pack()

    def confirm():
        if entry.get().strip() == "":
            messagebox.showwarning("錯誤", "必須簽名")
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.update_cell(row, 5, now)
        sheet.update_cell(row, 6, entry.get())
        win.destroy()
        refresh_borrow_list()

    tk.Button(
        win, text="確認歸還",
        bg=BTN, fg="white", font=FONT,
        command=confirm
    ).pack(pady=15)

# =====================
# UI
# =====================
root = tk.Tk()
root.title("平板借用系統")
root.geometry("460x600")
root.configure(bg=BG)

tk.Label(root, text="平板借用系統", font=FONT_TITLE, bg=BG).pack(pady=15)

card1 = tk.Frame(root, bg=CARD, padx=20, pady=15)
card1.pack(fill="x", padx=20)

tk.Label(card1, text="借用人", bg=CARD).pack(anchor="w")
combo_teacher = ttk.Combobox(card1, values=TEACHERS, state="readonly")
combo_teacher.pack(fill="x", pady=5)

tk.Label(card1, text="借用平板台數（1～50）", bg=CARD).pack(anchor="w")
entry_count = tk.Entry(card1)
entry_count.pack(fill="x", pady=5)

tk.Button(
    card1, text="送出借用",
    bg=BTN, fg="white",
    command=submit_data
).pack(pady=10)

card2 = tk.Frame(root, bg=CARD, padx=15, pady=10)
card2.pack(fill="both", expand=True, padx=20, pady=15)

tk.Label(card2, text="借用中紀錄", bg=CARD, font=("Arial", 13, "bold")).pack(anchor="w")
borrow_frame = tk.Frame(card2, bg=CARD)
borrow_frame.pack(fill="both", expand=True)

refresh_borrow_list()
root.mainloop()
