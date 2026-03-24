import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta, time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import traceback
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# =============================================================================
# 1. 系統參數與全域樣式定義 (System Parameters & Global Aesthetics)
# =============================================================================
APP_VERSION = "v5.6.1 - 2026 Stable Release (Dark Mode Ready)"
APP_TITLE_ZH = "蘭州國中 114學年度 第2學期平板借用系統"
APP_TITLE_EN = "LZJH Tablet Loan System (Semester 2, 2025-2026)"

# 字體規格設定
FONT_KAI_TITLE  = ("Microsoft JhengHei", 32, "bold")
FONT_KAI_SUB    = ("Microsoft JhengHei", 16)
FONT_KAI_CARD   = ("Microsoft JhengHei", 22, "bold")
FONT_KAI_LABEL  = ("Microsoft JhengHei", 15, "bold")
FONT_KAI_NORMAL = ("Microsoft JhengHei", 16)
FONT_KAI_BUTTON = ("Microsoft JhengHei", 14, "bold")
FONT_KAI_STATUS = ("Microsoft JhengHei", 18, "bold")

ADMIN_ACCESS_KEY = "1234"
TABLET_MAX_CAPACITY = 101

# 蘭州國中課表定義
SCHOOL_PERIODS = {
    "第1節 (P1)": "08:15", "第2節 (P2)": "09:10", "第3節 (P3)": "10:10",
    "第4節 (P4)": "11:05", "午休 (Lunch)": "11:50", "第5節 (P5)": "13:15",
    "第6節 (P6)": "14:10", "第7節 (P7)": "15:15", "第8節 (P8)": "16:10"
}

TEACHER_LIST = ["本孚","幃捷","舒婷","珊瑩","郁均","李安","佳佳","孟璇","婉湄","逸銓",
                "惠如","百育","峻維","品妤","彥宏","勇宏","盈盈","斐雁","淨瑜","俊萱",
                "裕貞","慧娟","晉邦","迪文"]

CLASS_LIST = ["701","702","703","704","705","801","802","803","804","901","902","903"]

# --- 雙語化數據字典 ---
LANG_DATA = {
    "zh": {
        "lbl_teacher": "教師 (Teacher):", "lbl_class": "班級 (Class):", "lbl_qty": "數量 (Qty):",
        "stock_sync": "系統同步中...", "stock_prefix": " 💡 剩餘平板庫存: {} 台 ",
        "btn_borrow": "⚡ 借用送出\n(55分鐘)", "btn_allday": "🏢 全天借用 \n(至 16:00)", "btn_reserve": "📅 預約登記\n(Reservation)",
        "monitor_title": "📊 即時借用狀態清單",
        "tree_t": "借用教師 (Teacher)", "tree_c": "班級 (Class)", "tree_q": "數量 (Qty)", "tree_s": "狀態 (Status)", "tree_i": "期限/節次 (Info)",
        "btn_pickup": "🚩 領取\n(Pickup)", "btn_renew": "🔄 續借\n(Renew)", "btn_return": "✅ 歸還\n(Return)", "btn_refresh": "🔄 刷新清單\n(Refresh List)",
        "fault_title": "⚠️ 設備故障報修:", "btn_fault": " 提交 (Submit) ",
        "msg_success": "成功", "msg_error": "錯誤", "msg_warn": "提醒",
        "msg_confirm_return": "確定要歸還教師【{}】的平板嗎？"
    },
    "en": {
        "lbl_teacher": "Teacher:", "lbl_class": "Class:", "lbl_qty": "Qty:",
        "stock_sync": "Syncing...", "stock_prefix": " 💡 Available Stock: {} Units ",
        "btn_borrow": "⚡ Borrow\n(55 mins)", "btn_allday": "🏢 All Day \n(Until 16:00)", "btn_reserve": "📅 Reserve\n(Schedule)",
        "monitor_title": "📊 Live Loan Status List",
        "tree_t": "Teacher", "tree_c": "Class", "tree_q": "Qty", "tree_s": "Status", "tree_i": "Info/Due",
        "btn_pickup": "🚩 Pickup\n(Now)", "btn_renew": "🔄 Renew\n(+55 mins)", "btn_return": "✅ Return\n(Done)", "btn_refresh": "🔄 Refresh\n(List)",
        "fault_title": "⚠️ Report Fault:", "btn_fault": " Submit ",
        "msg_success": "Success", "msg_error": "Error", "msg_warn": "Notice",
        "msg_confirm_return": "Return tablets for Teacher 【{}】?"
    }
}
current_lang = "zh"

