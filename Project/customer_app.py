import tkinter as tk
from tkinter import ttk, messagebox

import database as db


class CustomerApp(tk.Toplevel):
    def __init__(self, master, user, on_logout):
        super().__init__(master)
        self.user = user
        self.on_logout = on_logout
        self.title(f"Customer Dashboard - {user['full_name']}")
        self.geometry("950x600")
        self.protocol("WM_DELETE_WINDOW", self.logout)

        self.selected_menu_item = None

        self.build_ui()
        self.refresh_menu()
        self.refresh_cart()
        self.refresh_orders()

    def build_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text=f"Welcome, {self.user['full_name']}", font=("Segoe UI", 13, "bold")).pack(side="left")
        ttk.Button(top, text="Logout", command=self.logout).pack(side="right")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.menu_tab = ttk.Frame(notebook)
        self.orders_tab = ttk.Frame(notebook)
        notebook.add(self.menu_tab, text="Menu & Cart")
        notebook.add(self.orders_tab, text="My Orders")

        self.build_menu_tab()
        self.build_orders_tab()

    # ---------- Menu & Cart tab ----------
    def build_menu_tab(self):
        left = ttk.Frame(self.menu_tab)
        left.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ttk.Label(left, text="Available Menu", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        cols = ("vendor", "name", "price", "description")
        self.menu_tree = ttk.Treeview(left, columns=cols, show="headings", height=18)
        for c, w in zip(cols, (140, 150, 70, 250)):
            self.menu_tree.heading(c, text=c.capitalize())
            self.menu_tree.column(c, width=w)
        self.menu_tree.pack(fill="both", expand=True)

        qty_frame = ttk.Frame(left)
        qty_frame.pack(fill="x", pady=5)
        ttk.Label(qty_frame, text="Quantity:").pack(side="left")
        self.qty_var = tk.IntVar(value=1)
        ttk.Spinbox(qty_frame, from_=1, to=50, textvariable=self.qty_var, width=5).pack(side="left", padx=5)
        ttk.Button(qty_frame, text="Add to Cart", command=self.add_to_cart).pack(side="left", padx=5)
        ttk.Button(qty_frame, text="Refresh Menu", command=self.refresh_menu).pack(side="left")

        right = ttk.Frame(self.menu_tab)
        right.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        ttk.Label(right, text="Your Cart", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        cart_cols = ("item", "vendor", "qty", "subtotal")
        self.cart_tree = ttk.Treeview(right, columns=cart_cols, show="headings", height=14)
        for c, w in zip(cart_cols, (150, 130, 60, 90)):
            self.cart_tree.heading(c, text=c.capitalize())
            self.cart_tree.column(c, width=w)
        self.cart_tree.pack(fill="both", expand=True)

        cart_btns = ttk.Frame(right)
        cart_btns.pack(fill="x", pady=5)
        ttk.Button(cart_btns, text="Remove Selected", command=self.remove_selected_cart_item).pack(side="left", padx=3)
        ttk.Button(cart_btns, text="Place Order", command=self.place_order).pack(side="left", padx=3)

        self.total_label = ttk.Label(right, text="Total: Rs. 0.00", font=("Segoe UI", 11, "bold"))
        self.total_label.pack(anchor="e", pady=5)

    def refresh_menu(self):
        for row in self.menu_tree.get_children():
            self.menu_tree.delete(row)
        self.menu_items_cache = db.get_menu_items(available_only=True)
        for item in self.menu_items_cache:
            self.menu_tree.insert(
                "", "end", iid=item["id"],
                values=(item["vendor_name"], item["name"], f"{item['price']:.2f}", item["description"] or "")
            )

    def add_to_cart(self):
        selected = self.menu_tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a menu item first.")
            return
        item_id = int(selected[0])
        qty = self.qty_var.get()
        if qty <= 0:
            messagebox.showwarning("Invalid quantity", "Quantity must be at least 1.")
            return
        db.add_to_cart(self.user["id"], item_id, qty)
        self.refresh_cart()
        messagebox.showinfo("Added", "Item added to cart.")

    def refresh_cart(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)
        cart_items = db.get_cart(self.user["id"])
        total = 0.0
        for c in cart_items:
            self.cart_tree.insert(
                "", "end", iid=c["cart_id"],
                values=(c["name"], c["vendor_name"], c["quantity"], f"{c['subtotal']:.2f}")
            )
            total += c["subtotal"]
        self.total_label.config(text=f"Total: Rs. {total:.2f}")

    def remove_selected_cart_item(self):
        selected = self.cart_tree.selection()
        if not selected:
            return
        db.remove_from_cart(int(selected[0]))
        self.refresh_cart()

    def place_order(self):
        order_ids, message = db.place_order(self.user["id"])
        if order_ids:
            messagebox.showinfo("Order placed", message)
            self.refresh_cart()
            self.refresh_orders()
        else:
            messagebox.showwarning("Cannot place order", message)

    # ---------- My Orders tab ----------
    def build_orders_tab(self):
        left = ttk.Frame(self.orders_tab)
        left.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ttk.Label(left, text="Your Orders", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        cols = ("id", "vendor", "status", "total", "created_at")
        self.orders_tree = ttk.Treeview(left, columns=cols, show="headings", height=18)
        for c, w in zip(cols, (40, 130, 90, 80, 150)):
            self.orders_tree.heading(c, text=c.capitalize())
            self.orders_tree.column(c, width=w)
        self.orders_tree.pack(fill="both", expand=True)
        self.orders_tree.bind("<<TreeviewSelect>>", lambda e: self.show_order_items())
        ttk.Button(left, text="Refresh", command=self.refresh_orders).pack(anchor="w", pady=5)

        right = ttk.Frame(self.orders_tab)
        right.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        ttk.Label(right, text="Order Details", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        detail_cols = ("item", "qty", "price")
        self.order_items_tree = ttk.Treeview(right, columns=detail_cols, show="headings", height=18)
        for c, w in zip(detail_cols, (200, 60, 80)):
            self.order_items_tree.heading(c, text=c.capitalize())
            self.order_items_tree.column(c, width=w)
        self.order_items_tree.pack(fill="both", expand=True)

    def refresh_orders(self):
        for row in self.orders_tree.get_children():
            self.orders_tree.delete(row)
        for o in db.get_orders_for_customer(self.user["id"]):
            self.orders_tree.insert(
                "", "end", iid=o["id"],
                values=(o["id"], o["vendor_name"], o["status"], f"{o['total']:.2f}", o["created_at"])
            )

    def show_order_items(self):
        selected = self.orders_tree.selection()
        for row in self.order_items_tree.get_children():
            self.order_items_tree.delete(row)
        if not selected:
            return
        order_id = int(selected[0])
        for item in db.get_order_items(order_id):
            self.order_items_tree.insert(
                "", "end", values=(item["item_name"], item["quantity"], f"{item['price']:.2f}")
            )

    def logout(self):
        self.destroy()
        self.on_logout()