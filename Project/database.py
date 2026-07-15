import sqlite3
from datetime import datetime

import auth

DB_NAME = "food_ordering.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('customer','vendor')),
            full_name TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            available INTEGER DEFAULT 1,
            FOREIGN KEY(vendor_id) REFERENCES users(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES users(id),
            FOREIGN KEY(menu_item_id) REFERENCES menu_items(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            status TEXT DEFAULT 'Pending',
            total REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES users(id),
            FOREIGN KEY(vendor_id) REFERENCES users(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------- USERS ----------------

def create_user(username, password, role, full_name):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            (username, auth.hash_password(password), role, full_name),
        )
        conn.commit()
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    finally:
        conn.close()


def authenticate_user(username, password):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if row and auth.verify_password(password, row["password_hash"]):
        return dict(row)
    return None


def get_vendors():
    conn = get_connection()
    rows = conn.execute("SELECT id, full_name, username FROM users WHERE role = 'vendor'").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------- MENU ----------------

def add_menu_item(vendor_id, name, price, description):
    conn = get_connection()
    conn.execute(
        "INSERT INTO menu_items (vendor_id, name, price, description) VALUES (?, ?, ?, ?)",
        (vendor_id, name, price, description),
    )
    conn.commit()
    conn.close()


def update_menu_item(item_id, name, price, description, available):
    conn = get_connection()
    conn.execute(
        "UPDATE menu_items SET name=?, price=?, description=?, available=? WHERE id=?",
        (name, price, description, int(available), item_id),
    )
    conn.commit()
    conn.close()


def delete_menu_item(item_id):
    conn = get_connection()
    conn.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def get_menu_items(vendor_id=None, available_only=True):
    conn = get_connection()
    query = """
        SELECT m.*, u.full_name AS vendor_name
        FROM menu_items m JOIN users u ON m.vendor_id = u.id
        WHERE 1=1
    """
    params = []
    if vendor_id is not None:
        query += " AND m.vendor_id = ?"
        params.append(vendor_id)
    if available_only:
        query += " AND m.available = 1"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------- CART ----------------

def add_to_cart(customer_id, menu_item_id, quantity):
    conn = get_connection()
    existing = conn.execute(
        "SELECT id, quantity FROM cart WHERE customer_id=? AND menu_item_id=?",
        (customer_id, menu_item_id),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE cart SET quantity = quantity + ? WHERE id = ?",
            (quantity, existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO cart (customer_id, menu_item_id, quantity) VALUES (?, ?, ?)",
            (customer_id, menu_item_id, quantity),
        )
    conn.commit()
    conn.close()


def get_cart(customer_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.id AS cart_id, c.quantity, m.id AS menu_item_id, m.name,
               m.price, m.vendor_id, u.full_name AS vendor_name,
               (c.quantity * m.price) AS subtotal
        FROM cart c
        JOIN menu_items m ON c.menu_item_id = m.id
        JOIN users u ON m.vendor_id = u.id
        WHERE c.customer_id = ?
    """, (customer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_cart_quantity(cart_id, quantity):
    conn = get_connection()
    if quantity <= 0:
        conn.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
    else:
        conn.execute("UPDATE cart SET quantity = ? WHERE id = ?", (quantity, cart_id))
    conn.commit()
    conn.close()


def remove_from_cart(cart_id):
    conn = get_connection()
    conn.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
    conn.commit()
    conn.close()


def clear_cart(customer_id):
    conn = get_connection()
    conn.execute("DELETE FROM cart WHERE customer_id = ?", (customer_id,))
    conn.commit()
    conn.close()


# ---------------- ORDERS ----------------

def place_order(customer_id):
    """Groups the customer's cart by vendor and creates one order per vendor."""
    cart_items = get_cart(customer_id)
    if not cart_items:
        return [], "Cart is empty."

    by_vendor = {}
    for item in cart_items:
        by_vendor.setdefault(item["vendor_id"], []).append(item)

    conn = get_connection()
    order_ids = []
    for vendor_id, items in by_vendor.items():
        total = sum(i["subtotal"] for i in items)
        cur = conn.execute(
            "INSERT INTO orders (customer_id, vendor_id, status, total, created_at) VALUES (?, ?, 'Pending', ?, ?)",
            (customer_id, vendor_id, total, datetime.now().isoformat(timespec="seconds")),
        )
        order_id = cur.lastrowid
        order_ids.append(order_id)
        for i in items:
            conn.execute(
                "INSERT INTO order_items (order_id, menu_item_id, item_name, quantity, price) VALUES (?, ?, ?, ?, ?)",
                (order_id, i["menu_item_id"], i["name"], i["quantity"], i["price"]),
            )
    conn.commit()
    conn.close()
    clear_cart(customer_id)
    return order_ids, "Order placed successfully."


def get_orders_for_customer(customer_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT o.*, u.full_name AS vendor_name
        FROM orders o JOIN users u ON o.vendor_id = u.id
        WHERE o.customer_id = ?
        ORDER BY o.created_at DESC
    """, (customer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_orders_for_vendor(vendor_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT o.*, u.full_name AS customer_name, u.username AS customer_username
        FROM orders o JOIN users u ON o.customer_id = u.id
        WHERE o.vendor_id = ?
        ORDER BY o.created_at DESC
    """, (vendor_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_order_items(order_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_order_status(order_id, status):
    conn = get_connection()
    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()


# ---------------- ANALYTICS ----------------

def get_sales_by_day(vendor_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT substr(created_at, 1, 10) AS day, SUM(total) AS revenue
        FROM orders
        WHERE vendor_id = ?
        GROUP BY day
        ORDER BY day
    """, (vendor_id,)).fetchall()
    conn.close()
    return [(r["day"], r["revenue"]) for r in rows]

def get_revenue_by_item(vendor_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT oi.item_name, SUM(oi.quantity * oi.price) AS revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.vendor_id = ?
        GROUP BY oi.item_name
        ORDER BY revenue DESC
    """, (vendor_id,)).fetchall()
    conn.close()
    return [(r["item_name"], r["revenue"]) for r in rows]


def get_top_items(vendor_id, limit=5):
    conn = get_connection()
    rows = conn.execute("""
        SELECT oi.item_name, SUM(oi.quantity) AS total_qty
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.vendor_id = ?
        GROUP BY oi.item_name
        ORDER BY total_qty DESC
        LIMIT ?
    """, (vendor_id, limit)).fetchall()
    conn.close()
    return [(r["item_name"], r["total_qty"]) for r in rows]