# =============================================================================
# 2. 資料庫連線引擎 (Database Connection Engine)
# =============================================================================
def connect_to_google_sheets():
    try:
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # ==========================================================
        # 💡 終極打包魔法：尋找 PyInstaller 的神祕暫存資料夾 (_MEIPASS)
        # ==========================================================
        if getattr(sys, 'frozen', False):
            # 當被打包成單一 exe 時，讀取 PyInstaller 解壓縮資源的暫存目錄
            current_path = sys._MEIPASS
        else:
            # 開發模式下，讀取 py 檔所在的目錄
            current_path = os.path.dirname(os.path.abspath(__file__))
            
        json_file = os.path.join(current_path, "service_account.json")
        # ==========================================================

        creds = ServiceAccountCredentials.from_json_keyfile_name(json_file, scopes)
        client = gspread.authorize(creds)
        book = client.open("ipadinnout")
        return book.worksheet("借用平板"), book.worksheet("問題平板")
    except Exception as e:
        messagebox.showerror("連線失敗", f"系統無法同步雲端數據：\n{e}")
        sys.exit()

ws_borrow, ws_fault = connect_to_google_sheets()

# =============================================================================
# 3. 安全驗證邏輯 (Security & Permission Logic)
# =============================================================================
def check_admin_password():
    lang = LANG_DATA[current_lang]
    user_input = simpledialog.askstring(lang["msg_warn"], "請輸入管理密碼 (Admin Password):", show='*')
    if user_input == ADMIN_ACCESS_KEY: return True
    elif user_input is None: return False
    else:
        messagebox.showwarning(lang["msg_error"], "密碼錯誤！(Incorrect Password!)")
        return False

# =============================================================================
# 4. 數據處理核心 (Data Processing Core)
# =============================================================================
def get_latest_records():
    try:
        all_rows = ws_borrow.get_all_values()[1:]
        valid_data = []
        for row in all_rows:
            while len(row) < 10: row.append("")
            valid_data.append(row)
        return valid_data
    except Exception as e:
        print(f"取得資料失敗: {e}")
        return []

def update_stock_count(records=None):
    if records is None: records = get_latest_records()
    used_total = 0
    for r in records:
        if r[0].strip() != "" and r[4].strip() == "":
            if "使用" in r[6] or "預約" in r[6]:
                try: used_total += int(r[2])
                except ValueError: pass
    return TABLET_MAX_CAPACITY - used_total

def refresh_main_table():
    for i in tree_main.get_children(): tree_main.delete(i)
    try:
        lang = LANG_DATA[current_lang]
        current_dt = datetime.now()
        data_list = get_latest_records()
        
        for row in data_list:
            if row[0].strip() == "" or row[4].strip() != "": continue
            status_val = row[6]
            if "預約" in status_val:
                time_info = status_val.split("-")[1] if "-" in status_val else "預約中"
                tag = ("tag_res",)
            else:
                time_info = row[5]
                tag = ()
                try:
                    due_dt = datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S")
                    if current_dt > due_dt: tag = ("tag_overdue",)
                except ValueError: pass
            tree_main.insert("", "end", values=(row[0], row[1], row[2], status_val, time_info), tags=tag)
        
        rem_units = update_stock_count(data_list)
        # 動態調整庫存標籤顏色
        stock_style = "primary" if rem_units > 10 else "danger"
        label_stock.config(text=lang["stock_prefix"].format(rem_units), bootstyle=stock_style)
    except Exception as e:
        print(f"刷新表格失敗: {e}")
        traceback.print_exc()

