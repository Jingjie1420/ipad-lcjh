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

    # ⚠ 請改成你的試算表名稱
    sheet = client.open("ipadinnout").sheet1
    return sheet


# -------------------------
#   寫入試算表
# -------------------------
def submit_data():
    teacher = entry_teacher.get().strip()
    count = entry_count.get().strip()

    if teacher == "" or count == "":
        messagebox.showwarning("錯誤", "請輸入完整資料！")
        return
    
    try:
        count = int(count)
    except:
        messagebox.showerror("格式錯誤", "台數必須是數字！")
        return

    sheet.append_row([teacher, count])

    entry_teacher.delete(0, tk.END)
    entry_count.delete(0, tk.END)

    messagebox.showinfo("成功", "資料已成功提交！")


# -------------------------
#   Tkinter UI 建立介面
# -------------------------
root = tk.Tk()
root.title("平板借用系統")
root.geometry("350x250")

sheet = connect_google_sheet()

label1 = tk.Label(root, text="借用人姓名：", font=("微軟正黑體", 12))
label1.pack(pady=5)

entry_teacher = tk.Entry(root, font=("微軟正黑體", 12))
entry_teacher.pack(pady=5)

label2 = tk.Label(root, text="借用平板台數：", font=("微軟正黑體", 12))
label2.pack(pady=5)

entry_count = tk.Entry(root, font=("微軟正黑體", 12))
entry_count.pack(pady=5)

btn_submit = tk.Button(root, text="送出借用紀錄", font=("微軟正黑體", 12),
                       command=submit_data)
btn_submit.pack(pady=10)

root.mainloop()
