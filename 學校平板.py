import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# ==========================================
# 1. 基本設定與常數 (UI 與路徑)
# ==========================================
APP_TITLE = (
    "蘭州國中114學年度 第2學期 平板借用系統\n"
    "Lanzhou Junior High School 114th Academic Year Semester 2: Tablet Borrowing System"
)

ADMIN_PASSWORD = "1234" 
TOTAL_TABLETS = 101
MAX_SINGLE_BORROW = 50

# 本地資料檔案路徑 (獨立分開借用、報修與日誌)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OFFLINE_DATA_FILE = os.path.join(BASE_DIR, "offline_data.json")
OFFLINE_PROB_FILE = os.path.join(BASE_DIR, "offline_problems.json")
SYSTEM_LOG_FILE = os.path.join(BASE_DIR, "system_log.txt")

# 字體與顏色設定
FONT_TITLE = ("標楷體", 24, "bold")
FONT_HEADER = ("標楷體", 20, "bold")
FONT = ("標楷體", 18)
FONT_SMALL = ("標楷體", 14)

BG_COLOR = "#F4F6F8"
CARD_COLOR = "#FFFFE0"
BTN_SUCCESS_COLOR = "#4CAF50"
BTN_INFO_COLOR = "#2196F3"
BTN_WARNING_COLOR = "#FF9800"
BTN_DANGER_COLOR = "#F44336"

# 下拉選單資料
TEACHERS = [
    "本孚","幃捷","舒婷","珊瑩","郁均","李安","佳佳","孟璇","婉湄","逸銓",
    "惠如","百育","峻維","品妤","彥宏","勇宏","盈盈","斐雁","淨瑜","俊萱",
    "裕貞","慧娟","晉邦","迪文"
]
CLASSES = ["701","702","703","704","705","801","802","803","804","901","902","903"]


# ==========================================
# 2. 本地操作日誌系統 (Offline Logging)
# ==========================================
def write_log(action, detail):
    """ 將所有的操作記錄寫入本地 txt 檔案，方便斷網時追蹤 """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{now_str}] 【{action}】 {detail}\n"
    try:
        with open(SYSTEM_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_message)
    except Exception as e:
        print(f"日誌寫入失敗: {e}")


# ==========================================
# 3. 本地資料管理庫 (100% 離線運行)
# ==========================================
def load_json(filepath):
    """ 安全地讀取本地 JSON 檔案 """
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            write_log("系統錯誤", f"讀取 {filepath} 失敗: {e}")
            return []
    return []

def save_json(filepath, data):
    """ 安全地寫入本地 JSON 檔案 """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        write_log("系統錯誤", f"寫入 {filepath} 失敗: {e}")
        messagebox.showerror("本機存檔失敗", f"無法寫入檔案：{e}")
        return False

def get_available_codes():
    """ 根據本地借用資料與報修資料，計算還剩哪些編號 """
    all_codes = {f"Lcjh-{i:02}" for i in range(1, TOTAL_TABLETS + 1)}
    
    # 計算已被借出且未歸還的
    borrow_data = load_json(OFFLINE_DATA_FILE)
    borrowed_codes = set()
    for r in borrow_data:
        if r[4] == "" and r[7]: 
            codes = r[7].split(",")
            borrowed_codes.update(codes)
            
    # 計算報修不可用的
    prob_data = load_json(OFFLINE_PROB_FILE)
    broken_codes = set()
    for p in prob_data:
        if p[0]: 
            broken_codes.add(p[0])
            
    return sorted(list(all_codes - borrowed_codes - broken_codes))


# ==========================================
# 4. 雲端同步系統 (防護罩全面啟用)
# ==========================================
def connect_google_sheets():
    """ 建立 Google Sheets 連線 (只有同步時才會呼叫) """
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_path = os.path.join(BASE_DIR, "service_account.json")
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    s_borrow = client.open("ipadinnout").worksheet("借用平板")
    s_prob = client.open("ipadinnout").worksheet("問題平板")
    return s_borrow, s_prob

