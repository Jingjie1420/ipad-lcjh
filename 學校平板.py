# 匯入 tkinter，用來建立視窗介面
import tkinter as tk

# 從 tkinter 匯入 ttk（進階元件）與 messagebox（訊息視窗）
from tkinter import ttk, messagebox

# 匯入 gspread，用來操作 Google 試算表
import gspread

# 匯入 Google API 的 OAuth2 服務帳戶認證模組
from oauth2client.service_account import ServiceAccountCredentials

# 匯入 datetime 與 timedelta，用來處理時間與加 45 分鐘
from datetime import datetime, timedelta

# 匯入 os，用來處理檔案路徑
import os


# =====================
# UI 外觀設定
# =====================

# 視窗背景顏色
BG = "#F4F6F8"

# 卡片背景顏色
CARD = "#FFFFFF"

# 主要按鈕顏色
BTN = "#4A90E2"

# 標題字型
FONT_TITLE = ("Arial", 16, "bold")

# 一般文字字型
FONT = ("Arial", 12)

# 每一筆借用最大台數限制
MAX_TABLETS = 50


# =====================
# 借用人名單（下拉式選單）
# =====================

TEACHERS = [
    "本孚","幃捷","舒婷","珊瑩","郁均","李安","佳佳","孟璇","婉湄","逸銓",
    "惠如","百育","峻維","品妤","彥宏","勇宏","盈盈","斐雁","淨瑜","俊萱",
    "裕貞","慧娟","晉邦","迪文"
]


# =====================
# 連線 Google 試算表
# =====================

def connect_google_sheet():
    # 設定 Google API 授權範圍
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    # 取得目前程式所在資料夾路徑
    base = os.path.dirname(os.path.abspath(__file__))

    # 建立憑證（使用 service_account.json）
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        os.path.join(base, "service_account.json"),
        scope
    )

    # 回傳 ipadinnout 試算表的第一個工作表
    return gspread.authorize(creds).open("ipadinnout").sheet1


# 建立全域的 sheet 物件
sheet = connect_google_sheet()


# =====================
# 重新整理「借用中清單」
# =====================

def refresh_borrow_list():
    # 清空畫面上原本的借用紀錄
    for w in borrow_frame.winfo_children():
        w.destroy()

    # 取得試算表所有資料（不看欄位名稱）
    rows = sheet.get_all_values()[1:]  # 跳過第 1 列標題

    # 顯示用的列數計數器
    r = 0

    # 逐筆檢查資料
    for idx, row in enumerate(rows, start=2):
        # 如果欄位不足 或 已經有歸還時間，就跳過
        if len(row) < 6 or row[4] != "":
            continue

        # 組合顯示文字
        info = f"{row[0]}｜{row[1]} 台｜到 {row[3]}"

        # 顯示借用資訊
        tk.Label(
            borrow_frame,
            text=info,
            bg=CARD
        ).grid(row=r, column=0, sticky="w", pady=4)

        # 續借按鈕
        tk.Button(
            borrow_frame,
            text="續借",
            bg="#5CB85C",
            fg="white",
            width=6,
            command=lambda i=idx: renew(i)
        ).grid(row=r, column=1, padx=3)

        # 歸還按鈕
        tk.Button(
            borrow_frame,
            text="歸還",
            bg="#D9534F",
            fg="white",
            width=6,
            command=lambda i=idx: return_with_sign(i)
        ).grid(row=r, column=2, padx=3)

        # 顯示下一列
        r += 1


# =====================
# 新借用（含 1~50 防呆）
# =====================

def submit_data():
    # 取得下拉選單選擇的借用人
    teacher = combo_teacher.get()

    # 取得輸入的台數文字
    count_text = entry_count.get().strip()

    # 檢查是否有空白
    if teacher == "" or count_text == "":
        messagebox.showwarning("錯誤", "請選擇借用人並輸入台數")
        return

    # 嘗試將台數轉成整數並檢查範圍
    try:
        count = int(count_text)
        if not (1 <= count <= MAX_TABLETS):
            raise ValueError
    except:
        messagebox.showerror("錯誤", "台數必須是 1～50 的整數")
        return

    # 取得目前時間
    start = datetime.now()

    # 計算 45 分鐘後的時間
    end = start + timedelta(minutes=45)

    # 新增一筆借用紀錄到試算表
    sheet.append_row([
        teacher,
        count,
        start.strftime("%Y-%m-%d %H:%M:%S"),
        end.strftime("%Y-%m-%d %H:%M:%S"),
        "",
        ""
    ])

    # 清空輸入框
    entry_count.delete(0, tk.END)

    # 更新借用中清單
    refresh_borrow_list()

    # 顯示成功訊息
    messagebox.showinfo("成功", "借用完成（45 分鐘）")


