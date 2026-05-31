# -*- coding: utf-8 -*-
# Упрощённое приложение: модули 2 + 3 + 4 (без классов)
# Запуск: cd fin_demoex  →  python app_simple.py
import os
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import psycopg2
from PIL import Image, ImageTk

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "ffee",
    "user": "postgres",
    "password": "postgres",
}

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

win = None
user = None
logo_img = None
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


# ========== БАЗА ДАННЫХ ==========

def db(sql, params=None, one=False):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    if params:
        cur.execute(sql, params)
    else:
        cur.execute(sql)
    if sql.strip().upper().startswith("SELECT"):
        data = cur.fetchone() if one else cur.fetchall()
    else:
        conn.commit()
        data = None
    cur.close()
    conn.close()
    return data


# ========== ОБЩИЕ ПОМОЩНИКИ ==========

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


def green_btn(parent, text, cmd):
    return tk.Button(parent, text=text, command=cmd, bg=ACCENT, font=FONT, activebackground=ACCENT)


def plain_btn(parent, text, cmd):
    return tk.Button(parent, text=text, command=cmd, font=FONT, bg=BG)


def load_logo(size=(140, 140)):
    global logo_img
    if not os.path.isfile(LOGO):
        return None
    im = Image.open(LOGO)
    im.thumbnail(size, Image.Resampling.LANCZOS)
    logo_img = ImageTk.PhotoImage(im)
    return logo_img


def load_img(file_name, size=(120, 120)):
    name = str(file_name or "").strip()
    path = os.path.join(IMG, name) if name else STUB
    if not os.path.isfile(path):
        path = STUB
    if not os.path.isfile(path):
        return None
    try:
        im = Image.open(path).resize(size)
        tk_im = ImageTk.PhotoImage(im)
        return tk_im
    except Exception:
        return None


def card_color(discount, stock):
    if stock == 0:
        return BLUE
    if discount > 15:
        return GREEN
    return BG


def make_header(title, back_cmd=None):
    top = tk.Frame(win, bg=HDR)
    top.pack(fill=tk.X)
    tk.Label(top, text=title, bg=HDR, font=FONT_H).pack(side=tk.LEFT, padx=12, pady=8)
    fio = "Гость" if user["guest"] else user["name"]
    tk.Label(top, text=fio, bg=HDR, font=FONT_B).pack(side=tk.RIGHT, padx=16)
    plain_btn(top, "Выход", show_login).pack(side=tk.RIGHT, padx=6)
    if back_cmd:
        plain_btn(top, "Назад", back_cmd).pack(side=tk.RIGHT, padx=6)


def make_scroll():
    cv = tk.Canvas(win, bg=BG)
    sb = tk.Scrollbar(win, command=cv.yview)
    frame = tk.Frame(cv, bg=BG)
    frame.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
    cv.create_window((0, 0), window=frame, anchor="nw")
    cv.configure(yscrollcommand=sb.set)
    cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    return frame


def get_list(column):
    rows = db("SELECT DISTINCT " + column + " FROM products WHERE " + column + " <> '' ORDER BY 1")
    return [r[0] for r in rows]


def in_orders(article):
    art = str(article).strip()
    if art == "":
        return False
    n = db("SELECT COUNT(*) FROM orders WHERE order_articles LIKE %s", ("%" + art + "%",), one=True)[0]
    return n > 0


# ========== МОДУЛЬ 2: ТОВАРЫ ==========

def get_products():
    return db("""
        SELECT article, product_name, category_name, description,
               manufacturer_name, supplier_name, price, unit_name,
               stock_qty, discount_percent, photo_file
        FROM products ORDER BY product_name
    """)


def filter_products(rows):
    text = search_var.get().strip().lower() if search_var else ""
    sup = sup_var.get() if sup_var else "Все поставщики"
    sort = sort_var.get() if sort_var else "без сортировки"
    out = []
    for row in rows:
        if sup != "Все поставщики" and str(row[5]) != sup:
            continue
        if text:
            found = False
            for part in row:
                if text in str(part).lower():
                    found = True
                    break
            if not found:
                continue
        out.append(row)
    if sort == "по возрастанию":
        out.sort(key=lambda x: num(x[8]))
    if sort == "по убыванию":
        out.sort(key=lambda x: num(x[8]), reverse=True)
    return out


