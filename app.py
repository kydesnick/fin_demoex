# -*- coding: utf-8 -*-
# Модули 2-4: вход, товары, заказы (простой код, без классов)
import os
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import psycopg2
from PIL import Image, ImageTk
from config import DB_CONFIG

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "images")
ICON = os.path.join(IMG, "Icon.ico")
LOGO = os.path.join(IMG, "Icon.png")
STUB = os.path.join(IMG, "picture.png")

BG = "#FFFFFF"
HDR = "#7FFF00"
ACCENT = "#00FA9A"
GREEN = "#2E8B57"
BLUE = "#87CEFA"
FONT = ("Times New Roman", 11)
FONT_B = ("Times New Roman", 11, "bold")
FONT_H = ("Times New Roman", 14, "bold")
FONT_BIG = ("Times New Roman", 16, "bold")

win = None
user = None
logo_img = None
photos = {}
search_var = None
sort_var = None
sup_var = None
list_frame = None
form_open = False
form_mode = ""
form_article = ""
form_photo_path = None
form_fields = {}

orders_list_frame = None
order_form_open = False
order_form_mode = ""
order_form_id = 0
order_fields = {}

def db(sql, params=None, one=False):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    if params:
        cur.execute(sql, params)
    else:
        cur.execute(sql)
# SELECT
    if sql.strip().upper().startswith("SELECT"):
        data = cur.fetchone() if one else cur.fetchall()
        cur.close()
        conn.close()
        return data
# INSERT UPDATE DELETE
    conn.commit()
    cur.close()
    conn.close()

def clear():
    for w in win.winfo_children():
        w.destroy()

def num(x, d=0):
    try:
        t = str(x).replace(",", ".")
        if "." in t:
            return float(t)
        return int(t)
    except Exception:
        return d

def role_is(*names):
    if user is None:
        return False
    if user["guest"]:
        return "Гость" in names
    return user["role"] in names


def setup_style():
    win.option_add("*Font", FONT)
    style = ttk.Style()
    style.configure("TCombobox", font=FONT)


def load_logo(max_size=(140, 140)):
    global logo_img
    if not os.path.isfile(LOGO):
        return None
    im = Image.open(LOGO)
    im.thumbnail(max_size, Image.Resampling.LANCZOS)
    logo_img = ImageTk.PhotoImage(im)
    return logo_img


def btn(parent, text, cmd):
    return tk.Button(parent, text=text, command=cmd, bg=ACCENT, font=FONT, activebackground=ACCENT)


def btn_plain(parent, text, cmd):
    return tk.Button(parent, text=text, command=cmd, font=FONT, bg=BG)


def load_img(file_name, size=(120, 120)):
    name = str(file_name or "").strip()
    if name == "":
        path = STUB
    else:
        path = os.path.join(IMG, name)
    if not os.path.isfile(path):
        path = STUB
    if not os.path.isfile(path):
        return None
    key = path + str(size)
    if key in photos:
        return photos[key]
    try:
        im = Image.open(path).resize(size)
        tk_im = ImageTk.PhotoImage(im)
        photos[key] = tk_im
        return tk_im
    except Exception:
        return None

def card_color(discount, stock):
    if stock == 0:
        return BLUE
    if discount > 15:
        return GREEN
    return BG

def get_products():
    sql = """
        SELECT article, product_name, category_name, description,
            manufacturer_name, supplier_name, price, unit_name,
            stock_qty, discount_percent, photo_file
        FROM products ORDER BY product_name
    """
    return db(sql)

def get_list(column):
    rows = db("SELECT DISTINCT " + column + " FROM products WHERE " + column + " <> '' ORDER BY 1")
    out = []
    for r in rows:
        out.append(r[0])
    return out

def get_orders():
    try:
        sql = """
            SELECT o.order_id, o.order_articles, o.status_name,
            COALESCE(p.full_address, ''), o.order_date, o.delivery_date
            FROM orders o
            LEFT JOIN pickup_points p ON p.pickup_point_id = o.pickup_point_ref
            ORDER BY o.order_id
        """
        return db(sql)
    except Exception:
        sql = """
            SELECT order_id, order_articles, status_name, '', order_date, delivery_date
            FROM orders ORDER BY order_id
        """
        return db(sql)