# =====================
# 續借（複製成新一行）
# =====================

def renew(row):
    # 從原本那一行讀取借用人
    teacher = sheet.cell(row, 1).value

    # 從原本那一行讀取台數
    count = sheet.cell(row, 2).value

    # 重新取得現在時間
    start = datetime.now()

    # 計算新的 45 分鐘後時間
    end = start + timedelta(minutes=45)

    # 新增一筆全新的續借紀錄
    sheet.append_row([
        teacher,
        count,
        start.strftime("%Y-%m-%d %H:%M:%S"),
        end.strftime("%Y-%m-%d %H:%M:%S"),
        "",
        ""
    ])

    # 更新畫面
    refresh_borrow_list()

    # 顯示續借完成訊息
    messagebox.showinfo("續借完成", f"{teacher} 已續借 45 分鐘")


# =====================
# 歸還（必須簽名）
# =====================

def return_with_sign(row):
    # 建立簽名視窗
    win = tk.Toplevel(root)
    win.title("歸還簽名")
    win.geometry("300x180")
    win.configure(bg=BG)

    # 簽名提示文字
    tk.Label(
        win,
        text="請輸入簽名",
        bg=BG,
        font=FONT
    ).pack(pady=10)

    # 簽名輸入框
    entry = tk.Entry(win, font=FONT)
    entry.pack()

    # 確認歸還函式
    def confirm():
        # 如果沒有輸入簽名
        if entry.get().strip() == "":
            messagebox.showwarning("錯誤", "必須簽名")
            return

        # 取得歸還時間
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 寫入歸還時間
        sheet.update_cell(row, 5, now)

        # 寫入簽名
        sheet.update_cell(row, 6, entry.get())

        # 關閉簽名視窗
        win.destroy()

        # 更新借用中清單
        refresh_borrow_list()

    # 確認歸還按鈕
    tk.Button(
        win,
        text="確認歸還",
        bg=BTN,
        fg="white",
        font=FONT,
        command=confirm
    ).pack(pady=15)


# =====================
# 主視窗 UI
# =====================

# 建立主視窗
root = tk.Tk()

# 設定視窗標題
root.title("平板借用系統")

# 設定視窗大小
root.geometry("460x600")

# 設定背景顏色
root.configure(bg=BG)

# 標題文字
tk.Label(
    root,
    text="平板借用系統",
    font=FONT_TITLE,
    bg=BG
).pack(pady=15)


# 借用輸入區卡片
card1 = tk.Frame(root, bg=CARD, padx=20, pady=15)
card1.pack(fill="x", padx=20)

# 借用人標籤
tk.Label(card1, text="借用人", bg=CARD).pack(anchor="w")

# 借用人下拉式選單
combo_teacher = ttk.Combobox(
    card1,
    values=TEACHERS,
    state="readonly"
)
combo_teacher.pack(fill="x", pady=5)

# 台數標籤
tk.Label(
    card1,
    text="借用平板台數（1～50）",
    bg=CARD
).pack(anchor="w")

# 台數輸入框
entry_count = tk.Entry(card1)
entry_count.pack(fill="x", pady=5)

# 送出借用按鈕
tk.Button(
    card1,
    text="送出借用",
    bg=BTN,
    fg="white",
    command=submit_data
).pack(pady=10)


# 借用中清單卡片
card2 = tk.Frame(root, bg=CARD, padx=15, pady=10)
card2.pack(fill="both", expand=True, padx=20, pady=15)

# 借用中標題
tk.Label(
    card2,
    text="借用中紀錄",
    bg=CARD,
    font=("Arial", 13, "bold")
).pack(anchor="w")

# 借用紀錄顯示區
borrow_frame = tk.Frame(card2, bg=CARD)
borrow_frame.pack(fill="both", expand=True)

# 初次載入借用中清單
refresh_borrow_list()

# 啟動視窗事件迴圈
root.mainloop()
