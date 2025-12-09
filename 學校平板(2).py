import tkinter as tk
from tkinter import messagebox
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------
#  Google Sheets 連線設定
# -------------------------
def connect_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "service_account.json",
        scope
    )

    client = gspread.authorize(creds)

    # 試算表名稱
    sheet = client.open("ipadinnout").sheet1
    return sheet


# -------------------------
#   寫入試算表
# -------------------------
def submit_data():
    teacher = selected_teacher.get()
    count = entry_count.get().strip()

    if teacher == "請選擇借用人":
        messagebox.showwarning("錯誤", "請選擇借用人！")
        return

    if count == "":
        messagebox.showwarning("錯誤", "請輸入借用台數！")
        return

    try:
        count = int(count)
    except:
        messagebox.showerror("格式錯誤", "台數必須是數字！")
        return

    sheet.append_row([teacher, count])

    entry_count.delete(0, tk.END)
    selected_teacher.set("請選擇借用人")

    messagebox.showinfo("成功", "資料已成功提交！")


# -------------------------
#   Tkinter UI 建立介面
# -------------------------
root = tk.Tk()
root.title("平板借用系統")
root.geometry("350x300")

sheet = connect_google_sheet()

# 下拉選單人名清單
teachers = [
    "本孚","幃捷","舒婷","珊瑩","郁均","李安","佳佳","孟璇","婉湄","逸銓",
    "惠如","百育","峻維","品妤","彥宏","勇宏","盈盈","斐雁","淨瑜","俊萱",
    "裕貞","慧娟","晉邦","迪文","睿婷","庚霖"
]

label1 = tk.Label(root, text="借用人姓名：", font=("微軟正黑體", 12))
label1.pack(pady=5)

# 下拉式選單
selected_teacher = tk.StringVar()
selected_teacher.set("請選擇借用人")

teacher_menu = tk.OptionMenu(root, selected_teacher, *teachers)
teacher_menu.config(font=("微軟正黑體", 12))
teacher_menu.pack(pady=5)

label2 = tk.Label(root, text="借用平板台數：", font=("微軟正黑體", 12))
label2.pack(pady=5)

entry_count = tk.Entry(root, font=("微軟正黑體", 12))
entry_count.pack(pady=5)

btn_submit = tk.Button(root, text="送出借用紀錄", font=("微軟正黑體", 12),
                       command=submit_data)
btn_submit.pack(pady=15)

root.mainloop()