def draw_card(parent, row):
    art, name, cat, desc, man, sup, price, unit, stock, disc, photo = row
    p, d, s = num(price), num(disc), num(stock)
    bg = card_color(d, s)
    card = tk.Frame(parent, bg=bg, bd=1, relief=tk.SOLID)
    card.pack(fill=tk.X, padx=8, pady=6)
    if role_is("Администратор"):
        card.bind("<Button-1>", lambda e, a=art: open_form("edit", a))
        card.config(cursor="hand2")

    pl = tk.Label(card, bg=bg)
    pl.grid(row=0, column=0, rowspan=6, padx=8, pady=8)
    ph = load_img(photo)
    if ph:
        pl.config(image=ph)
        pl.image = ph

    tk.Label(card, text=cat + " | " + name, bg=bg, font=FONT_B).grid(row=0, column=1, sticky="w", padx=4)
    for i, line in enumerate([
        "Описание: " + str(desc), "Производитель: " + str(man), "Поставщик: " + str(sup),
        "Ед. изм.: " + str(unit), "На складе: " + str(s),
    ], start=1):
        tk.Label(card, text=line, bg=bg, anchor="w").grid(row=i, column=1, sticky="w", padx=4)

    pf = tk.Frame(card, bg=bg)
    pf.grid(row=6, column=1, sticky="w", padx=4)
    if d > 0:
        fin = p - p * d / 100
        tk.Label(pf, text="Цена: %.2f" % p, bg=bg, fg="#FF0000", font=(FONT[0], 10, "overstrike")).pack(side=tk.LEFT)
        tk.Label(pf, text="  %.2f" % fin, bg=bg, font=FONT_B).pack(side=tk.LEFT)
    else:
        tk.Label(pf, text="Цена: %.2f" % p, bg=bg).pack(side=tk.LEFT)
    tk.Label(card, text="Скидка\n" + str(d) + "%", bg=bg, font=FONT_B).grid(row=0, column=2, padx=12)


def refresh_list():
    if list_frame is None:
        return
    for w in list_frame.winfo_children():
        w.destroy()
    try:
        rows = filter_products(get_products())
    except Exception as e:
        messagebox.showerror("Ошибка БД", str(e))
        return
    if not rows:
        tk.Label(list_frame, text="Товары не найдены", bg=BG).pack(pady=20)
        return
    for row in rows:
        draw_card(list_frame, row)


def show_products():
    global list_frame, search_var, sort_var, sup_var
    clear()
    win.title("Список товаров - ООО «Обувь»")
    make_header("Список товаров - ООО «Обувь»")

    if role_is("Менеджер", "Администратор"):
        panel = tk.Frame(win, bg=BG)
        panel.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(panel, text="Поиск:", bg=BG).grid(row=0, column=0, padx=4)
        search_var = tk.StringVar()
        search_var.trace_add("write", lambda *a: refresh_list())
        tk.Entry(panel, textvariable=search_var, width=30).grid(row=0, column=1, padx=4)
        tk.Label(panel, text="Сортировка:", bg=BG).grid(row=0, column=2, padx=4)
        sort_var = tk.StringVar(value="без сортировки")
        sort_var.trace_add("write", lambda *a: refresh_list())
        ttk.Combobox(panel, textvariable=sort_var,
                     values=["без сортировки", "по возрастанию", "по убыванию"],
                     state="readonly", width=16).grid(row=0, column=3)
        tk.Label(panel, text="Поставщик:", bg=BG).grid(row=1, column=0, padx=4)
        sup_var = tk.StringVar(value="Все поставщики")
        sup_var.trace_add("write", lambda *a: refresh_list())
        ttk.Combobox(panel, textvariable=sup_var,
                     values=["Все поставщики"] + get_list("supplier_name"),
                     state="readonly", width=28).grid(row=1, column=1, padx=4)

    row_btns = tk.Frame(win, bg=BG)
    row_btns.pack(fill=tk.X, padx=12, pady=4)
    if role_is("Администратор"):
        green_btn(row_btns, "Добавить товар", lambda: open_form("add", "")).pack(side=tk.LEFT, padx=4)
    if role_is("Менеджер", "Администратор"):
        green_btn(row_btns, "Заказы", show_orders).pack(side=tk.LEFT, padx=4)

    list_frame = make_scroll()
    refresh_list()


