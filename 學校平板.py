import os
import sys
import traceback
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta, time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# ==========================================================
# 💡 系統級優化：宣告 DPI Awareness，讓畫面在全螢幕下保持極致清晰
# ==========================================================
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# =============================================================================
# 1. 系統參數與全域樣式定義 (System Parameters & Global Aesthetics)
# =============================================================================
APP_VERSION = "v5.6.1 - 2026 Stable Release (Final)"
APP_TITLE_ZH = "蘭州國中 114學年度 第2學期平板借用系統"
APP_TITLE_EN = "LZJH Tablet Loan System (Semester 2, 2025-2026)"

# 💡 全面升級為現代化無襯線字體 (微軟正黑體)
FONT_KAI_TITLE  = ("Microsoft JhengHei", 32, "bold")
FONT_KAI_SUB    = ("Microsoft JhengHei", 16)
FONT_KAI_CARD   = ("Microsoft JhengHei", 22, "bold")
FONT_KAI_LABEL  = ("Microsoft JhengHei", 15, "bold")
FONT_KAI_NORMAL = ("Microsoft JhengHei", 16)
FONT_KAI_BUTTON = ("Microsoft JhengHei", 14, "bold")
FONT_KAI_STATUS = ("Microsoft JhengHei", 18, "bold")

ADMIN_ACCESS_KEY = "1234"
TABLET_MAX_CAPACITY = 101

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
        "monitor_title": "📊 即時借用狀態", "reserve_title": "📅 今日預約清單",
        "tree_t": "借用教師 (Teacher)", "tree_c": "班級 (Class)", "tree_q": "數量 (Qty)", 
        "tree_i": "期限 (Due)", "tree_p": "預約節次 (Period)",
        "btn_pickup": "🚩 領取\n(Pickup)", "btn_renew": "🔄 續借\n(Renew)", "btn_return": "✅ 歸還\n(Return)", "btn_refresh": "🔄 刷新雙清單\n(Refresh)",
        "fault_title": "⚠️ 設備故障報修:", "btn_fault": " 提交 (Submit) ",
        "msg_success": "成功", "msg_error": "錯誤", "msg_warn": "提醒",
    },
    "en": {
        "lbl_teacher": "Teacher:", "lbl_class": "Class:", "lbl_qty": "Qty:",
        "stock_sync": "Syncing...", "stock_prefix": " 💡 Available Stock: {} Units ",
        "btn_borrow": "⚡ Borrow\n(55 mins)", "btn_allday": "🏢 All Day \n(Until 16:00)", "btn_reserve": "📅 Reserve\n(Schedule)",
        "monitor_title": "📊 Live Loans", "reserve_title": "📅 Today's Reservations",
        "tree_t": "Teacher", "tree_c": "Class", "tree_q": "Qty", 
        "tree_i": "Due Time", "tree_p": "Period",
        "btn_pickup": "🚩 Pickup\n(Now)", "btn_renew": "🔄 Renew\n(+55 mins)", "btn_return": "✅ Return\n(Done)", "btn_refresh": "🔄 Refresh\n(List)",
        "fault_title": "⚠️ Report Fault:", "btn_fault": " Submit ",
        "msg_success": "Success", "msg_error": "Error", "msg_warn": "Notice",
    }
}
current_lang = "zh"

# =============================================================================
# 2. 資料庫連線引擎 (Database Connection Engine - PyInstaller 支援版)
# =============================================================================
def connect_to_google_sheets():
    try:
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # 尋找 PyInstaller 的神祕暫存資料夾 (_MEIPASS)
        if getattr(sys, 'frozen', False):
            current_path = sys._MEIPASS
        else:
            current_path = os.path.dirname(os.path.abspath(__file__))
            
        json_file = os.path.join(current_path, "service_account.json")
        creds = ServiceAccountCredentials.from_json_keyfile_name(json_file, scopes)
        client = gspread.authorize(creds)
        book = client.open("ipadinnout")
        return book.worksheet("借用平板"), book.worksheet("問題平板")
    except Exception as e:
        messagebox.showerror("連線失敗", f"系統無法同步雲端數據：\n{e}")
        sys.exit()

ws_borrow, ws_fault = connect_to_google_sheets()