# =============================================================================
# 5. 借用與預約功能模組 (Loan & Reservation Modules)
# =============================================================================
def submit_borrow_request(mode):
    if not check_admin_password(): return
    lang = LANG_DATA[current_lang]
    t_name = ent_other_name.get().strip() if var_teacher.get() == "其他" else var_teacher.get()
    c_name = var_class.get()
    q_str  = ent_qty.get().strip()

    if not t_name or not c_name or not q_str.isdigit():
        messagebox.showwarning(lang["msg_warn"], "請輸入完整教師、班級與數量。"); return
    
    qty_val = int(q_str)
    stock_val = update_stock_count()
    if qty_val <= 0 or qty_val > stock_val:
        messagebox.showerror(lang["msg_error"], f"數量錯誤或庫存不足 (剩餘: {stock_val})"); return

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if mode == "SHORT": due_obj = datetime.now() + timedelta(minutes=55)
    else: due_obj = datetime.combine(datetime.now().date(), time(16, 0))
    
    due_str = due_obj.strftime("%Y-%m-%d %H:%M:%S")

    try:
        ws_borrow.append_row([t_name, c_name, qty_val, now_str, "", due_str, "使用中 (In Use)", "", qty_val], table_range="A1")
        var_teacher.set(''); var_class.set(''); ent_qty.delete(0, tk.END)
        refresh_main_table()
        messagebox.showinfo(lang["msg_success"], f"【{t_name}】登記成功！\n期限: {due_str[11:16]}")
    except Exception as e:
        messagebox.showerror(lang["msg_error"], f"雲端寫入失敗: {e}")

def open_reserve_window():
    lang = LANG_DATA[current_lang]
    t_name = ent_other_name.get().strip() if var_teacher.get() == "其他" else var_teacher.get()
    c_name = var_class.get()
    q_str  = ent_qty.get().strip()
    if not t_name or not q_str.isdigit(): return messagebox.showwarning(lang["msg_warn"], "請先輸入教師與數量。")

    pop = tb.Toplevel(root); pop.title("預約節次"); pop.geometry("420x380"); pop.grab_set()
    tb.Label(pop, text="🗓️ 選擇預約時段\nSelect Period", font=FONT_KAI_CARD, bootstyle="primary").pack(pady=25)
    var_p = tk.StringVar(value="第1節 (P1)")
    tb.Combobox(pop, values=list(SCHOOL_PERIODS.keys()), font=FONT_KAI_NORMAL, state="readonly", textvariable=var_p).pack(pady=15, ipady=8)

    def do_reserve():
        if not check_admin_password(): return
        try:
            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status_tag = f"預約中-{var_p.get()} (Reserved)"
            ws_borrow.append_row([t_name, c_name, int(q_str), now_ts, "", "", status_tag, "", int(q_str)], table_range="A1")
            pop.destroy(); refresh_main_table(); messagebox.showinfo(lang["msg_success"], "預約已完成!")
        except Exception as e: 
            messagebox.showerror("錯誤", f"預約失敗: {str(e)}")

    tb.Button(pop, text=" 確定預約 (Confirm) ", bootstyle=PRIMARY, width=20, command=do_reserve).pack(pady=30)

# =============================================================================
# 6. 續借、歸還與領取功能 (Renew, Return & Pickup Actions)
# =============================================================================
def action_return():
    sel = tree_main.selection()
    if not sel: return messagebox.showwarning("提醒", "請選取紀錄。")
    if not check_admin_password(): return
    lang = LANG_DATA[current_lang]
    name_key = tree_main.item(sel[0])['values'][0]
    try:
        all_data = ws_borrow.get_all_values()
        for idx, row in enumerate(all_data):
            if idx == 0: continue
            if row[0] == name_key and row[4] == "":
                ws_borrow.update(range_name=f"E{idx+1}", values=[[datetime.now().strftime("%Y-%m-%d %H:%M:%S")]])
                messagebox.showinfo(lang["msg_success"], f"【{name_key}】平板已歸還!")
                break
        refresh_main_table()
    except Exception as e: messagebox.showerror("錯誤", f"歸還操作失敗: {str(e)}")

def action_renew():
    sel = tree_main.selection()
    if not sel: return messagebox.showwarning("提醒", "請選取紀錄。")
    if not check_admin_password(): return
    lang = LANG_DATA[current_lang]
    name_key = tree_main.item(sel[0])['values'][0]
    try:
        all_data = ws_borrow.get_all_values()
        for idx, row in enumerate(all_data):
            if idx == 0: continue
            if row[0] == name_key and row[4] == "" and "使用" in row[6]:
                try: old_due = datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S")
                except ValueError: old_due = datetime.now()
                new_due = (old_due + timedelta(minutes=55)).strftime("%Y-%m-%d %H:%M:%S")
                ws_borrow.update(range_name=f"F{idx+1}", values=[[new_due]])
                messagebox.showinfo(lang["msg_success"], f"續借成功至: {new_due[11:16]}")
                break
        refresh_main_table()
    except Exception as e: messagebox.showerror("錯誤", f"續借操作失敗: {str(e)}")