# ========== МОДУЛЬ 3: ФОРМА ТОВАРА ==========

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


def check_form():
    if form_fields["name"].get().strip() == "":
        messagebox.showwarning("Ошибка", "Укажите наименование.")
        return False
    if form_fields["cat"].get().strip() == "":
        messagebox.showwarning("Ошибка", "Укажите категорию.")
        return False
    if form_fields["man"].get().strip() == "":
        messagebox.showwarning("Ошибка", "Укажите производителя.")
        return False
    if form_fields["sup"].get().strip() == "":
        messagebox.showwarning("Ошибка", "Укажите поставщика.")
        return False
    try:
        price = float(form_fields["price"].get().replace(",", "."))
        stock = int(form_fields["stock"].get())
        disc = int(form_fields["disc"].get())
    except Exception:
        messagebox.showwarning("Ошибка", "Цена, склад и скидка — числа.")
        return False
    if price < 0 or stock < 0 or disc < 0 or disc > 100:
        messagebox.showwarning("Ошибка", "Цена и склад ≥ 0, скидка 0–100.")
        return False
    return True


def next_article():
    mx = 0
    for r in db("SELECT article FROM products"):
        if str(r[0]).isdigit() and int(r[0]) > mx:
            mx = int(r[0])
    return str(mx + 1)


def save_photo(src, article):
    im = Image.open(src).resize((300, 200))
    fname = "product_" + str(article) + ".jpg"
    im.save(os.path.join(IMG, fname), "JPEG")
    return fname


def remove_old_photo(name):
    name = str(name or "").strip()
    if name in ("", "picture.png"):
        return
    path = os.path.join(IMG, name)
    if os.path.isfile(path):
        n = db("SELECT COUNT(*) FROM products WHERE photo_file=%s", (name,), one=True)[0]
        if n <= 1:
            os.remove(path)


