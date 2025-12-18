import tkinter as tk  # 匯入 tkinter，建立 GUI 視窗介面
from tkinter import messagebox  # 匯入訊息框功能，用來顯示提醒、錯誤或成功訊息
from tkinter import ttk  # 匯入 ttk 模組，用於進階元件（例如 Combobox）
import gspread  # 匯入 gspread，用於操作 Google Sheets
from oauth2client.service_account import ServiceAccountCredentials  # OAuth2 認證用
from datetime import datetime  # 匯入 datetime，用來取得當前日期時間
import os  # 匯入 os，用於處理檔案路徑

# -------------------------
#  全域設定
# -------------------------
FONT = ("Arial", 12)  # 定義全域字型，Label/Entry/Button 都可以使用
MAX_TABLETS = 50  # 最大可借平板數量限制改為 50
TEACHERS = [      # 借用人列表，可以依實際需求修改
    "本孚","幃捷","舒婷","珊瑩","郁均","李安","佳佳","孟璇","婉湄","逸銓",
    "惠如","百育","峻維","品妤","彥宏","勇宏","盈盈","斐雁","淨瑜","俊萱",
    "裕貞","慧娟","晉邦","迪文"
]

# -------------------------
#  連線 Google Sheets
# -------------------------
def connect_google_sheet():
    # 設定授權範圍
    scope = [
        "https://spreadsheets.google.com/feeds",  # 操作 Sheets API
        "https://www.googleapis.com/auth/drive"  # 存取 Google Drive
    ]

    # 取得專案根目錄路徑
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # 拼接 service_account.json 的完整路徑
    json_path = os.path.join(BASE_DIR, "service_account.json")

    # 透過 service_account.json 建立憑證
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        json_path,
        scope
    )

    # 用憑證授權 gspread
    client = gspread.authorize(creds)
    # 開啟名為 "ipadinnout" 的試算表，回傳第一個工作表
    return client.open("ipadinnout").sheet1

# -------------------------
#  檢查是否已借出
# -------------------------
def is_already_borrowed(name):
    records = sheet.get_all_records()  # 取得 Google Sheet 所有紀錄（轉成 dict list）
    for r in records:
        # 如果借用人相同，且尚未歸還
        if r["借用人"] == name and r["歸還時間"] == "":
            return True
    return False  # 沒有重複借用

# -------------------------
#  送出借用紀錄
# -------------------------
def submit_data():
    teacher = combo_teacher.get()  # 取得下拉選單選擇的借用人
    count_text = entry_count.get().strip()  # 取得輸入框平板數量，並去除空白

    # 欄位驗證
    if teacher == "" or count_text == "":
        messagebox.showwarning("錯誤", "請選擇借用人並輸入台數")
        return

    try:
        count = int(count_text)  # 嘗試轉成整數
        if not (1 <= count <= MAX_TABLETS):  # 檢查範圍，現在最大 50
            raise ValueError
    except:
        messagebox.showerror("錯誤", f"台數必須是 1～{MAX_TABLETS} 的整數")
        return

    # 檢查是否已借出
    if is_already_borrowed(teacher):
        messagebox.showerror("錯誤", f"{teacher} 尚未歸還，不能重複借用")
        return

    # 取得目前時間
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 將紀錄新增到 Google Sheet
    sheet.append_row([teacher, count, now, ""])

    # 清空輸入框
    entry_count.delete(0, tk.END)
    # 顯示成功訊息
    messagebox.showinfo("成功", "借用紀錄已送出")

# -------------------------
#  Tkinter UI
# -------------------------
root = tk.Tk()  # 建立主視窗
root.title("平板借用系統")  # 視窗標題
root.geometry("360x280")  # 視窗大小

sheet = connect_google_sheet()  # 連線 Google Sheets

# 借用人標籤
tk.Label(root, text="借用人：", font=FONT).pack(pady=5)

# 借用人下拉選單
combo_teacher = ttk.Combobox(
    root,
    values=TEACHERS,  # 選單內容
    state="readonly",  # 不允許輸入
    font=FONT
)
combo_teacher.pack(pady=5)

# 平板數量標籤
tk.Label(root, text="借用平板台數：", font=FONT).pack(pady=5)

# 平板數量輸入框
entry_count = tk.Entry(root, font=FONT)
entry_count.pack(pady=5)

# 送出按鈕
tk.Button(
    root,
    text="送出借用",
    font=FONT,
    command=submit_data  # 按下後執行 submit_data
).pack(pady=15)

# 啟動主視窗迴圈
root.mainloop()