def action_pickup():
    sel = tree_main.selection()
    if not sel or not check_admin_password(): return
    lang = LANG_DATA[current_lang]
    name_key = tree_main.item(sel[0])['values'][0]
    try:
        all_data = ws_borrow.get_all_values()
        for idx, row in enumerate(all_data):
            if idx == 0: continue
            if row[0] == name_key and row[4] == "" and "預約" in row[6]:
                new_due = (datetime.now() + timedelta(minutes=55)).strftime("%Y-%m-%d %H:%M:%S")
                ws_borrow.update(range_name=f"F{idx+1}:G{idx+1}", values=[[new_due, "使用中 (In Use)"]])
                messagebox.showinfo(lang["msg_success"], "領取完成!")
                break
        refresh_main_table()
    except Exception as e: messagebox.showerror("錯誤", f"領取操作失敗: {str(e)}")

# =============================================================================
# 7. UI 主介面架構 (Master GUI Architecture)
# =============================================================================
root = tb.Window(title=f"{APP_TITLE_ZH} {APP_VERSION}", themename="litera")
root.state("zoomed")

# 透過 Style 配置 Treeview 字體
style = tb.Style()
style.configure("Treeview.Heading", font=FONT_KAI_BUTTON)
style.configure("Treeview", font=FONT_KAI_NORMAL, rowheight=40)

# 最底層滾動畫布
cvs = tk.Canvas(root, highlightthickness=0)
# 💡 將 Canvas 背景綁定為當前主題的背景色
cvs.configure(bg=style.colors.bg) 

scb = ttk.Scrollbar(root, orient="vertical", command=cvs.yview)
cvs.configure(yscrollcommand=scb.set)
scb.pack(side="right", fill="y"); cvs.pack(side="left", fill="both", expand=True)

# 💡 拔除所有手動 bg 設定，改用 tb.Frame 擁抱自動換膚
main_f = tb.Frame(cvs)
cvs.create_window((0, 0), window=main_f, anchor="nw")
cvs.bind("<Configure>", lambda e: cvs.itemconfig(1, width=e.width))
main_f.bind("<Configure>", lambda e: cvs.configure(scrollregion=cvs.bbox("all")))

def _on_mousewheel(event):
    widget_name = str(event.widget).lower()
    if "popdown" in widget_name or "listbox" in widget_name: return
    root.focus_set()
    if event.num == 4: cvs.yview_scroll(-1, "units")
    elif event.num == 5: cvs.yview_scroll(1, "units")
    else:
        scroll_units = -1 if event.delta > 0 else 1
        cvs.yview_scroll(scroll_units, "units")

root.bind_all("<MouseWheel>", _on_mousewheel)
root.bind_all("<Button-4>", _on_mousewheel)
root.bind_all("<Button-5>", _on_mousewheel)

# --- Header Section ---
header_f = tb.Frame(main_f)
header_f.pack(fill="x", pady=20)

# 💡 右上角控制面板 (語言與主題雙開關)
toggle_f = tb.Frame(header_f)
toggle_f.place(relx=1.0, rely=0.0, anchor="ne", x=-50, y=0)

var_lang = tk.BooleanVar(value=False)
def toggle_lang():
    global current_lang
    current_lang = "en" if var_lang.get() else "zh"
    sw_lang.config(text="EN" if var_lang.get() else "ZH")
    update_ui_text()

sw_lang = tb.Checkbutton(toggle_f, text="ZH", variable=var_lang, bootstyle="info-round-toggle", command=toggle_lang)
sw_lang.pack(side="top", anchor="e", pady=(0, 8))

var_theme = tk.BooleanVar(value=False)
def toggle_theme():
    new_theme = "darkly" if var_theme.get() else "litera"
    tb.Style().theme_use(new_theme)
    sw_theme.config(text="Dark" if var_theme.get() else "Light")
    # ==========================================================
    # 💡 終極修正：強制統一深淺模式的「行高」與「內部留白」
    # 讓深色模式也擁有淺色模式般舒適的大留白，治癒你的不開心！
    # ==========================================================
    style_engine = tb.Style()
    
    # 強制設定內部邊距 (padding): [左, 上, 右, 下]
    # 我們設定上方和下方留白各 8px，撐開高度
    style_engine.configure("Treeview", padding=[10, 8, 10, 8]) 
    
    # 強制設定行高為 42px (稍微調大一點點，配合正黑體更完美)
    style_engine.configure("Treeview", rowheight=42) 
    # ==========================================================

    cvs.configure(bg=style_engine.colors.bg)
    res_bg = "#1f5f8b" if var_theme.get() else "#E1F5FE"
    tree_main.tag_configure("tag_res", background=res_bg)
    tree_main.tag_configure("tag_overdue", foreground=style_engine.colors.danger, font=("Microsoft JhengHei", 16, "bold"))