def save_product():
    global form_photo_path
    if not check_form():
        return
    vals = (
        form_fields["name"].get().strip(), form_fields["cat"].get().strip(),
        form_fields["desc"].get().strip(), form_fields["man"].get().strip(),
        form_fields["sup"].get().strip(), form_fields["price"].get().strip().replace(",", "."),
        form_fields["unit"].get().strip(), form_fields["stock"].get().strip(),
        form_fields["disc"].get().strip(),
    )
    photo = form_fields["old_photo"]
    try:
        if form_mode == "add":
            art = next_article()
            if form_photo_path:
                photo = save_photo(form_photo_path, art)
            db("""INSERT INTO products(article,product_name,category_name,description,
                manufacturer_name,supplier_name,price,unit_name,stock_qty,discount_percent,photo_file)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (art,) + vals + (photo,))
            messagebox.showinfo("Готово", "Товар добавлен: " + art)
        else:
            art = form_article
            old = form_fields["old_photo"]
            if form_photo_path:
                photo = save_photo(form_photo_path, art)
                remove_old_photo(old)
            db("""UPDATE products SET product_name=%s,category_name=%s,description=%s,
                manufacturer_name=%s,supplier_name=%s,price=%s,unit_name=%s,stock_qty=%s,
                discount_percent=%s,photo_file=%s WHERE article=%s""", vals + (photo, art))
            messagebox.showinfo("Готово", "Товар сохранён.")
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))
        return
    close_form()
    show_products()


def delete_product():
    if in_orders(form_article):
        messagebox.showwarning("Ошибка", "Товар в заказе — удалить нельзя.")
        return
    if not messagebox.askyesno("Удаление", "Удалить товар?"):
        return
    try:
        db("DELETE FROM products WHERE article=%s", (form_article,))
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))
        return
    messagebox.showinfo("Готово", "Товар удалён.")
    close_form()
    show_products()


def pick_photo():
    global form_photo_path
    path = filedialog.askopenfilename(filetypes=[("Картинки", "*.jpg *.png *.jpeg")])
    if not path:
        return
    try:
        tk_im = ImageTk.PhotoImage(Image.open(path).resize((120, 80)))
        form_fields["ph"].config(image=tk_im)
        form_fields["ph"].image = tk_im
        form_photo_path = path
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))


def open_form(mode, article):
    global form_open, form_mode, form_article, form_photo_path, form_fields
    if not role_is("Администратор"):
        messagebox.showwarning("Доступ", "Только администратор.")
        return
    if form_open:
        messagebox.showwarning("Внимание", "Форма уже открыта.")
        return
    form_open = True
    form_mode = mode
    form_article = article
    form_photo_path = None
    form_fields = {}

    fw = tk.Toplevel(win)
    form_fields["win"] = fw
    fw.title("Добавление товара" if mode == "add" else "Редактирование товара")
    fw.geometry("650x680")
    fw.configure(bg=BG)
    fw.protocol("WM_DELETE_WINDOW", close_form)

    plain_btn(fw, "Назад", close_form).pack(anchor="w", padx=10, pady=8)
    ph = tk.Label(fw, bg=BG)
    ph.pack(pady=4)
    form_fields["ph"] = ph
    plain_btn(fw, "Выбрать фото", pick_photo).pack()

    fr = tk.Frame(fw, bg=BG)
    fr.pack(padx=12, pady=8)
    cats = get_list("category_name")
    mans = get_list("manufacturer_name")

    if mode == "edit":
        p = db("""SELECT article, product_name, category_name, description,
            manufacturer_name, supplier_name, price, unit_name, stock_qty, discount_percent, photo_file
            FROM products WHERE article=%s""", (article,), one=True)
        if not p:
            messagebox.showerror("Ошибка", "Товар не найден.")
            close_form()
            return
        form_fields["old_photo"] = str(p[10] or "picture.png")
        im = load_img(p[10], (120, 80))
        if im:
            ph.config(image=im)
            ph.image = im
        e = tk.Entry(fr, width=40, state="readonly")
        e.grid(row=0, column=1, pady=3)
        e.insert(0, p[0])
        tk.Label(fr, text="Артикул:", bg=BG).grid(row=0, column=0, sticky="w")
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
    green_btn(btns, "Сохранить", save_product).pack(side=tk.LEFT, padx=6)
    if mode == "edit":
        plain_btn(btns, "Удалить", delete_product).pack(side=tk.LEFT, padx=6)


# ========== МОДУЛЬ 4: ЗАКАЗЫ ==========

def get_orders():
    return db("""
        SELECT o.order_id, o.order_articles, o.status_name,
               COALESCE(p.full_address, ''), o.order_date, o.delivery_date
        FROM orders o
        LEFT JOIN pickup_points p ON p.pickup_point_id = o.pickup_point_ref
        ORDER BY o.order_id
    """)


def get_status_list():
    rows = db("SELECT name FROM order_statuses ORDER BY id")
    if rows:
        return [r[0] for r in rows]
    rows = db("SELECT DISTINCT status_name FROM orders WHERE status_name <> ''")
    return [str(r[0]).strip() for r in rows]


def get_pickup_addresses():
    rows = db("SELECT full_address FROM pickup_points ORDER BY pickup_point_id")
    return [str(r[0]) for r in rows]


def pickup_id_by_address(address):
    rows = db("SELECT pickup_point_id, full_address FROM pickup_points")
    for pid, addr in rows:
        if str(addr) == address:
            return pid
    return rows[0][0] if rows else 1


def date_only(value):
    text = str(value)
    return text.split(" ")[0] if " " in text else text


def draw_order_card(parent, row):
    oid, articles, status, address, odate, ddate = row[0], row[1], row[2], row[3], date_only(row[4]), date_only(row[5])
    card = tk.Frame(parent, bg=BG, bd=1, relief=tk.SOLID)
    card.pack(fill=tk.X, padx=8, pady=6)
    if role_is("Администратор"):
        card.bind("<Button-1>", lambda e, x=oid: open_order_form("edit", x))
        card.config(cursor="hand2")

    left = tk.Frame(card, bg=BG)
    left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
    tk.Label(left, text="Артикул заказа: " + str(articles), bg=BG, font=FONT_B, anchor="w").pack(anchor="w")
    tk.Label(left, text="Статус: " + str(status), bg=BG, anchor="w").pack(anchor="w")
    tk.Label(left, text="Адрес: " + str(address), bg=BG, anchor="w").pack(anchor="w")
    tk.Label(left, text="Дата заказа: " + str(odate), bg=BG, anchor="w").pack(anchor="w")

    right = tk.Frame(card, bg=BG, bd=1, relief=tk.SOLID, width=140, height=80)
    right.pack(side=tk.RIGHT, padx=10, pady=8)
    right.pack_propagate(False)
    tk.Label(right, text="Дата доставки", bg=BG, font=FONT_B).pack(pady=4)
    tk.Label(right, text=str(ddate), bg=BG).pack()


def refresh_orders_list():
    if orders_list_frame is None:
        return
    for w in orders_list_frame.winfo_children():
        w.destroy()
    try:
        rows = get_orders()
    except Exception as e:
        messagebox.showerror("Ошибка БД", str(e))
        return
    if not rows:
        tk.Label(orders_list_frame, text="Заказы не найдены", bg=BG).pack(pady=20)
        return
    for row in rows:
        draw_order_card(orders_list_frame, row)


def show_orders():
    global orders_list_frame
    if not role_is("Менеджер", "Администратор"):
        messagebox.showwarning("Доступ", "Только менеджер и администратор.")
        return
    clear()
    win.title("Список заказов - ООО «Обувь»")
    make_header("Список заказов - ООО «Обувь»", show_products)

    row_btns = tk.Frame(win, bg=BG)
    row_btns.pack(fill=tk.X, padx=12, pady=6)
    if role_is("Администратор"):
        green_btn(row_btns, "Добавить заказ", lambda: open_order_form("add", 0)).pack(side=tk.LEFT)

    orders_list_frame = make_scroll()
    refresh_orders_list()


def close_order_form():
    global order_form_open, order_fields
    if "win" in order_fields:
        try:
            order_fields["win"].destroy()
        except Exception:
            pass
    order_form_open = False
    order_fields = {}


def check_order_form():
    for key, msg in [
        ("articles", "Укажите артикул заказа."),
        ("status", "Укажите статус."),
        ("address", "Укажите адрес."),
        ("odate", "Укажите дату заказа."),
        ("ddate", "Укажите дату выдачи."),
    ]:
        w = order_fields[key]
        val = w.get().strip() if hasattr(w, "get") else ""
        if val == "":
            messagebox.showwarning("Ошибка", msg)
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
            oid = int(db("SELECT COALESCE(MAX(order_id),0) FROM orders", one=True)[0]) + 1
            client = db("SELECT full_name FROM users LIMIT 1", one=True)
            cname = client[0] if client else "Клиент"
            db("""INSERT INTO orders(order_id, order_articles, order_date, delivery_date,
                pickup_point_ref, client_full_name, pickup_code, status_name)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
               (oid, articles, odate, ddate, pickup_ref, cname, str(oid), status))
            messagebox.showinfo("Готово", "Заказ №" + str(oid))
        else:
            db("""UPDATE orders SET order_articles=%s, status_name=%s, order_date=%s,
                delivery_date=%s, pickup_point_ref=%s WHERE order_id=%s""",
               (articles, status, odate, ddate, pickup_ref, order_form_id))
            messagebox.showinfo("Готово", "Заказ сохранён.")
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))
        return
    close_order_form()
    show_orders()