def get_pickup_list():
    try:
        return db("SELECT pickup_point_id, full_address FROM pickup_points ORDER BY pickup_point_id")
    except Exception:
        return db("SELECT pickup_point_id, full_address FROM pickup_points ORDER BY 1")

def get_status_list():
    try:
        rows = db("SELECT name FROM order_statuses ORDER BY id")
        out = []
        for r in rows:
            out.append(r[0])
        return out
    except Exception:
        rows = db("SELECT DISTINCT status_name FROM orders WHERE status_name <> ''")
        out = []
        for r in rows:
            out.append(str(r[0]).strip())
        return out

def next_order_id():
    row = db("SELECT COALESCE(MAX(order_id), 0) FROM orders", one=True)
    return int(row[0]) + 1

def date_only(value):
    text = str(value)
    if " " in text:
        return text.split(" ")[0]
    return text

def pickup_id_by_address(address):
    rows = get_pickup_list()
    for r in rows:
        if str(r[1]) == address:
            return r[0]
    return rows[0][0] if len(rows) > 0 else 1

def next_article():
    rows = db("SELECT article FROM products")
    mx = 0
    for r in rows:
        if str(r[0]).isdigit() and int(r[0]) > mx:
            mx = int(r[0])
    return str(mx + 1)

def in_orders(article):
    try:
        n = db("SELECT COUNT(*) FROM order_items WHERE product_article=%s", (article,), one=True)[0]
        return n > 0
    except Exception:
        return False

def filter_products(rows):
    text = search_var.get().strip().lower() if search_var else ""
    sup = sup_var.get() if sup_var else "Все поставщики"
    sort = sort_var.get() if sort_var else "без сортировки"
    out = []
    for row in rows:
        if sup != "Все поставщики" and str(row[5]) != sup:
            continue
        if text != "":
            ok = False
            for part in row:
                if text in str(part).lower():
                    ok = True
                    break
            if not ok:
                continue
        out.append(row)
    if sort == "по возрастанию":
        out.sort(key=lambda x: num(x[8]))
    if sort == "по убыванию":
        out.sort(key=lambda x: num(x[8]), reverse=True)
    return out

def refresh_list():
    if list_frame is None:
        return
    for w in list_frame.winfo_children():
        w.destroy()
    try:
        rows = get_products()
    except Exception as e:
        messagebox.showerror("Ошибка БД", str(e))
        return
    rows = filter_products(rows)
    if len(rows) == 0:
        tk.Label(list_frame, text="Товары не найдены", bg=BG).pack(pady=20)
        return
    for row in rows:
        draw_card(list_frame, row)

def on_filter_change(*a):
    refresh_list()

def draw_card(parent, row):
    art, name, cat, desc, man, sup, price, unit, stock, disc, photo = row
    p = num(price)
    d = num(disc)
    s = num(stock)
    bg = card_color(d, s)

    card = tk.Frame(parent, bg=bg, bd=1, relief=tk.SOLID)
    card.pack(fill=tk.X, padx=8, pady=6)
    if role_is("Администратор"):
        card.bind("<Button-1>", lambda e, a=art: open_form("edit", a))
        card.config(cursor="hand2")

    ph = load_img(photo)
    pl = tk.Label(card, bg=bg)
    pl.grid(row=0, column=0, rowspan=6, padx=8, pady=8)
    if ph:
        pl.config(image=ph)
        pl.image = ph

    tk.Label(card, text=cat + " | " + name, bg=bg, font=FONT_B).grid(row=0, column=1, sticky="w", padx=4)
    lines = [
        "Артикул: " + str(art),
        "Описание: " + str(desc),
        "Производитель: " + str(man),
        "Поставщик: " + str(sup),
        "Ед. изм.: " + str(unit),
        "На складе: " + str(s),
    ]
    r = 1
    for line in lines:
        tk.Label(card, text=line, bg=bg, anchor="w").grid(row=r, column=1, sticky="w", padx=4)
        r = r + 1

    pf = tk.Frame(card, bg=bg)
    pf.grid(row=r, column=1, sticky="w", padx=4)
    if d > 0:
        fin = p - p * d / 100
        tk.Label(pf, text="Цена: %.2f" % p, bg=bg, fg="#FF0000", font=(FONT[0], 10, "overstrike")).pack(side=tk.LEFT)
        tk.Label(pf, text="  %.2f" % fin, bg=bg, fg="#000000", font=FONT_B).pack(side=tk.LEFT)
    else:
        tk.Label(pf, text="Цена: %.2f" % p, bg=bg).pack(side=tk.LEFT)

    tk.Label(card, text="Скидка\n" + str(d) + "%", bg=bg, font=FONT_B).grid(row=0, column=2, padx=12)