sw_theme = tb.Checkbutton(toggle_f, text="Light", variable=var_theme, bootstyle="dark-round-toggle", command=toggle_theme)
sw_theme.pack(side="top", anchor="e")

# 標題區 (拔除 bg / fg，全靠主題)
tb.Label(header_f, text=APP_TITLE_ZH, font=FONT_KAI_TITLE).pack()
tb.Label(header_f, text=APP_TITLE_EN, font=FONT_KAI_SUB, bootstyle="secondary").pack()
lbl_clock = tb.Label(header_f, font=("Arial", 14, "bold"), bootstyle="secondary")
lbl_clock.pack(pady=5)

# --- Input Area ---
# 使用 Labelframe 讓輸入區更有層次感
input_card = tb.Labelframe(main_f, text=" 借用登記區 ", padding=20)
input_card.pack(fill="x", padx=120, pady=10)

grid_f = tb.Frame(input_card)
grid_f.pack(fill="x", pady=10)
grid_f.columnconfigure((1, 3, 5), weight=1)

lbl_teacher = tb.Label(grid_f, text="教師 (Teacher):", font=FONT_KAI_LABEL)
lbl_teacher.grid(row=0, column=0)
var_teacher = tk.StringVar()
cb_t = tb.Combobox(grid_f, values=TEACHER_LIST+["其他"], state="readonly", font=FONT_KAI_NORMAL, textvariable=var_teacher)
cb_t.grid(row=0, column=1, sticky="ew", padx=10)

lbl_class = tb.Label(grid_f, text="班級 (Class):", font=FONT_KAI_LABEL)
lbl_class.grid(row=0, column=2)
var_class = tk.StringVar()
cb_c = tb.Combobox(grid_f, values=CLASS_LIST, state="readonly", font=FONT_KAI_NORMAL, textvariable=var_class)
cb_c.grid(row=0, column=3, sticky="ew", padx=10)

lbl_qty = tb.Label(grid_f, text="數量 (Qty):", font=FONT_KAI_LABEL)
lbl_qty.grid(row=0, column=4)
ent_qty = tb.Entry(grid_f, font=FONT_KAI_NORMAL)
ent_qty.grid(row=0, column=5, sticky="ew", padx=10)

ent_other_name = tb.Entry(grid_f, font=FONT_KAI_NORMAL)
cb_t.bind("<<ComboboxSelected>>", lambda e: ent_other_name.grid(row=1, column=1, sticky="ew", padx=10, pady=(5,0)) if var_teacher.get() == "其他" else ent_other_name.grid_remove())

label_stock = tb.Label(input_card, text="系統同步中...", font=FONT_KAI_STATUS, bootstyle="info")
label_stock.pack(pady=20)

btn_row1 = tb.Frame(input_card)
btn_row1.pack()

def create_btn(p, txt, b_style, cmd):
    # 💡 使用 ttkbootstrap 按鈕
    return tb.Button(p, text=txt, bootstyle=b_style, width=22, cursor="hand2", command=cmd)

# 💡 加入 fill="y" 確保高度一致
btn_borrow = create_btn(btn_row1, "⚡ 借用送出\n(55分鐘)", SUCCESS, lambda: submit_borrow_request("SHORT"))
btn_borrow.pack(side="left", padx=15, pady=15, fill="y")
btn_allday = create_btn(btn_row1, "🏢 全天借用\n(至 16:00)", INFO, lambda: submit_borrow_request("LONG"))
btn_allday.pack(side="left", padx=15, pady=15, fill="y")
btn_reserve = create_btn(btn_row1, "📅 預約登記\n(Reservation)", WARNING, open_reserve_window)
btn_reserve.pack(side="left", padx=15, pady=15, fill="y")

# --- Monitoring Section ---
monitor_f = tb.Frame(main_f)
monitor_f.pack(fill="both", expand=True, padx=120, pady=20)
lbl_monitor = tb.Label(monitor_f, text="📊 即時借用狀態清單", font=FONT_KAI_CARD)
lbl_monitor.pack(anchor="w", pady=10)

