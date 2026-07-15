import tkinter as tk
from tkinter import ttk, messagebox

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import database as db


class VendorApp(tk.Toplevel):
    def __init__(self, master, user, on_logout):
        super().__init__(master)
        self.user = user
        self.on_logout = on_logout
        self.title(f"Vendor Dashboard - {user['full_name']}")
        self.geometry("1000x650")
        self.protocol("WM_DELETE_WINDOW", self.logout)

        self.build_ui()
        self.refresh_orders()
        self.refresh_menu_items()
        self.refresh_chart()

    def build_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text=f"Welcome, {self.user['full_name']}", font=("Segoe UI", 13, "bold")).pack(side="left")
        ttk.Button(top, text="Logout", command=self.logout).pack(side="right")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.orders_tab = ttk.Frame(notebook)
        self.menu_tab = ttk.Frame(notebook)
        self.analytics_tab = ttk.Frame(notebook)
        notebook.add(self.orders_tab, text="Incoming Orders")
        notebook.add(self.menu_tab, text="Menu Management")
        notebook.add(self.analytics_tab, text="Sales Analytics")

        self.build_orders_tab()
        self.build_menu_tab()
        self.build_analytics_tab()

    # ---------- Incoming Orders ----------
    def build_orders_tab(self):
        left = ttk.Frame(self.orders_tab)
        left.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ttk.Label(left, text="Incoming Orders", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        cols = ("id", "customer", "status", "total", "created_at")
        self.orders_tree = ttk.Treeview(left, columns=cols, show="headings", height=20)
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
        self.order_items_tree = ttk.Treeview(right, columns=detail_cols, show="headings", height=14)
        for c, w in zip(detail_cols, (200, 60, 80)):
            self.order_items_tree.heading(c, text=c.capitalize())
            self.order_items_tree.column(c, width=w)
        self.order_items_tree.pack(fill="both", expand=True)

        status_frame = ttk.Frame(right)
        status_frame.pack(fill="x", pady=10)
        ttk.Label(status_frame, text="Update Status:").pack(side="left")
        self.status_var = tk.StringVar(value="Pending")
        ttk.Combobox(
            status_frame, textvariable=self.status_var,
            values=["Pending", "Preparing", "Out for Delivery", "Completed", "Cancelled"],
            state="readonly", width=18
        ).pack(side="left", padx=5)
        ttk.Button(status_frame, text="Update", command=self.update_status).pack(side="left")

    def refresh_orders(self):
        for row in self.orders_tree.get_children():
            self.orders_tree.delete(row)
        for o in db.get_orders_for_vendor(self.user["id"]):
            self.orders_tree.insert(
                "", "end", iid=o["id"],
                values=(o["id"], o["customer_name"], o["status"], f"{o['total']:.2f}", o["created_at"])
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
        current_status = self.orders_tree.item(selected[0], "values")[2]
        self.status_var.set(current_status)

    def update_status(self):
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select an order first.")
            return
        order_id = int(selected[0])
        db.update_order_status(order_id, self.status_var.get())
        self.refresh_orders()
        self.refresh_chart()
        messagebox.showinfo("Updated", "Order status updated.")

    # ---------- Menu Management ----------
    def build_menu_tab(self):
        left = ttk.Frame(self.menu_tab)
        left.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ttk.Label(left, text="Your Menu Items", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        cols = ("id", "name", "price", "description", "available")
        self.items_tree = ttk.Treeview(left, columns=cols, show="headings", height=18)
        for c, w in zip(cols, (40, 140, 70, 220, 70)):
            self.items_tree.heading(c, text=c.capitalize())
            self.items_tree.column(c, width=w)
        self.items_tree.pack(fill="both", expand=True)
        self.items_tree.bind("<<TreeviewSelect>>", lambda e: self.load_selected_item())

        right = ttk.Frame(self.menu_tab)
        right.pack(side="right", fill="both", padx=5, pady=5)

        ttk.Label(right, text="Add / Edit Item", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(right, text="Name:").grid(row=1, column=0, sticky="w", pady=3)
        self.name_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.name_var, width=25).grid(row=1, column=1, pady=3)

        ttk.Label(right, text="Price:").grid(row=2, column=0, sticky="w", pady=3)
        self.price_var = tk.DoubleVar(value=0.0)
        ttk.Entry(right, textvariable=self.price_var, width=25).grid(row=2, column=1, pady=3)

        ttk.Label(right, text="Description:").grid(row=3, column=0, sticky="nw", pady=3)
        self.desc_text = tk.Text(right, width=25, height=4)
        self.desc_text.grid(row=3, column=1, pady=3)

        self.available_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(right, text="Available", variable=self.available_var).grid(row=4, column=1, sticky="w", pady=3)

        btn_frame = ttk.Frame(right)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Add New", command=self.add_item).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="Update Selected", command=self.update_item).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_item).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_form).pack(side="left", padx=3)

        self.selected_item_id = None

    def refresh_menu_items(self):
        for row in self.items_tree.get_children():
            self.items_tree.delete(row)
        for item in db.get_menu_items(vendor_id=self.user["id"], available_only=False):
            self.items_tree.insert(
                "", "end", iid=item["id"],
                values=(item["id"], item["name"], f"{item['price']:.2f}",
                        item["description"] or "", "Yes" if item["available"] else "No")
            )

    def load_selected_item(self):
        selected = self.items_tree.selection()
        if not selected:
            return
        item_id = int(selected[0])
        items = db.get_menu_items(vendor_id=self.user["id"], available_only=False)
        item = next((i for i in items if i["id"] == item_id), None)
        if not item:
            return
        self.selected_item_id = item_id
        self.name_var.set(item["name"])
        self.price_var.set(item["price"])
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", item["description"] or "")
        self.available_var.set(bool(item["available"]))

    def add_item(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing name", "Item name is required.")
            return
        try:
            price = float(self.price_var.get())
        except (tk.TclError, ValueError):
            messagebox.showwarning("Invalid price", "Enter a valid price.")
            return
        description = self.desc_text.get("1.0", "end").strip()
        db.add_menu_item(self.user["id"], name, price, description)
        self.refresh_menu_items()
        self.clear_form()

    def update_item(self):
        if not self.selected_item_id:
            messagebox.showwarning("No selection", "Select an item to update.")
            return
        name = self.name_var.get().strip()
        try:
            price = float(self.price_var.get())
        except (tk.TclError, ValueError):
            messagebox.showwarning("Invalid price", "Enter a valid price.")
            return
        description = self.desc_text.get("1.0", "end").strip()
        db.update_menu_item(self.selected_item_id, name, price, description, self.available_var.get())
        self.refresh_menu_items()
        self.clear_form()

    def delete_item(self):
        if not self.selected_item_id:
            messagebox.showwarning("No selection", "Select an item to delete.")
            return
        if messagebox.askyesno("Confirm", "Delete this item?"):
            db.delete_menu_item(self.selected_item_id)
            self.refresh_menu_items()
            self.clear_form()

    def clear_form(self):
        self.selected_item_id = None
        self.name_var.set("")
        self.price_var.set(0.0)
        self.desc_text.delete("1.0", "end")
        self.available_var.set(True)

    # ---------- Sales Analytics ----------
    def build_analytics_tab(self):
        ttk.Button(self.analytics_tab, text="Refresh Chart", command=self.refresh_chart).pack(anchor="w", padx=5, pady=5)
        self.chart_container = ttk.Frame(self.analytics_tab)
        self.chart_container.pack(fill="both", expand=True, padx=5, pady=5)
        self.canvas = None

    def refresh_chart(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        data = db.get_revenue_by_item(self.user["id"])
        fig = Figure(figsize=(8, 5), dpi=100)
        ax = fig.add_subplot(111)

        if data:
            items = [name for name, _ in data]
            revenue = [rev for _, rev in data]
            ax.bar(items, revenue, color="#4c72b0")
            ax.set_title("Revenue by Item")
            ax.set_xlabel("Item")
            ax.set_ylabel("Revenue (Rs.)")
            fig.autofmt_xdate(rotation=45)
        else:
            ax.text(0.5, 0.5, "No sales data yet", ha="center", va="center")
            ax.set_axis_off()

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
    def logout(self):
        self.destroy()
        self.on_logout()