import os
import tkinter as tk
from tkinter import messagebox

import psycopg2
from PIL import Image, ImageTk

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "shoe_store_demo",
    "user": "postgres",
    "password": "postgres",
}

# module2.py в папке «модуль 2», images — на уровень выше (корень fin_demoex)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
ICON_PATH = os.path.join(IMAGES_DIR, "Icon.ico")
LOGO_PATH = os.path.join(IMAGES_DIR, "Icon.png")
PLACEHOLDER_PATH = os.path.join(IMAGES_DIR, "picture.png")


COLOR_BG = "#FFFFFF"
COLOR_HEADER = "#7FFF00"
COLOR_ACCENT = "#00FA9A"
COLOR_HIGH_DISCOUNT = "#2E8B57"
COLOR_OUT_OF_STOCK = "#87CEFA"
COLOR_PRICE_OLD = "#FF0000"
COLOR_PRICE_NEW = "#000000"

# ---------- шрифт Times New Roman ----------
FONT = ("Times New Roman", 11)
FONT_BOLD = ("Times New Roman", 11, "bold")
FONT_TITLE = ("Times New Roman", 14, "bold")
FONT_LOGIN = ("Times New Roman", 16, "bold")

# ---------- глобальные переменные ----------
main_window = None
current_user = None
logo_image = None
product_images_cache = {}


def connect_db():
    return psycopg2.connect(**DB_CONFIG)


def clear_window():
    for widget in main_window.winfo_children():
        widget.destroy()


def setup_style():
    main_window.option_add("*Font", FONT)


def load_logo(max_size=(120, 120)):
    global logo_image
    if not os.path.exists(LOGO_PATH):
        return None
    img = Image.open(LOGO_PATH)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    logo_image = ImageTk.PhotoImage(img)
    return logo_image


def make_accent_button(parent, text, command):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=COLOR_ACCENT,
        font=FONT,
        activebackground=COLOR_ACCENT,
    )


def make_button(parent, text, command):
    return tk.Button(parent, text=text, command=command, font=FONT, bg=COLOR_BG)


def load_product_photo(photo_file, size=(120, 120)):
    name = str(photo_file or "").strip()
    if name == "":
        path = PLACEHOLDER_PATH
    else:
        path = os.path.join(IMAGES_DIR, name)
    if not os.path.isfile(path):
        path = PLACEHOLDER_PATH
    if not os.path.isfile(path):
        return None
    key = (path, size[0], size[1])
    if key in product_images_cache:
        return product_images_cache[key]
    img = Image.open(path)
    img = img.resize(size)
    tk_img = ImageTk.PhotoImage(img)
    product_images_cache[key] = tk_img
    return tk_img


def to_number(value, default=0):
    try:
        text = str(value).replace(",", ".")
        if "." in text:
            return float(text)
        return int(text)
    except Exception:
        return default


def auth_user(login, password):
    sql = """
        SELECT full_name, role_name
        FROM users
        WHERE login = %s AND password_plain = %s
        LIMIT 1
    """
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(sql, (login, password))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        return None
    return {"full_name": row[0], "role_name": row[1], "is_guest": False}


def fetch_products():
    sql = """
        SELECT
            product_name,
            category_name,
            description,
            manufacturer_name,
            supplier_name,
            price,
            unit_name,
            stock_qty,
            discount_percent,
            photo_file
        FROM products
        ORDER BY product_name
    """
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_role_note(role_name):
    if role_name == "Гость":
        return "Режим гостя: только просмотр товаров"
    if role_name == "Авторизированный клиент":
        return "Клиент: просмотр товаров"
    if role_name == "Менеджер":
        return "Менеджер: просмотр товаров"
    if role_name == "Администратор":
        return "Администратор: просмотр товаров"
    return "Просмотр товаров"


def get_card_background(discount, stock_qty):
    if stock_qty == 0:
        return COLOR_OUT_OF_STOCK
    if discount > 15:
        return COLOR_HIGH_DISCOUNT
    return COLOR_BG


def create_product_card(parent, product_row):
    (
        product_name,
        category_name,
        description,
        manufacturer_name,
        supplier_name,
        price,
        unit_name,
        stock_qty,
        discount_percent,
        photo_file,
    ) = product_row

    price_value = to_number(price, 0)
    discount_value = to_number(discount_percent, 0)
    stock_value = to_number(stock_qty, 0)

    bg_color = get_card_background(discount_value, stock_value)

    card = tk.Frame(parent, bg=bg_color, bd=1, relief=tk.SOLID)
    card.pack(fill=tk.X, padx=8, pady=6)

    photo = load_product_photo(photo_file)
    photo_label = tk.Label(card, bg=bg_color)
    photo_label.grid(row=0, column=0, rowspan=6, padx=8, pady=8, sticky="n")
    if photo is not None:
        photo_label.config(image=photo)
        photo_label.image = photo

    title_text = category_name + " | " + product_name
    title_label = tk.Label(
        card,
        text=title_text,
        bg=bg_color,
        fg="#000000",
        font=FONT_BOLD,
        anchor="w",
    )
    title_label.grid(row=0, column=1, sticky="w", padx=4, pady=2)

    info_lines = [
        "Описание товара: " + str(description),
        "Производитель: " + str(manufacturer_name),
        "Поставщик: " + str(supplier_name),
        "Единица измерения: " + str(unit_name),
        "Количество на складе: " + str(stock_value),
    ]
    row_index = 1
    for line in info_lines:
        lbl = tk.Label(card, text=line, bg=bg_color, anchor="w", justify="left", font=FONT)
        lbl.grid(row=row_index, column=1, sticky="w", padx=4)
        row_index = row_index + 1

    price_frame = tk.Frame(card, bg=bg_color)
    price_frame.grid(row=row_index, column=1, sticky="w", padx=4, pady=2)

    if discount_value > 0:
        final_price = price_value - (price_value * discount_value / 100)
        old_label = tk.Label(
            price_frame,
            text="Цена: %.2f" % price_value,
            bg=bg_color,
            fg=COLOR_PRICE_OLD,
            font=(FONT[0], 10, "overstrike"),
        )
        old_label.pack(side=tk.LEFT)
        new_label = tk.Label(
            price_frame,
            text="  %.2f" % final_price,
            bg=bg_color,
            fg=COLOR_PRICE_NEW,
            font=FONT_BOLD,
        )
        new_label.pack(side=tk.LEFT)
    else:
        normal_label = tk.Label(
            price_frame,
            text="Цена: %.2f" % price_value,
            bg=bg_color,
            fg=COLOR_PRICE_NEW,
            font=FONT,
        )
        normal_label.pack(side=tk.LEFT)

    discount_label = tk.Label(
        card,
        text="Действующая скидка\n" + str(discount_value) + "%",
        bg=bg_color,
        font=FONT_BOLD,
        justify="center",
    )
    discount_label.grid(row=0, column=2, rowspan=6, padx=12, pady=8)