# 💡 補回 Treeview 專屬捲軸
tree_frame = tb.Frame(monitor_f)
tree_frame.pack(fill="both", expand=True)

tree_main = ttk.Treeview(tree_frame, columns=("t", "c", "q", "s", "i"), show="headings", height=6)
tree_main.pack(side="left", fill="both", expand=True)

tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_main.yview)
tree_scroll.pack(side="right", fill="y")
tree_main.configure(yscrollcommand=tree_scroll.set)

tree_main.tag_configure("tag_res", background="#E1F5FE")
tree_main.tag_configure("tag_overdue", foreground=tb.Style().colors.danger, font=("Microsoft JhengHei", 16, "bold"))

ctrl_f = tb.Frame(monitor_f)
ctrl_f.pack(fill="x", pady=20)

# 💡 加入 fill="y"
btn_pickup = create_btn(ctrl_f, "🚩 領取\n(Pickup)", WARNING, action_pickup); btn_pickup.pack(side="left", padx=15, pady=15, fill="y")
btn_renew  = create_btn(ctrl_f, "🔄 續借\n(Renew)", SECONDARY, action_renew); btn_renew.pack(side="left", padx=15, pady=15, fill="y")
btn_return = create_btn(ctrl_f, "✅ 歸還\n(Return)", PRIMARY, action_return); btn_return.pack(side="left", padx=15, pady=15, fill="y")

btn_refresh = tb.Button(ctrl_f, text="🔄 刷新清單\n(Refresh)", bootstyle="outline-primary", command=refresh_main_table)
btn_refresh.pack(side="right", padx=15, pady=15, fill="y")

# --- Footer Fault Report ---
fault_card = tb.Frame(main_f)
fault_card.pack(fill="x", side="bottom", pady=20)
lbl_fault = tb.Label(fault_card, text="⚠️ 設備故障報修:", font=FONT_KAI_LABEL, bootstyle="danger")
lbl_fault.pack(side="left", padx=(120, 20))
ent_fault = tb.Entry(fault_card, font=FONT_KAI_NORMAL, width=50)
ent_fault.pack(side="left", padx=10)

def send_fault():
    if not check_admin_password(): return
    msg = ent_fault.get().strip()
    if msg:
        try: 
            ws_fault.append_row([msg, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            messagebox.showinfo("成功", "故障紀錄已提交!")
            ent_fault.delete(0, tk.END)
        except Exception as e: 
            messagebox.showerror("錯誤", f"提交失敗: {e}")
            
btn_fault = tb.Button(fault_card, text=" 提交 (Submit) ", bootstyle="danger", command=send_fault)
btn_fault.pack(side="left", padx=20)

# --- UI Text Update Function ---
def update_ui_text():
    lang = LANG_DATA[current_lang]
    lbl_teacher.config(text=lang["lbl_teacher"])
    lbl_class.config(text=lang["lbl_class"])
    lbl_qty.config(text=lang["lbl_qty"])
    btn_borrow.config(text=lang["btn_borrow"])
    btn_allday.config(text=lang["btn_allday"])
    btn_reserve.config(text=lang["btn_reserve"])
    lbl_monitor.config(text=lang["monitor_title"])
    tree_main.heading("t", text=lang["tree_t"])
    tree_main.heading("c", text=lang["tree_c"])
    tree_main.heading("q", text=lang["tree_q"])
    tree_main.heading("s", text=lang["tree_s"])
    tree_main.heading("i", text=lang["tree_i"])
    btn_pickup.config(text=lang["btn_pickup"])
    btn_renew.config(text=lang["btn_renew"])
    btn_return.config(text=lang["btn_return"])
    btn_refresh.config(text=lang["btn_refresh"])
    lbl_fault.config(text=lang["fault_title"])
    btn_fault.config(text=lang["btn_fault"])

# =============================================================================
# 8. 系統背景守護與啟動 (Background Monitor & Launch)
# =============================================================================
def update_clock():
    try: lbl_clock.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    except Exception: pass
    root.after(1000, update_clock) 

def auto_refresh_data():
    refresh_main_table()
    root.after(900000, auto_refresh_data) 

# 啟動時先更新一次文字與資料
update_ui_text()
refresh_main_table()

# 啟動 Tkinter 的定時器
update_clock()
auto_refresh_data()

root.mainloop()