def sync_to_cloud(is_auto=False):
    """ 執行同步作業，包含完整的網路異常攔截機制 """
    borrow_data = load_json(OFFLINE_DATA_FILE)
    prob_data = load_json(OFFLINE_PROB_FILE)
    
    if not borrow_data and not prob_data:
        if not is_auto:
            messagebox.showinfo("同步", "目前本機沒有需要上傳的資料。")
        return

    if not is_auto:
        status_label.config(text="⏳ 正在嘗試連線雲端並上傳資料...", fg="orange")
        root.update()

    try:
        write_log("同步開始", f"嘗試同步 {len(borrow_data)} 筆借用, {len(prob_data)} 筆報修")
        s_borrow, s_prob = connect_google_sheets()
        
        # 傳送借用資料
        if borrow_data:
            s_borrow.append_rows(borrow_data)
            if os.path.exists(OFFLINE_DATA_FILE): 
                os.remove(OFFLINE_DATA_FILE)
            
        # 傳送報修資料
        if prob_data:
            s_prob.append_rows(prob_data)
            if os.path.exists(OFFLINE_PROB_FILE): 
                os.remove(OFFLINE_PROB_FILE)
            
        msg = f"同步成功！\n上傳了 {len(borrow_data)} 筆借用紀錄\n上傳了 {len(prob_data)} 筆報修紀錄"
        write_log("同步成功", msg.replace('\n', ', '))
        
        if not is_auto:
            messagebox.showinfo("同步成功", msg)
        status_label.config(text="🟢 同步完成，目前為最新狀態", fg="green")
        refresh_borrow_table()
        
    except Exception as e:
        # 【關鍵防護】攔截所有 HTTPSConnectionPool 錯誤，不讓系統崩潰
        write_log("同步失敗", f"網路連線異常: {e}")
        status_label.config(text="🔴 離線模式 (資料安全存於本機)", fg="red")
        if not is_auto:
            messagebox.showwarning(
                "網路連線失敗", 
                "目前無法連線到 Google 伺服器 (可能是沒有網路)。\n\n"
                "請放心，您的資料已安全保存在本機，\n"
                "待網路恢復或今晚 18:00 系統會再次嘗試自動同步。"
            )


# ==========================================
# 5. UI 介面初始化與主視窗
# ==========================================
root = tk.Tk()
root.title("蘭州國中平板借用系統 (終極離線版)")
root.state("zoomed")
root.configure(bg=BG_COLOR)

# 建立可滾動的畫布與框架
canvas = tk.Canvas(root, bg=BG_COLOR, highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg=BG_COLOR)