def show_products_window():
    global current_user
    clear_window()

    main_window.title("Список товаров - ООО «Обувь»")

    top_bar = tk.Frame(main_window, bg=COLOR_HEADER, height=70)
    top_bar.pack(fill=tk.X)

    logo = load_logo((60, 60))
    if logo is not None:
        logo_label = tk.Label(top_bar, image=logo, bg=COLOR_HEADER)
        logo_label.image = logo
        logo_label.pack(side=tk.LEFT, padx=10, pady=5)

    title_label = tk.Label(
        top_bar,
        text="Список товаров - ООО «Обувь»",
        bg=COLOR_HEADER,
        font=FONT_TITLE,
    )
    title_label.pack(side=tk.LEFT, padx=10)

    if current_user["is_guest"]:
        fio_text = "Гость"
    else:
        fio_text = current_user["full_name"]

    user_label = tk.Label(
        top_bar,
        text=fio_text,
        bg=COLOR_HEADER,
        font=FONT_BOLD,
    )
    user_label.pack(side=tk.RIGHT, padx=20)

    make_button(top_bar, "Выход", show_login_window).pack(side=tk.RIGHT, padx=10)

    role_note = get_role_note(current_user["role_name"])
    note_label = tk.Label(
        main_window,
        text=role_note,
        bg=COLOR_BG,
        font=FONT,
        anchor="w",
    )
    note_label.pack(fill=tk.X, padx=10, pady=4)

    canvas = tk.Canvas(main_window, bg=COLOR_BG)
    scrollbar = tk.Scrollbar(main_window, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg=COLOR_BG)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    try:
        products = fetch_products()
    except Exception as error:
        messagebox.showerror("Ошибка БД", str(error))
        show_login_window()
        return

    if len(products) == 0:
        empty_label = tk.Label(scroll_frame, text="Товары не найдены", bg=COLOR_BG, font=FONT)
        empty_label.pack(padx=20, pady=20)
    else:
        for product_row in products:
            create_product_card(scroll_frame, product_row)


def on_login_click():
    global current_user
    login = login_entry.get().strip()
    password = password_entry.get().strip()

    if login == "" or password == "":
        messagebox.showwarning("Внимание", "Введите логин и пароль")
        return

    try:
        user = auth_user(login, password)
    except Exception as error:
        messagebox.showerror("Ошибка БД", str(error))
        return

    if user is None:
        messagebox.showerror("Ошибка", "Неверный логин или пароль")
        return

    current_user = user
    show_products_window()


def on_guest_click():
    global current_user
    current_user = {
        "full_name": "Гость",
        "role_name": "Гость",
        "is_guest": True,
    }
    show_products_window()


def show_login_window():
    global current_user, login_entry, password_entry
    current_user = None
    clear_window()

    main_window.title("Авторизация - ООО «Обувь»")

    center_frame = tk.Frame(main_window, bg=COLOR_BG)
    center_frame.pack(expand=True)

    logo = load_logo((140, 140))
    if logo is not None:
        logo_label = tk.Label(center_frame, image=logo, bg=COLOR_BG)
        logo_label.image = logo
        logo_label.pack(pady=10)

    title_label = tk.Label(
        center_frame,
        text="Вход в систему - ООО «Обувь»",
        bg=COLOR_BG,
        font=FONT_LOGIN,
    )
    title_label.pack(pady=8)

    login_label = tk.Label(center_frame, text="Логин:", bg=COLOR_BG, font=FONT)
    login_label.pack()
    login_entry = tk.Entry(center_frame, width=40, font=FONT)
    login_entry.pack(pady=4)

    password_label = tk.Label(center_frame, text="Пароль:", bg=COLOR_BG, font=FONT)
    password_label.pack()
    password_entry = tk.Entry(center_frame, width=40, show="*", font=FONT)
    password_entry.pack(pady=4)

    make_accent_button(center_frame, "Войти", on_login_click).pack(pady=8)
    make_accent_button(center_frame, "Войти как гость", on_guest_click).pack(pady=4)


def main():
    global main_window
    main_window = tk.Tk()
    main_window.geometry("1100x750")
    main_window.configure(bg=COLOR_BG)
    main_window.title("ООО «Обувь»")

    if os.path.exists(ICON_PATH):
        main_window.iconbitmap(ICON_PATH)

    setup_style()
    show_login_window()
    main_window.mainloop()


if __name__ == "__main__":
    main()