def delete_order():
    if not messagebox.askyesno("Удаление", "Удалить заказ?"):
        return
    try:
        db("DELETE FROM orders WHERE order_id=%s", (order_form_id,))
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))
        return
    messagebox.showinfo("Готово", "Заказ удалён.")
    close_order_form()
    show_orders()


def open_order_form(mode, order_id):
    global order_form_open, order_form_mode, order_form_id, order_fields
    if not role_is("Администратор"):
        messagebox.showwarning("Доступ", "Только администратор.")
        return
    if order_form_open:
        messagebox.showwarning("Внимание", "Форма заказа уже открыта.")
        return
    order_form_open = True
    order_form_mode = mode
    order_form_id = order_id
    order_fields = {}

    fw = tk.Toplevel(win)
    order_fields["win"] = fw
    fw.title("Добавление заказа" if mode == "add" else "Редактирование заказа")
    fw.geometry("620x420")
    fw.configure(bg=BG)
    fw.protocol("WM_DELETE_WINDOW", close_order_form)

    plain_btn(fw, "Назад", close_order_form).pack(anchor="w", padx=10, pady=8)
    fr = tk.Frame(fw, bg=BG)
    fr.pack(padx=12, pady=8)

    statuses = get_status_list()
    addresses = get_pickup_addresses()
    start = 0

    if mode == "edit":
        row = db("""
            SELECT o.order_id, o.order_articles, o.status_name,
                   COALESCE(p.full_address,''), o.order_date, o.delivery_date
            FROM orders o
            LEFT JOIN pickup_points p ON p.pickup_point_id = o.pickup_point_ref
            WHERE o.order_id=%s""", (order_id,), one=True)
        if not row:
            messagebox.showerror("Ошибка", "Заказ не найден.")
            close_order_form()
            return
        def_art, def_st = row[1], str(row[2]).strip()
        def_addr, def_od, def_dd = row[3], date_only(row[4]), date_only(row[5])
        e = tk.Entry(fr, width=40, state="readonly")
        e.insert(0, str(row[0]))
        e.grid(row=0, column=1, pady=3)
        tk.Label(fr, text="Номер:", bg=BG).grid(row=0, column=0, sticky="w")
        start = 1
    else:
        def_art = ""
        def_st = statuses[0] if statuses else "Новый"
        def_addr = addresses[0] if addresses else ""
        def_od, def_dd = "", ""

    def add_order_field(r, label, key, val, combo=None):
        tk.Label(fr, text=label, bg=BG).grid(row=r, column=0, sticky="w", pady=3)
        if combo is not None:
            w = ttk.Combobox(fr, values=combo, width=37)
            w.set(val)
        else:
            w = tk.Entry(fr, width=40)
            w.insert(0, val)
        w.grid(row=r, column=1, pady=3)
        order_fields[key] = w

    add_order_field(start, "Артикул заказа:", "articles", def_art)
    add_order_field(start + 1, "Статус:", "status", def_st, statuses)
    add_order_field(start + 2, "Адрес:", "address", def_addr, addresses)
    add_order_field(start + 3, "Дата заказа:", "odate", def_od)
    add_order_field(start + 4, "Дата выдачи:", "ddate", def_dd)

    btns = tk.Frame(fw, bg=BG)
    btns.pack(pady=10)
    green_btn(btns, "Сохранить", save_order).pack(side=tk.LEFT, padx=6)
    if mode == "edit":
        plain_btn(btns, "Удалить", delete_order).pack(side=tk.LEFT, padx=6)


