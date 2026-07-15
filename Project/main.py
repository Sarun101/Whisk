import tkinter as tk
from tkinter import ttk, messagebox

import database as db
from customer_app import CustomerApp
from vendor_app import VendorApp


class LoginApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Food Ordering System - Login")
        self.geometry("400x600")
        self.resizable(False, False)
        self.build_login_ui()

    def build_login_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Login", font=("Segoe UI", 16, "bold")).pack(pady=10)

        ttk.Label(frame, text="Username").pack(anchor="w")
        self.username_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.username_var).pack(fill="x", pady=3)

        ttk.Label(frame, text="Password").pack(anchor="w")
        self.password_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.password_var, show="*").pack(fill="x", pady=3)

        ttk.Button(frame, text="Login", command=self.login).pack(fill="x", pady=15)
        ttk.Button(frame, text="Create an account", command=self.build_register_ui).pack(fill="x")

    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showwarning("Missing info", "Enter both username and password.")
            return

        user = db.authenticate_user(username, password)
        if not user:
            messagebox.showerror("Login failed", "Invalid username or password.")
            return

        self.withdraw()
        if user["role"] == "customer":
            CustomerApp(self, user, on_logout=self.show_login_again)
        else:
            VendorApp(self, user, on_logout=self.show_login_again)

    def show_login_again(self):
        self.username_var.set("")
        self.password_var.set("")
        self.deiconify()
        self.build_login_ui()

    def build_register_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Create Account", font=("Segoe UI", 16, "bold")).pack(pady=10)

        ttk.Label(frame, text="Full Name").pack(anchor="w")
        full_name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=full_name_var).pack(fill="x", pady=3)

        ttk.Label(frame, text="Username").pack(anchor="w")
        username_var = tk.StringVar()
        ttk.Entry(frame, textvariable=username_var).pack(fill="x", pady=3)

        ttk.Label(frame, text="Password").pack(anchor="w")
        password_var = tk.StringVar()
        ttk.Entry(frame, textvariable=password_var, show="*").pack(fill="x", pady=3)

        ttk.Label(frame, text="Role").pack(anchor="w")
        role_var = tk.StringVar(value="customer")
        role_box = ttk.Combobox(frame, textvariable=role_var, values=["customer", "vendor"], state="readonly")
        role_box.pack(fill="x", pady=3)

        def register():
            full_name = full_name_var.get().strip()
            username = username_var.get().strip()
            password = password_var.get()
            role = role_var.get()

            if not (full_name and username and password and role):
                messagebox.showwarning("Missing info", "Please fill in all fields.")
                return

            success, message = db.create_user(username, password, role, full_name)
            if success:
                user = db.authenticate_user(username, password)
                self.withdraw()
                if user["role"] == "customer":
                    CustomerApp(self, user, on_logout=self.show_login_again)
                else:
                    VendorApp(self, user, on_logout=self.show_login_again)
            else:
                messagebox.showerror("Error", message)

        ttk.Button(frame, text="Register", command=register).pack(fill="x", pady=15)
        ttk.Button(frame, text="Back to Login", command=self.build_login_ui).pack(fill="x")


if __name__ == "__main__":
    db.init_db()
    app = LoginApp()
    app.mainloop()