def show_products():
    global list_frame, search_var, sort_var, sup_var
    clear()
    win.title("Список товаров - ООО «Обувь»")

    top = tk.Frame(win, bg=HDR)
    top.pack(fill=tk.X)
    lg = load_logo((60, 60))
    if lg:
        lb = tk.Label(top, image=lg, bg=HDR)
        lb.image = lg
        lb.pack(side=tk.LEFT, padx=10, pady=5)
    tk.Label(top, text="Список товаров", bg=HDR, font=FONT_H).pack(side=tk.LEFT, padx=10)
    fio = "Гость" if user["guest"] else user["name"]
    tk.Label(top, text=fio, bg=HDR, font=FONT_B).pack(side=tk.RIGHT, padx=20)
    btn_plain(top, "Выход", show_login).pack(side=tk.RIGHT, padx=10)

    if role_is("Менеджер", "Администратор"):
        panel = tk.Frame(win, bg=BG)
        panel.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(panel, text="Поиск:", bg=BG).grid(row=0, column=0, padx=4)
        search_var = tk.StringVar()
        search_var.trace_add("write", on_filter_change)
        tk.Entry(panel, textvariable=search_var, width=30).grid(row=0, column=1, padx=4)
        tk.Label(panel, text="Сортировка:", bg=BG).grid(row=0, column=2, padx=4)
        sort_var = tk.StringVar(value="без сортировки")
        sort_var.trace_add("write", on_filter_change)
        ttk.Combobox(panel, textvariable=sort_var, values=["без сортировки", "по возрастанию", "по убыванию"], state="readonly", width=16).grid(row=0, column=3)
        tk.Label(panel, text="Поставщик:", bg=BG).grid(row=1, column=0, padx=4)
        sups = ["Все поставщики"] + get_list("supplier_name")
        sup_var = tk.StringVar(value="Все поставщики")
        sup_var.trace_add("write", on_filter_change)
        ttk.Combobox(panel, textvariable=sup_var, values=sups, state="readonly", width=28).grid(row=1, column=1, padx=4)

    btn_row = tk.Frame(win, bg=BG)
    btn_row.pack(fill=tk.X, padx=12, pady=4)
    if role_is("Администратор"):
        btn(btn_row, "Добавить товар", lambda: open_form("add", "")).pack(side=tk.LEFT, padx=4)
    if role_is("Менеджер", "Администратор"):
        btn(btn_row, "Заказы", show_orders).pack(side=tk.LEFT, padx=4)

    cv = tk.Canvas(win, bg=BG)
    sb = tk.Scrollbar(win, command=cv.yview)
    list_frame = tk.Frame(cv, bg=BG)
    list_frame.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
    cv.create_window((0, 0), window=list_frame, anchor="nw")
    cv.configure(yscrollcommand=sb.set)
    cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    refresh_list()

def close_form():
    global form_open, form_photo_path, form_fields
    if "win" in form_fields:
        try:
            form_fields["win"].destroy()
        except Exception:
            pass
    form_open = False
    form_photo_path = None
    form_fields = {}

def check_form():
    name = form_fields["name"].get().strip()
    cat = form_fields["cat"].get().strip()
    man = form_fields["man"].get().strip()
    sup = form_fields["sup"].get().strip()
    unit = form_fields["unit"].get().strip()
    if name == "":
        messagebox.showwarning("Проверка данных", "Заполните наименование товара.")
        return False
    if cat == "":
        messagebox.showwarning("Проверка данных", "Выберите категорию товара.")
        return False
    if man == "":
        messagebox.showwarning("Проверка данных", "Выберите производителя.")
        return False
    if sup == "":
        messagebox.showwarning("Проверка данных", "Укажите поставщика.")
        return False
    if unit == "":
        messagebox.showwarning("Проверка данных", "Укажите единицу измерения (например: шт.).")
        return False
    try:
        price = float(form_fields["price"].get().replace(",", "."))
        stock = int(form_fields["stock"].get())
        disc = int(form_fields["disc"].get())
    except Exception:
        messagebox.showwarning(
            "Проверка данных",
            "Цена — число (можно с копейками: 1999.99).\nСклад и скидка — целые числа.",
        )
        return False
    if price < 0:
        messagebox.showwarning("Проверка данных", "Цена не может быть отрицательной.")
        return False
    if stock < 0:
        messagebox.showwarning("Проверка данных", "Количество на складе не может быть отрицательным.")
        return False
    if disc < 0 or disc > 100:
        messagebox.showwarning("Проверка данных", "Скидка должна быть от 0 до 100 процентов.")
        return False
    return True

