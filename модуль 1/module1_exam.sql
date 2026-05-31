-- =============================================================================
-- МОДУЛЬ 1 — БД «ООО Обувь»
-- Файл: module1_exam.sql
--
-- ПОРЯДОК:
--   1) ЧАСТЬ 1 — выполнить в Query Tool (создание таблиц)
--   2) Импорт 4 CSV через pgAdmin (см. инструкцию txt)
--   3) ЧАСТЬ 2 — выполнить в Query Tool (связи ID + состав заказов)
--   4) ЧАСТЬ 3 — выполнить в Query Tool (внешние ключи FK)
--   5) ЧАСТЬ 4 — проверка
--   6) ERD Tool → PDF
-- =============================================================================


-- =============================================================================
-- ЧАСТЬ 1. СОЗДАНИЕ ТАБЛИЦ (ДО импорта CSV)
-- Подключись к базе shoe_store_demo → Query Tool → Execute
-- =============================================================================

DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS pickup_points CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS order_statuses CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- Справочник ролей (3НФ)
CREATE TABLE roles (
    id   SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Справочник статусов заказа (3НФ)
CREATE TABLE order_statuses (
    id   SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Пользователи
CREATE TABLE users (
    user_id         SERIAL PRIMARY KEY,
    role_name       TEXT,
    full_name       TEXT,
    login           TEXT,
    password_plain  TEXT,
    role_id         INT
);

-- Товары (данные из Tovar — текстовые поля, как в CSV)
CREATE TABLE products (
    article          TEXT PRIMARY KEY,
    product_name     TEXT,
    unit_name        TEXT,
    price            TEXT,
    supplier_name    TEXT,
    manufacturer_name TEXT,
    category_name    TEXT,
    discount_percent TEXT,
    stock_qty        TEXT,
    description      TEXT,
    photo_file       TEXT
);

-- Пункты выдачи
CREATE TABLE pickup_points (
    pickup_point_id SERIAL PRIMARY KEY,
    full_address    TEXT NOT NULL
);

-- Заказы
CREATE TABLE orders (
    order_id          INT PRIMARY KEY,
    order_articles    TEXT,
    order_date        TEXT,
    delivery_date     TEXT,
    pickup_point_ref  INT,
    client_full_name  TEXT,
    pickup_code       TEXT,
    status_name       TEXT,
    client_id         INT,
    status_id         INT
);

-- Состав заказа (для модуля 3: нельзя удалить товар, если он в заказе)
CREATE TABLE order_items (
    id              SERIAL PRIMARY KEY,
    order_id        INT NOT NULL,
    product_article TEXT NOT NULL,
    qty             INT NOT NULL CHECK (qty > 0),
    UNIQUE (order_id, product_article)
);

-- Справочники — фиксированные значения (можно до импорта)
INSERT INTO roles (name) VALUES
    ('Администратор'),
    ('Менеджер'),
    ('Авторизированный клиент');

INSERT INTO order_statuses (name) VALUES
    ('Новый'),
    ('Завершен');


-- =============================================================================
-- ЧАСТЬ 2. ПОСЛЕ ИМПОРТА CSV
-- Импортировал users, products, pickup_points, orders → Execute эту часть
-- =============================================================================

-- role_id у пользователей
UPDATE users SET role_id = 1 WHERE role_name = 'Администратор';
UPDATE users SET role_id = 2 WHERE role_name = 'Менеджер';
UPDATE users SET role_id = 3 WHERE role_name = 'Авторизированный клиент';

-- status_id у заказов (TRIM — на случай пробела в «Новый »)
UPDATE orders SET status_id = 1 WHERE TRIM(status_name) = 'Новый';
UPDATE orders SET status_id = 2 WHERE TRIM(status_name) = 'Завершен';

-- client_id у заказов (по ФИО клиента)
UPDATE orders o
SET client_id = u.user_id
FROM users u
WHERE TRIM(o.client_full_name) = TRIM(u.full_name);

-- Состав заказов (из order_articles, без сложного SQL)
INSERT INTO order_items (order_id, product_article, qty) VALUES
    (1,  'А112Т4', 2), (1,  'F635R4', 2),
    (2,  'H782T5', 1), (2,  'G783F5', 1),
    (3,  'J384T6', 10), (3, 'D572U8', 10),
    (4,  'F572H7', 5), (4,  'D329H3', 4),
    (5,  'А112Т4', 2), (5,  'F635R4', 2),
    (6,  'H782T5', 1), (6,  'G783F5', 1),
    (7,  'J384T6', 10), (7, 'D572U8', 10),
    (8,  'F572H7', 5), (8,  'D329H3', 4),
    (9,  'B320R5', 5), (9,  'G432E4', 1),
    (10, 'S213E3', 5), (10, 'E482R4', 5);


-- =============================================================================
-- ЧАСТЬ 3. ВНЕШНИЕ КЛЮЧИ (FK) — только ПОСЛЕ части 2
-- Если ошибка FK — сначала выполни проверки из части 4 (bad_*)
-- =============================================================================

ALTER TABLE users
    ADD CONSTRAINT fk_users_role
    FOREIGN KEY (role_id) REFERENCES roles (id);

ALTER TABLE orders
    ADD CONSTRAINT fk_orders_client
    FOREIGN KEY (client_id) REFERENCES users (user_id);

ALTER TABLE orders
    ADD CONSTRAINT fk_orders_status
    FOREIGN KEY (status_id) REFERENCES order_statuses (id);

ALTER TABLE orders
    ADD CONSTRAINT fk_orders_pickup
    FOREIGN KEY (pickup_point_ref) REFERENCES pickup_points (pickup_point_id);

ALTER TABLE order_items
    ADD CONSTRAINT fk_order_items_order
    FOREIGN KEY (order_id) REFERENCES orders (order_id) ON DELETE CASCADE;

ALTER TABLE order_items
    ADD CONSTRAINT fk_order_items_product
    FOREIGN KEY (product_article) REFERENCES products (article);


-- =============================================================================
-- ЧАСТЬ 4. ПРОВЕРКА (показать комиссии)
-- =============================================================================

SELECT COUNT(*) AS users_cnt         FROM users;
SELECT COUNT(*) AS products_cnt      FROM products;
SELECT COUNT(*) AS pickup_points_cnt FROM pickup_points;
SELECT COUNT(*) AS orders_cnt        FROM orders;
SELECT COUNT(*) AS order_items_cnt   FROM order_items;

-- Должно быть 0 в каждой строке:
SELECT COUNT(*) AS bad_users   FROM users  WHERE role_id IS NULL;
SELECT COUNT(*) AS bad_orders  FROM orders WHERE client_id IS NULL OR status_id IS NULL;

-- Пример связей:
SELECT o.order_id, u.full_name, s.name AS status, p.full_address
FROM orders o
JOIN users u ON u.user_id = o.client_id
JOIN order_statuses s ON s.id = o.status_id
JOIN pickup_points p ON p.pickup_point_id = o.pickup_point_ref
ORDER BY o.order_id
LIMIT 5;