# ========== ВХОД (МОДУЛЬ 2) ==========

def show_login():
    global user, login_box, pass_box
    user = None
    close_form()
    close_order_form()
    clear()
    win.title("Авторизация - ООО «Обувь»")
    f = tk.Frame(win, bg=BG)
    f.pack(expand=True)
    lg = load_logo()
    if lg:
        lb = tk.Label(f, image=lg, bg=BG)
        lb.image = lg
        lb.pack(pady=10)
    tk.Label(f, text="Вход - ООО «Обувь»", bg=BG, font=FONT_H).pack(pady=8)
    tk.Label(f, text="Логин:", bg=BG).pack()
    login_box = tk.Entry(f, width=40)
    login_box.pack(pady=4)
    tk.Label(f, text="Пароль:", bg=BG).pack()
    pass_box = tk.Entry(f, width=40, show="*")
    pass_box.pack(pady=4)
    green_btn(f, "Войти", do_login).pack(pady=8)
    green_btn(f, "Войти как гость", do_guest).pack(pady=4)


def do_login():
    global user
    login = login_box.get().strip()
    pwd = pass_box.get().strip()
    if login == "" or pwd == "":
        messagebox.showwarning("Ошибка", "Введите логин и пароль.")
        return
    try:
        row = db("SELECT full_name, role_name FROM users WHERE login=%s AND password_plain=%s",
                 (login, pwd), one=True)
    except Exception as e:
        messagebox.showerror("Ошибка БД", str(e))
        return
    if not row:
        messagebox.showerror("Ошибка", "Неверный логин или пароль.")
        return
    user = {"name": row[0], "role": row[1], "guest": False}
    show_products()


def do_guest():
    global user
    user = {"name": "Гость", "role": "Гость", "guest": True}
    show_products()


def main():
    global win
    win = tk.Tk()
    win.geometry("1100x750")
    win.configure(bg=BG)
    win.option_add("*Font", FONT)
    ttk.Style().configure("TCombobox", font=FONT)
    if os.path.isfile(ICON):
        try:
            win.iconbitmap(ICON)
        except Exception:
            pass
    show_login()
    win.mainloop()


if __name__ == "__main__":
    main()
