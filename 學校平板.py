import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk  # 用 PIL 處理圖片

# -------------------------
#  全域設定
# -------------------------
FONT = ("Arial", 12)
MAX_TABLETS = 50
TEACHERS = [
    "本孚","幃捷","舒婷","珊瑩","郁均","李安","佳佳","孟璇","婉湄","逸銓",
    "惠如","百育","峻維","品妤","彥宏","勇宏","盈盈","斐雁","淨瑜","俊萱",
    "裕貞","慧娟","晉邦","迪文"
]

root = tk.Tk()
root.title("平板借用系統")
root.geometry("360x280")

# -------------------------
#  設置背景圖片
# -------------------------
# 載入圖片
bg_image = Image.open("84fd58bd-7092-4ceb-aa1d-e11979579c67.png")
bg_image = bg_image.resize((360, 280))  # 調整成視窗大小
bg_photo = ImageTk.PhotoImage(bg_image)

# 建立 Canvas 並放入背景
canvas = tk.Canvas(root, width=360, height=280)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=bg_photo, anchor="nw")

# -------------------------
#  將元件放到 Canvas 上
# -------------------------
tk.Label(root, text="借用人：", font=FONT, bg="#ffffff").place(x=30, y=30)
combo_teacher = ttk.Combobox(root, values=TEACHERS, state="readonly", font=FONT)
combo_teacher.place(x=150, y=30)

tk.Label(root, text="借用平板台數：", font=FONT, bg="#ffffff").place(x=30, y=80)
entry_count = tk.Entry(root, font=FONT)
entry_count.place(x=150, y=80)

tk.Button(root, text="送出借用", font=FONT).place(x=130, y=150)

root.mainloop()