scrollable_frame.bind(
    "<Configure>", 
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

content = scrollable_frame

# --- 頂部時間與標題 ---
def update_time():
    now = datetime.now()
    time_label.config(text=now.strftime("%Y-%m-%d %H:%M:%S"))
    
    # 每天 18:00:00 自動在背景嘗試同步
    if now.strftime("%H:%M:%S") == "18:00:00":
        sync_to_cloud(is_auto=True)
        
    root.after(1000, update_time)

time_label = tk.Label(content, font=("標楷體", 18), fg="gray", bg=BG_COLOR)
time_label.pack(pady=10)

title_label = tk.Label(content, text=APP_TITLE, font=FONT_TITLE, bg=BG_COLOR, justify="center")
title_label.pack(pady=10)


# ==========================================
# 6. 借用登記區 (完全離線運作)
# ==========================================
borrow_frame = tk.Frame(content, bg=CARD_COLOR, padx=30, pady=25, relief="groove", bd=2)
borrow_frame.pack(fill="x", padx=80, pady=15)

borrow_title = tk.Label(borrow_frame, text="📝 借用登記 (本地防護罩啟用中)", font=FONT_HEADER, bg=CARD_COLOR)
borrow_title.grid(row=0, column=0, columnspan=2, pady=15)

# 教師選擇
tk.Label(borrow_frame, text="借用教師：", font=FONT, bg=CARD_COLOR).grid(row=1, column=0, sticky="e", pady=10)
teacher_var = tk.StringVar()
teacher_combo = ttk.Combobox(borrow_frame, values=TEACHERS + ["其他"], state="readonly", font=FONT, textvariable=teacher_var)
teacher_combo.grid(row=1, column=1, sticky="w", pady=10)

# 其他教師姓名
tk.Label(borrow_frame, text="姓名 (若選其他)：", font=FONT, bg=CARD_COLOR).grid(row=2, column=0, sticky="e", pady=10)
other_teacher_entry = tk.Entry(borrow_frame, font=FONT, state="disabled")
other_teacher_entry.grid(row=2, column=1, sticky="w", pady=10)

def toggle_teacher_entry(*args):
    if teacher_var.get() == "其他":
        other_teacher_entry.config(state="normal")
    else:
        other_teacher_entry.delete(0, tk.END)
        other_teacher_entry.config(state="disabled")
teacher_var.trace("w", toggle_teacher_entry)

# 班級選擇
tk.Label(borrow_frame, text="借用班級：", font=FONT, bg=CARD_COLOR).grid(row=3, column=0, sticky="e", pady=10)
class_var = tk.StringVar()
class_combo = ttk.Combobox(borrow_frame, values=CLASSES, state="readonly", font=FONT, textvariable=class_var)
class_combo.grid(row=3, column=1, sticky="w", pady=10)

# 借用台數
tk.Label(borrow_frame, text="借用台數：", font=FONT, bg=CARD_COLOR).grid(row=4, column=0, sticky="e", pady=10)
count_entry = tk.Entry(borrow_frame, font=FONT)
count_entry.grid(row=4, column=1, sticky="w", pady=10)

# 狀態資訊
info_label = tk.Label(borrow_frame, text="系統計算中...", font=("標楷體", 16), bg=CARD_COLOR, fg="blue")
info_label.grid(row=5, column=0, columnspan=2, pady=10)

def submit_borrow():
    pwd = simpledialog.askstring("權限驗證", "請輸入管理員密碼：", show='*')
    if pwd != ADMIN_PASSWORD:
        if pwd is not None: messagebox.showerror("錯誤", "密碼不正確！")
        return
        
    t = other_teacher_entry.get().strip() if teacher_var.get() == "其他" else teacher_var.get()
    c = class_var.get()
    n_str = count_entry.get().strip()
    
    if not t or not c or not n_str.isdigit():
        return messagebox.showerror("錯誤", "請完整填寫教師、班級與正確的台數！")
    
    n = int(n_str)
    if n <= 0 or n > MAX_SINGLE_BORROW:
        return messagebox.showerror("錯誤", f"單次借用台數須在 1~{MAX_SINGLE_BORROW} 之間")

    avail_codes = get_available_codes()
    if len(avail_codes) < n:
        return messagebox.showerror("錯誤", "剩餘可用平板不足！")
        
    assigned = avail_codes[:n]
    now = datetime.now()
    due = now + timedelta(minutes=55)
    
    # 格式比照試算表
    row = [t, c, n, now.strftime("%Y-%m-%d %H:%M:%S"), "", due.strftime("%Y-%m-%d %H:%M:%S"), "", ",".join(assigned), n]
    
    data = load_json(OFFLINE_DATA_FILE)
    data.append(row)
    
    if save_json(OFFLINE_DATA_FILE, data):
        write_log("借用成功", f"教師:{t}, 班級:{c}, 台數:{n}, 分配:{','.join(assigned)}")
        messagebox.showinfo("成功", f"借用已記錄於本機！\n分配編號：{row[7]}\n將於 18:00 自動上傳。")
        
        teacher_var.set("")
        class_var.set("")
        count_entry.delete(0, tk.END)
        refresh_borrow_table()

submit_btn = tk.Button(borrow_frame, text="確認送出借用", font=FONT, bg=BTN_SUCCESS_COLOR, fg="white", command=submit_borrow, padx=30, pady=5)
submit_btn.grid(row=6, column=0, columnspan=2, pady=20)


# ==========================================
# 7. 當前借用清單表格 (完全離線運作)
# ==========================================
status_frame = tk.Frame(content, bg=BG_COLOR)
status_frame.pack(fill="both", expand=True, padx=80, pady=15)

tk.Label(status_frame, text="📊 本日本機借用清單", font=FONT_HEADER, bg=BG_COLOR).pack(anchor="w", pady=5)

tree_columns = ("teacher", "class", "count", "due_time")
tree = ttk.Treeview(status_frame, columns=tree_columns, show="headings", height=10)

tree.heading("teacher", text="教師"); tree.column("teacher", anchor="center", width=120)
tree.heading("class", text="班級"); tree.column("class", anchor="center", width=120)
tree.heading("count", text="台數"); tree.column("count", anchor="center", width=100)
tree.heading("due_time", text="應歸還時間"); tree.column("due_time", anchor="center", width=250)
tree.pack(fill="both", expand=True, pady=5)

def refresh_borrow_table():
    """ 更新表格資料與剩餘台數 (全本地計算) """
    for item in tree.get_children(): 
        tree.delete(item)
        
    data = load_json(OFFLINE_DATA_FILE)
    now = datetime.now()
    active_count = 0
    
    for r in data:
        if r[4] == "": # 尚未歸還
            active_count += int(r[2])
            due = datetime.strptime(r[5], "%Y-%m-%d %H:%M:%S")
            tag = "overdue" if now > due else ""
            tree.insert("", "end", values=(r[0], r[1], r[2], r[5]), tags=(tag,))
            
    tree.tag_configure("overdue", foreground="red")
    avail = len(get_available_codes())
    info_label.config(text=f"🟢 目前本機推算剩餘可用台數：{avail} 台")


# ==========================================
# 8. 功能按鈕區 (歸還、同步與說明)
# ==========================================
btn_group = tk.Frame(content, bg=BG_COLOR)
btn_group.pack(pady=15)

def return_tablet():
    selected = tree.selection()
    if not selected: 
        return messagebox.showwarning("提醒", "請先在下方表格選擇要歸還的紀錄。")
    
    pwd = simpledialog.askstring("驗證", "請輸入管理員密碼：", show='*')
    if pwd != ADMIN_PASSWORD: 
        return
    
    item_values = tree.item(selected[0])['values']
    data = load_json(OFFLINE_DATA_FILE)
    
    for r in data:
        if r[0] == str(item_values[0]) and r[1] == str(item_values[1]) and r[4] == "":
            r[4] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_json(OFFLINE_DATA_FILE, data)
            write_log("歸還成功", f"教師:{r[0]}, 班級:{r[1]}, 台數:{r[2]}")
            messagebox.showinfo("成功", "本機歸還登記成功！")
            refresh_borrow_table()
            return
            
    messagebox.showerror("錯誤", "找不到對應的未歸還紀錄。")

def show_system_info():
    """ 顯示系統操作說明的輔助視窗 """
    info_text = (
        "【系統操作須知】\n\n"
        "1. 斷網保護：白天借用、歸還、報修皆存於本機，不受網路影響。\n"
        "2. 自動同步：每日 18:00 系統會在背景自動連網上傳資料。\n"
        "3. 手動同步：若有需要，可隨時點擊「手動同步」按鈕。\n"
        "4. 操作日誌：所有動作皆已記錄於 system_log.txt 以供備查。"
    )
    messagebox.showinfo("系統資訊", info_text)

tk.Button(btn_group, text="✅ 選中歸還", font=FONT, bg=BTN_INFO_COLOR, fg="white", command=return_tablet, padx=15).pack(side="left", padx=15)
tk.Button(btn_group, text="☁️ 手動同步至雲端", font=FONT, bg=BTN_WARNING_COLOR, fg="white", command=lambda: sync_to_cloud(is_auto=False), padx=15).pack(side="left", padx=15)
tk.Button(btn_group, text="ℹ️ 系統說明", font=FONT, command=show_system_info, padx=15).pack(side="left", padx=15)


# ==========================================
# 9. 問題平板報修區 (完全離線運作)
# ==========================================
repair_frame = tk.Frame(content, bg="#FFEBEE", padx=30, pady=25, relief="groove", bd=2)
repair_frame.pack(fill="x", padx=80, pady=25)

tk.Label(repair_frame, text="⚠️ 問題平板登記", font=FONT_HEADER, bg="#FFEBEE", fg="#B71C1C").pack(pady=5)
repair_input_frame = tk.Frame(repair_frame, bg="#FFEBEE")
repair_input_frame.pack(pady=10)

tk.Label(repair_input_frame, text="平板編號 (例:Lcjh-05)：", font=FONT, bg="#FFEBEE").pack(side="left")
repair_entry = tk.Entry(repair_input_frame, font=FONT, width=20)
repair_entry.pack(side="left", padx=10)

def submit_repair():
    code = repair_entry.get().strip()
    if not code: 
        return messagebox.showwarning("提醒", "請輸入編號")
    
    pwd = simpledialog.askstring("驗證", "請輸入管理員密碼：", show='*')
    if pwd != ADMIN_PASSWORD: 
        return
    
    prob_data = load_json(OFFLINE_PROB_FILE)
    prob_data.append([code, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    
    if save_json(OFFLINE_PROB_FILE, prob_data):
        write_log("報修登記", f"故障編號: {code}")
        messagebox.showinfo("報修成功", f"已將 {code} 記錄於本機，將於下次同步時上傳。")
        repair_entry.delete(0, tk.END)
        refresh_borrow_table() # 刷新可用台數

tk.Button(repair_frame, text="登記報修", font=FONT, bg=BTN_DANGER_COLOR, fg="white", command=submit_repair, padx=20).pack(pady=10)


# ==========================================
# 10. 底部狀態列與啟動
# ==========================================
status_label = tk.Label(root, text="系統已就緒 (本地防護模式運行中)", bd=1, relief="sunken", anchor="w", font=("Arial", 12), bg="#E0E0E0")
status_label.pack(side="bottom", fill="x")

# 初始化時寫入啟動日誌
write_log("系統啟動", "程式已開啟，進入本地防護模式")

# 啟動時鐘與更新表格
update_time()
refresh_borrow_table()
root.mainloop()