# =============================================================================
# 3. 模態載入視窗引擎 (Loading Modal Engine) & 權限驗證
# =============================================================================
def show_loading(message="資料同步中，請稍候..."):
    """顯示一個鎖死背景的載入視窗，防止使用者連點引發 Bug"""
    load_pop = tb.Toplevel(root)
    load_pop.title("系統通知")
    
    # 置中運算
    w, h = 350, 150
    root.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (w // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (h // 2)
    load_pop.geometry(f"{w}x{h}+{x}+{y}")
    
    load_pop.transient(root)
    load_pop.resizable(False, False)
    load_pop.grab_set() # 鎖死背景
    
    tb.Label(load_pop, text="⏳", font=("Microsoft JhengHei", 36)).pack(pady=(20, 5))
    tb.Label(load_pop, text=message, font=FONT_KAI_LABEL, bootstyle="info").pack()
    
    root.update()
    return load_pop

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
            # 預約不扣庫存，只有「使用中」才扣
            if "使用" in r[6]:
                try: used_total += int(r[2])
                except ValueError: pass
    return TABLET_MAX_CAPACITY - used_total

def refresh_main_table():
    for i in tree_main.get_children(): tree_main.delete(i)
    for i in tree_res.get_children(): tree_res.delete(i)
    try:
        lang = LANG_DATA[current_lang]
        current_dt = datetime.now()
        data_list = get_latest_records()
        
        for row in data_list:
            if row[0].strip() == "" or row[4].strip() != "": continue
            status_val = row[6]
            
            if "預約" in status_val:
                time_info = status_val.split("-")[1] if "-" in status_val else "預約中"
                tree_res.insert("", "end", values=(row[0], row[1], row[2], time_info), tags=("tag_res",))
            else:
                tag = ()
                try:
                    due_dt = datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S")
                    if current_dt > due_dt: tag = ("tag_overdue",)
                except ValueError: pass
                tree_main.insert("", "end", values=(row[0], row[1], row[2], row[5]), tags=tag)
        
        rem_units = update_stock_count(data_list)
        stock_style = "primary" if rem_units > 10 else "danger"
        label_stock.config(text=lang["stock_prefix"].format(rem_units), bootstyle=stock_style)
    except Exception as e:
        print(f"刷新表格失敗: {e}")
        traceback.print_exc()

def manual_refresh():
    """帶有載入視窗的手動刷新"""
    loading_win = show_loading("從雲端同步最新狀態...")
    try:
        refresh_main_table()
    finally:
        loading_win.destroy()

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

    loading_win = show_loading("資料寫入中，請勿關閉視窗...")
    try:
        ws_borrow.append_row([t_name, c_name, qty_val, now_str, "", due_str, "使用中 (In Use)", "", qty_val], table_range="A1")
        var_teacher.set(''); var_class.set(''); ent_qty.delete(0, tk.END)
        refresh_main_table()
        messagebox.showinfo(lang["msg_success"], f"【{t_name}】登記成功！\n期限: {due_str[11:16]}")
    except Exception as e:
        messagebox.showerror(lang["msg_error"], f"雲端寫入失敗: {e}")
    finally:
        loading_win.destroy()

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
        
        loading_win = show_loading("預約登記中...")
        try:
            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status_tag = f"預約中-{var_p.get()} (Reserved)"
            ws_borrow.append_row([t_name, c_name, int(q_str), now_ts, "", "", status_tag, "", int(q_str)], table_range="A1")
            pop.destroy(); refresh_main_table(); messagebox.showinfo(lang["msg_success"], "預約已完成!")
        except Exception as e: 
            messagebox.showerror("錯誤", f"預約失敗: {str(e)}")
        finally:
            loading_win.destroy()

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
    
    loading_win = show_loading("歸還資料處理中...")
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
    finally: loading_win.destroy()

def action_renew():
    sel = tree_main.selection()
    if not sel: return messagebox.showwarning("提醒", "請選取紀錄。")
    if not check_admin_password(): return
    lang = LANG_DATA[current_lang]
    name_key = tree_main.item(sel[0])['values'][0]
    
    loading_win = show_loading("續借資料處理中...")
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
    finally: loading_win.destroy()

def action_pickup():
    sel = tree_res.selection()
    if not sel: return messagebox.showwarning("提醒", "請選取紀錄。")
    if not check_admin_password(): return
    lang = LANG_DATA[current_lang]
    name_key = tree_res.item(sel[0])['values'][0]
    
    loading_win = show_loading("領取資料處理中...")
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
    finally: loading_win.destroy()

def send_fault():
    if not check_admin_password(): return
    msg = ent_fault.get().strip()
    if msg:
        loading_win = show_loading("報修資料提交中...")
        try: 
            ws_fault.append_row([msg, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            messagebox.showinfo("成功", "故障紀錄已提交!")
            ent_fault.delete(0, tk.END)
        except Exception as e: 
            messagebox.showerror("錯誤", f"提交失敗: {e}")
        finally:
            loading_win.destroy()

# =============================================================================
# 7. UI 主介面架構 (Master GUI Architecture)
# =============================================================================
root = tb.Window(title=f"{APP_TITLE_ZH} {APP_VERSION}", themename="litera")
root.state("zoomed") # 啟動即最大化全螢幕

style = tb.Style()
style.configure("Treeview.Heading", font=FONT_KAI_BUTTON)
style.configure("Treeview", font=FONT_KAI_NORMAL, rowheight=42, padding=[10, 8, 10, 8])

cvs = tk.Canvas(root, highlightthickness=0)
cvs.configure(bg=style.colors.bg)
scb = ttk.Scrollbar(root, orient="vertical", command=cvs.yview)
cvs.configure(yscrollcommand=scb.set)
scb.pack(side="right", fill="y"); cvs.pack(side="left", fill="both", expand=True)

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
    
    style_engine = tb.Style()
    style_engine.configure("Treeview", padding=[10, 8, 10, 8], rowheight=42)
    
    cvs.configure(bg=style_engine.colors.bg)
    res_bg = "#1f5f8b" if var_theme.get() else "#E1F5FE"
    tree_res.tag_configure("tag_res", background=res_bg)
    tree_main.tag_configure("tag_overdue", foreground=style_engine.colors.danger, font=("Microsoft JhengHei", 16, "bold"))

sw_theme = tb.Checkbutton(toggle_f, text="Light", variable=var_theme, bootstyle="dark-round-toggle", command=toggle_theme)
sw_theme.pack(side="top", anchor="e")

tb.Label(header_f, text=APP_TITLE_ZH, font=FONT_KAI_TITLE).pack()
tb.Label(header_f, text=APP_TITLE_EN, font=FONT_KAI_SUB, bootstyle="secondary").pack()
lbl_clock = tb.Label(header_f, font=("Arial", 14, "bold"), bootstyle="secondary")
lbl_clock.pack(pady=5)

# --- Input Area ---
input_card = tb.Labelframe(main_f, text=" 借用登記區 ", padding=20)
input_card.pack(fill="x", padx=80, pady=10)

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
    return tb.Button(p, text=txt, bootstyle=b_style, width=22, cursor="hand2", command=cmd)

btn_borrow = create_btn(btn_row1, "⚡ 借用送出\n(55分鐘)", SUCCESS, lambda: submit_borrow_request("SHORT"))
btn_borrow.pack(side="left", padx=15, pady=15, fill="y")
btn_allday = create_btn(btn_row1, "🏢 全天借用\n(至 16:00)", INFO, lambda: submit_borrow_request("LONG"))
btn_allday.pack(side="left", padx=15, pady=15, fill="y")
btn_reserve = create_btn(btn_row1, "📅 預約登記\n(Reservation)", WARNING, open_reserve_window)
btn_reserve.pack(side="left", padx=15, pady=15, fill="y")

# --- Monitoring Section (Split View) ---
monitor_f = tb.Frame(main_f)
monitor_f.pack(fill="both", expand=True, padx=80, pady=20)

# 強制保證絕對的 50% / 50% 寬度分佈
monitor_f.columnconfigure(0, weight=1, uniform="equal_split")
monitor_f.columnconfigure(1, weight=1, uniform="equal_split")

left_pane = tb.Frame(monitor_f)
left_pane.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

right_pane = tb.Frame(monitor_f)
right_pane.grid(row=0, column=1, sticky="nsew", padx=(15, 0))

# ==========================================
# 左側：即時借用狀態區 (Live Loans)
# ==========================================
lbl_monitor = tb.Label(left_pane, text="📊 即時借用狀態", font=FONT_KAI_CARD)
lbl_monitor.pack(anchor="w", pady=10)

tree_frame = tb.Frame(left_pane)
tree_frame.pack(fill="both", expand=True)
tree_main = ttk.Treeview(tree_frame, columns=("t", "c", "q", "i"), show="headings", height=6)
tree_main.pack(side="left", fill="both", expand=True)

tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_main.yview)
tree_scroll.pack(side="right", fill="y")
tree_main.configure(yscrollcommand=tree_scroll.set)

tree_main.column("t", width=100, anchor="center")
tree_main.column("c", width=80, anchor="center")
tree_main.column("q", width=80, anchor="center")
tree_main.column("i", width=150, anchor="w", stretch=True) 
tree_main.tag_configure("tag_overdue", foreground=tb.Style().colors.danger, font=("Microsoft JhengHei", 16, "bold"))

ctrl_left = tb.Frame(left_pane)
ctrl_left.pack(fill="x", pady=10)
btn_renew  = create_btn(ctrl_left, "🔄 續借 (Renew)", SECONDARY, action_renew); btn_renew.pack(side="left", padx=(0, 10), fill="y")
btn_return = create_btn(ctrl_left, "✅ 歸還 (Return)", PRIMARY, action_return); btn_return.pack(side="left", padx=10, fill="y")

# ==========================================
# 右側：今日預約清單區 (Reservations)
# ==========================================
lbl_reserve = tb.Label(right_pane, text="📅 今日預約清單", font=FONT_KAI_CARD)
lbl_reserve.pack(anchor="w", pady=10)

res_frame = tb.Frame(right_pane)
res_frame.pack(fill="both", expand=True)
tree_res = ttk.Treeview(res_frame, columns=("t", "c", "q", "p"), show="headings", height=6)
tree_res.pack(side="left", fill="both", expand=True)

res_scroll = ttk.Scrollbar(res_frame, orient="vertical", command=tree_res.yview)
res_scroll.pack(side="right", fill="y")
tree_res.configure(yscrollcommand=res_scroll.set)

tree_res.column("t", width=100, anchor="center")
tree_res.column("c", width=80, anchor="center")
tree_res.column("q", width=80, anchor="center")
tree_res.column("p", width=150, anchor="w", stretch=True) 
tree_res.tag_configure("tag_res", background="#E1F5FE")

ctrl_right = tb.Frame(right_pane)
ctrl_right.pack(fill="x", pady=10)
btn_pickup = create_btn(ctrl_right, "🚩 領取 (Pickup)", WARNING, action_pickup); btn_pickup.pack(side="left", padx=(0, 10), fill="y")
btn_refresh = tb.Button(ctrl_right, text="🔄 刷新雙清單", bootstyle="outline-primary", command=manual_refresh)
btn_refresh.pack(side="right", fill="y")

# --- Footer Fault Report ---
fault_card = tb.Frame(main_f)
fault_card.pack(fill="x", side="bottom", pady=20, padx=80)
lbl_fault = tb.Label(fault_card, text="⚠️ 設備故障報修:", font=FONT_KAI_LABEL, bootstyle="danger")
lbl_fault.pack(side="left", padx=(0, 20))
ent_fault = tb.Entry(fault_card, font=FONT_KAI_NORMAL, width=50)
ent_fault.pack(side="left", padx=10)
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
    btn_pickup.config(text=lang["btn_pickup"])
    btn_renew.config(text=lang["btn_renew"])
    btn_return.config(text=lang["btn_return"])
    btn_refresh.config(text=lang["btn_refresh"])
    btn_fault.config(text=lang["btn_fault"])
    
    lbl_monitor.config(text=lang["monitor_title"])
    lbl_reserve.config(text=lang["reserve_title"])
    lbl_fault.config(text=lang["fault_title"])
    
    tree_main.heading("t", text=lang["tree_t"])
    tree_main.heading("c", text=lang["tree_c"])
    tree_main.heading("q", text=lang["tree_q"])
    tree_main.heading("i", text=lang["tree_i"])
    
    tree_res.heading("t", text=lang["tree_t"])
    tree_res.heading("c", text=lang["tree_c"])
    tree_res.heading("q", text=lang["tree_q"])
    tree_res.heading("p", text=lang["tree_p"])

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

# 初始化
toggle_theme() # 套用預設主題與修正 Treeview 參數
update_ui_text()
refresh_main_table()

update_clock()
auto_refresh_data()

root.mainloop()