def remove_old_photo(file_name):
    if file_name is None:
        return
    name = str(file_name).strip()
    if name == "" or name == "picture.png":
        return
    path = os.path.join(IMG, name)
    if not os.path.isfile(path):
        return
    try:
        n = db("SELECT COUNT(*) FROM products WHERE photo_file=%s", (name,), one=True)[0]
        if n <= 1:
            os.remove(path)
    except Exception:
        pass

def save_photo(src, article):
    im = Image.open(src).resize((300, 200))
    fname = "product_" + str(article) + ".jpg"
    im.save(os.path.join(IMG, fname), "JPEG")
    return fname

def save_product():
    global form_photo_path
    if not check_form():
        return
    vals = (
        form_fields["name"].get().strip(),
        form_fields["cat"].get().strip(),
        form_fields["desc"].get().strip(),
        form_fields["man"].get().strip(),
        form_fields["sup"].get().strip(),
        form_fields["price"].get().strip().replace(",", "."),
        form_fields["unit"].get().strip(),
        form_fields["stock"].get().strip(),
        form_fields["disc"].get().strip(),
    )
    photo = form_fields["old_photo"]
    old_photo_name = photo
    try:
        if form_mode == "add":
            art = next_article()
            if form_photo_path:
                photo = save_photo(form_photo_path, art)
            sql = """INSERT INTO products(article,product_name,category_name,description,
                manufacturer_name,supplier_name,price,unit_name,stock_qty,discount_percent,photo_file)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            db(sql, (art,) + vals + (photo,))
            messagebox.showinfo("Успех", "Товар добавлен. Артикул: " + str(art))
        else:
            art = form_article
            if form_photo_path:
                photo = save_photo(form_photo_path, art)
                remove_old_photo(old_photo_name)
            sql = """UPDATE products SET product_name=%s,category_name=%s,description=%s,
                manufacturer_name=%s,supplier_name=%s,price=%s,unit_name=%s,stock_qty=%s,
                discount_percent=%s,photo_file=%s WHERE article=%s"""
            db(sql, vals + (photo, art))
            messagebox.showinfo("Успех", "Данные товара сохранены.")
    except Exception as e:
        messagebox.showerror(
            "Ошибка сохранения",
            "Не удалось сохранить товар в базу данных.\n\n" + str(e),
        )
        return
    close_form()
    show_products()

def delete_product():
    if in_orders(form_article):
        messagebox.showwarning(
            "Удаление запрещено",
            "Этот товар есть в заказах. Сначала уберите его из заказов, затем удаляйте.",
        )
        return
    if not messagebox.askyesno(
        "Подтверждение удаления",
        "Удалить товар? Это действие нельзя отменить.",
    ):
        return
    old_photo_name = form_fields["old_photo"]
    try:
        db("DELETE FROM products WHERE article=%s", (form_article,))
    except Exception as e:
        messagebox.showerror(
            "Ошибка удаления",
            "Не удалось удалить товар.\n\n" + str(e),
        )
        return
    remove_old_photo(old_photo_name)
    messagebox.showinfo("Успех", "Товар удалён.")
    close_form()
    show_products()

def pick_photo():
    global form_photo_path
    path = filedialog.askopenfilename(filetypes=[("Картинки", "*.jpg *.png *.jpeg")])
    if path == "":
        return
    try:
        im = Image.open(path).resize((120, 80))
        tk_im = ImageTk.PhotoImage(im)
        form_fields["ph"].config(image=tk_im)
        form_fields["ph"].image = tk_im
        form_photo_path = path
    except Exception as e:
        messagebox.showerror(
            "Ошибка изображения",
            "Не удалось открыть файл. Выберите JPG или PNG.\n\n" + str(e),
        )

def add_field(frame, row, label, key, value="", combo=None):
    tk.Label(frame, text=label, bg=BG).grid(row=row, column=0, sticky="w", pady=3)
    if combo is not None:
        w = ttk.Combobox(frame, values=combo, width=37)
        w.set(value)
    else:
        w = tk.Entry(frame, width=40)
        w.insert(0, value)
    w.grid(row=row, column=1, pady=3)
    form_fields[key] = w

def open_form(mode, article):
    global form_open, form_mode, form_article, form_photo_path, form_fields
    if not role_is("Администратор"):
        messagebox.showwarning("Доступ", "Только для администратора")
        return
    if form_open:
        messagebox.showwarning("Внимание", "Уже открыта форма редактирования")
        return
    form_open = True
    form_mode = mode
    form_article = article
    form_photo_path = None
    form_fields = {}

    fw = tk.Toplevel(win)
    form_fields["win"] = fw
    fw.title("Добавление товара" if mode == "add" else "Редактирование товара")
    fw.geometry("650x700")
    fw.configure(bg=BG)
    fw.grab_set()
    fw.protocol("WM_DELETE_WINDOW", close_form)

    btn_plain(fw, "Назад", close_form).pack(anchor="w", padx=10, pady=8)
    ph = tk.Label(fw, bg=BG)
    ph.pack(pady=6)
    form_fields["ph"] = ph
    tk.Button(fw, text="Выбрать фото", command=pick_photo).pack()

    fr = tk.Frame(fw, bg=BG)
    fr.pack(padx=12, pady=8)
    cats = get_list("category_name")
    mans = get_list("manufacturer_name")

    if mode == "edit":
        sql = """
            SELECT article, product_name, category_name, description,
                manufacturer_name, supplier_name, price, unit_name,
                stock_qty, discount_percent, photo_file
            FROM products WHERE article=%s
        """
        p = db(sql, (article,), one=True)
        if p is None:
            messagebox.showerror("Ошибка", "Товар не найден")
            close_form()
            return
        form_fields["old_photo"] = str(p[10] or "picture.png")
        im = load_img(p[10], (120, 80))
        if im:
            ph.config(image=im)
            ph.image = im
        tk.Label(fr, text="ID (артикул):", bg=BG).grid(row=0, column=0, sticky="w")
        e = tk.Entry(fr, width=40)
        e.insert(0, p[0])
        e.config(state="readonly")
        e.grid(row=0, column=1)
        add_field(fr, 1, "Наименование:", "name", p[1])
        add_field(fr, 2, "Категория:", "cat", p[2], cats)
        add_field(fr, 3, "Описание:", "desc", p[3])
        add_field(fr, 4, "Производитель:", "man", p[4], mans)
        add_field(fr, 5, "Поставщик:", "sup", p[5])
        add_field(fr, 6, "Цена:", "price", p[6])
        add_field(fr, 7, "Ед. изм.:", "unit", p[7])
        add_field(fr, 8, "На складе:", "stock", p[8])
        add_field(fr, 9, "Скидка %:", "disc", p[9])
    else:
        form_fields["old_photo"] = "picture.png"
        im = load_img("picture.png", (120, 80))
        if im:
            ph.config(image=im)
            ph.image = im
        add_field(fr, 0, "Наименование:", "name", "")
        add_field(fr, 1, "Категория:", "cat", "", cats)
        add_field(fr, 2, "Описание:", "desc", "")
        add_field(fr, 3, "Производитель:", "man", "", mans)
        add_field(fr, 4, "Поставщик:", "sup", "")
        add_field(fr, 5, "Цена:", "price", "")
        add_field(fr, 6, "Ед. изм.:", "unit", "шт.")
        add_field(fr, 7, "На складе:", "stock", "0")
        add_field(fr, 8, "Скидка %:", "disc", "0")

    btns = tk.Frame(fw, bg=BG)
    btns.pack(pady=10)
    btn(btns, "Сохранить", save_product).pack(side=tk.LEFT, padx=6)
    if mode == "edit":
        btn_plain(btns, "Удалить", delete_product).pack(side=tk.LEFT, padx=6)

def do_login():
    global user
    login = login_box.get().strip()
    pwd = pass_box.get().strip()
    if login == "" or pwd == "":
        messagebox.showwarning("Внимание", "Введите логин и пароль")
        return
    try:
        row = db("SELECT full_name, role_name FROM users WHERE login=%s AND password_plain=%s", (login, pwd), one=True)
    except Exception as e:
        messagebox.showerror("Ошибка БД", str(e))
        return
    if row is None:
        messagebox.showerror(
            "Ошибка авторизации",
            "Неверный логин или пароль. Проверьте данные и попробуйте снова.",
        )
        return
    user = {"name": row[0], "role": row[1], "guest": False}
    show_products()

def close_order_form():
    global order_form_open, order_fields
    if "win" in order_fields:
        try:
            order_fields["win"].destroy()
        except Exception:
            pass
    order_form_open = False
    order_fields = {}

def refresh_orders_list():
    if orders_list_frame is None:
        return
    for w in orders_list_frame.winfo_children():
        w.destroy()
    try:
        rows = get_orders()
    except Exception as e:
        messagebox.showerror("Ошибка БД", "Не удалось загрузить заказы.\n\n" + str(e))
        return
    if len(rows) == 0:
        tk.Label(orders_list_frame, text="Заказы не найдены", bg=BG).pack(pady=20)
        return
    for row in rows:
        draw_order_card(orders_list_frame, row)

def draw_order_card(parent, row):
    oid = row[0]
    articles = row[1]
    status = row[2]
    address = row[3]
    odate = date_only(row[4])
    ddate = date_only(row[5])

    card = tk.Frame(parent, bg=BG, bd=1, relief=tk.SOLID)
    card.pack(fill=tk.X, padx=8, pady=6)
    if role_is("Администратор"):
        card.bind("<Button-1>", lambda e, x=oid: open_order_form("edit", x))
        card.config(cursor="hand2")

    left = tk.Frame(card, bg=BG)
    left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
    tk.Label(left, text="Артикул заказа: " + str(articles), bg=BG, font=FONT_B, anchor="w").pack(anchor="w")
    tk.Label(left, text="Статус заказа: " + str(status), bg=BG, anchor="w").pack(anchor="w")
    tk.Label(left, text="Адрес пункта выдачи: " + str(address), bg=BG, anchor="w").pack(anchor="w")
    tk.Label(left, text="Дата заказа: " + str(odate), bg=BG, anchor="w").pack(anchor="w")

    right = tk.Frame(card, bg=BG, bd=1, relief=tk.SOLID, width=140, height=80)
    right.pack(side=tk.RIGHT, padx=10, pady=8)
    right.pack_propagate(False)
    tk.Label(right, text="Дата доставки", bg=BG, font=FONT_B).pack(pady=4)
    tk.Label(right, text=str(ddate), bg=BG).pack()


def show_orders():
    global orders_list_frame
    if not role_is("Менеджер", "Администратор"):
        messagebox.showwarning("Доступ", "Заказы доступны менеджеру и администратору.")
        return
    clear()
    win.title("Список заказов - ООО «Обувь»")

    top = tk.Frame(win, bg=HDR)
    top.pack(fill=tk.X)
    lg = load_logo((60, 60))
    if lg:
        lb = tk.Label(top, image=lg, bg=HDR)
        lb.image = lg
        lb.pack(side=tk.LEFT, padx=10, pady=5)
    tk.Label(top, text="Список заказов", bg=HDR, font=FONT_H).pack(side=tk.LEFT, padx=10)
    fio = "Гость" if user["guest"] else user["name"]
    tk.Label(top, text=fio, bg=HDR, font=FONT_B).pack(side=tk.RIGHT, padx=20)
    btn_plain(top, "Выход", show_login).pack(side=tk.RIGHT, padx=10)
    btn_plain(top, "Назад к товарам", show_products).pack(side=tk.RIGHT, padx=10)

    btn_row = tk.Frame(win, bg=BG)
    btn_row.pack(fill=tk.X, padx=12, pady=6)
    if role_is("Администратор"):
        btn(btn_row, "Добавить заказ", lambda: open_order_form("add", 0)).pack(side=tk.LEFT)

    cv = tk.Canvas(win, bg=BG)
    sb = tk.Scrollbar(win, command=cv.yview)
    orders_list_frame = tk.Frame(cv, bg=BG)
    orders_list_frame.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
    cv.create_window((0, 0), window=orders_list_frame, anchor="nw")
    cv.configure(yscrollcommand=sb.set)
    cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    refresh_orders_list()

def check_order_form():
    art = order_fields["articles"].get().strip()
    status = order_fields["status"].get().strip()
    address = order_fields["address"].get().strip()
    odate = order_fields["odate"].get().strip()
    ddate = order_fields["ddate"].get().strip()
    if art == "":
        messagebox.showwarning("Проверка данных", "Укажите артикул заказа (товары и количество).")
        return False
    if status == "":
        messagebox.showwarning("Проверка данных", "Выберите статус заказа.")
        return False
    if address == "":
        messagebox.showwarning("Проверка данных", "Выберите адрес пункта выдачи.")
        return False
    if odate == "" or ddate == "":
        messagebox.showwarning("Проверка данных", "Укажите дату заказа и дату выдачи.")
        return False
    return True

def save_order():
    if not check_order_form():
        return
    articles = order_fields["articles"].get().strip()
    status = order_fields["status"].get().strip()
    address = order_fields["address"].get().strip()
    odate = order_fields["odate"].get().strip()
    ddate = order_fields["ddate"].get().strip()
    pickup_ref = pickup_id_by_address(address)
    try:
        if order_form_mode == "add":
            oid = next_order_id()
            client = db("SELECT full_name FROM users LIMIT 1", one=True)
            cname = client[0] if client else "Клиент"
            sql = """
                INSERT INTO orders(order_id, order_articles, order_date, delivery_date,
                    pickup_point_ref, client_full_name, pickup_code, status_name)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
            """
            db(sql, (oid, articles, odate, ddate, pickup_ref, cname, str(oid), status))
            messagebox.showinfo("Успех", "Заказ добавлен. Номер: " + str(oid))
        else:
            sql = """
                UPDATE orders SET order_articles=%s, status_name=%s, order_date=%s,
                    delivery_date=%s, pickup_point_ref=%s
                WHERE order_id=%s
            """
            db(sql, (articles, status, odate, ddate, pickup_ref, order_form_id))
            messagebox.showinfo("Успех", "Заказ сохранён.")
    except Exception as e:
        messagebox.showerror("Ошибка сохранения", "Не удалось сохранить заказ.\n\n" + str(e))
        return
    close_order_form()
    show_orders()

def delete_order():
    if not messagebox.askyesno("Подтверждение", "Удалить заказ? Это действие нельзя отменить."):
        return
    try:
        db("DELETE FROM order_items WHERE order_id=%s", (order_form_id,))
    except Exception:
        pass
    try:
        db("DELETE FROM orders WHERE order_id=%s", (order_form_id,))
    except Exception as e:
        messagebox.showerror("Ошибка удаления", "Не удалось удалить заказ.\n\n" + str(e))
        return
    messagebox.showinfo("Успех", "Заказ удалён.")
    close_order_form()
    show_orders()

def open_order_form(mode, order_id):
    global order_form_open, order_form_mode, order_form_id, order_fields
    if not role_is("Администратор"):
        messagebox.showwarning("Доступ", "Редактирование заказов только для администратора.")
        return
    if order_form_open:
        messagebox.showwarning("Внимание", "Уже открыта форма заказа. Сначала закройте её.")
        return
    order_form_open = True
    order_form_mode = mode
    order_form_id = order_id
    order_fields = {}

    fw = tk.Toplevel(win)
    order_fields["win"] = fw
    fw.title("Добавление заказа" if mode == "add" else "Редактирование заказа")
    fw.geometry("620x480")
    fw.configure(bg=BG)
    fw.grab_set()
    fw.protocol("WM_DELETE_WINDOW", close_order_form)

    btn_plain(fw, "Назад", close_order_form).pack(anchor="w", padx=10, pady=8)
    fr = tk.Frame(fw, bg=BG)
    fr.pack(padx=12, pady=8)

    statuses = get_status_list()
    pickups = get_pickup_list()
    addresses = []
    for p in pickups:
        addresses.append(str(p[1]))

    if mode == "edit":
        row = db(
            """
            SELECT o.order_id, o.order_articles, o.status_name,
            COALESCE(p.full_address, ''), o.order_date, o.delivery_date
            FROM orders o
            LEFT JOIN pickup_points p ON p.pickup_point_id = o.pickup_point_ref
            WHERE o.order_id=%s
            """,
            (order_id,),
            one=True,
        )
        if row is None:
            messagebox.showerror("Ошибка", "Заказ не найден.")
            close_order_form()
            return
        def_art = row[1]
        def_status = str(row[2]).strip()
        def_addr = row[3]
        def_odate = date_only(row[4])
        def_ddate = date_only(row[5])
        tk.Label(fr, text="Номер заказа:", bg=BG).grid(row=0, column=0, sticky="w", pady=3)
        e = tk.Entry(fr, width=40)
        e.insert(0, str(row[0]))
        e.config(state="readonly")
        e.grid(row=0, column=1, pady=3)
        start_row = 1
    else:
        def_art = ""
        def_status = statuses[0] if len(statuses) > 0 else "Новый"
        def_addr = addresses[0] if len(addresses) > 0 else ""
        def_odate = ""
        def_ddate = ""
        start_row = 0

    tk.Label(fr, text="Артикул заказа:", bg=BG).grid(row=start_row, column=0, sticky="w", pady=3)
    e_art = tk.Entry(fr, width=40)
    e_art.insert(0, def_art)
    e_art.grid(row=start_row, column=1, pady=3)
    order_fields["articles"] = e_art

    tk.Label(fr, text="Статус заказа:", bg=BG).grid(row=start_row + 1, column=0, sticky="w", pady=3)
    cb_st = ttk.Combobox(fr, values=statuses, width=37)
    cb_st.set(def_status)
    cb_st.grid(row=start_row + 1, column=1, pady=3)
    order_fields["status"] = cb_st

    tk.Label(fr, text="Адрес пункта выдачи:", bg=BG).grid(row=start_row + 2, column=0, sticky="w", pady=3)
    cb_addr = ttk.Combobox(fr, values=addresses, width=37)
    cb_addr.set(def_addr)
    cb_addr.grid(row=start_row + 2, column=1, pady=3)
    order_fields["address"] = cb_addr

    tk.Label(fr, text="Дата заказа:", bg=BG).grid(row=start_row + 3, column=0, sticky="w", pady=3)
    e_od = tk.Entry(fr, width=40)
    e_od.insert(0, def_odate)
    e_od.grid(row=start_row + 3, column=1, pady=3)
    order_fields["odate"] = e_od

    tk.Label(fr, text="Дата выдачи:", bg=BG).grid(row=start_row + 4, column=0, sticky="w", pady=3)
    e_dd = tk.Entry(fr, width=40)
    e_dd.insert(0, def_ddate)
    e_dd.grid(row=start_row + 4, column=1, pady=3)
    order_fields["ddate"] = e_dd

    btns = tk.Frame(fw, bg=BG)
    btns.pack(pady=10)
    btn(btns, "Сохранить", save_order).pack(side=tk.LEFT, padx=6)
    if mode == "edit":
        btn_plain(btns, "Удалить", delete_order).pack(side=tk.LEFT, padx=6)

def show_login():
    global user, login_box, pass_box
    user = None
    close_form()
    close_order_form()
    clear()
    win.title("Авторизация - ООО «Обувь»")
    f = tk.Frame(win, bg=BG)
    f.pack(expand=True)
    lg = load_logo((140, 140))
    if lg:
        lb = tk.Label(f, image=lg, bg=BG)
        lb.image = lg
        lb.pack(pady=10)
    tk.Label(f, text="Вход в систему - ООО «Обувь»", bg=BG, font=FONT_BIG).pack(pady=8)
    tk.Label(f, text="Логин:", bg=BG).pack()
    login_box = tk.Entry(f, width=40)
    login_box.pack(pady=4)
    tk.Label(f, text="Пароль:", bg=BG).pack()
    pass_box = tk.Entry(f, width=40, show="*")
    pass_box.pack(pady=4)
    btn(f, "Войти", do_login).pack(pady=8)
    btn(f, "Войти как гость", do_guest).pack(pady=4)

def do_guest():
    global user
    user = {"name": "Гость", "role": "Гость", "guest": True}
    show_products()

def main():
    global win
    win = tk.Tk()
    win.geometry("1100x750")
    win.configure(bg=BG)
    if os.path.exists(ICON):
        try:
            win.iconbitmap(ICON)
        except Exception:
            pass
    setup_style()
    show_login()
    win.mainloop()

if __name__ == "__main__":
    main()