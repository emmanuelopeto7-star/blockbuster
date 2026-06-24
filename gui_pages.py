import tkinter as tk

from actions import authenticate_user

class LoginScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller=controller

        tk.Label(self, text="Blockbuster Login", font=("Arial", 16)).pack(pady=20)

        tk.Label(self, text="Email:").pack()
        self.email_entry = tk.Entry(self, width=30)
        self.email_entry.pack(pady=5)
        self.email_entry.bind("<Return>", lambda event: self.attempt_login())
        self.email_entry.focus_set()

        self.error_label = tk.Label(self, text="", fg="red")
        self.error_label.pack(pady=5)

        tk.Button(self, text="Login", command=self.attempt_login).pack(pady=10)

    def attempt_login(self):
        email = self.email_entry.get().strip()
        if not email:
            self.error_label.config(text="Please enter an email.")
            return

        success, message, user_data = authenticate_user(email)
        if not success:
            self.error_label.config(text=message)
            return

        role = user_data[4]
        dashboards = {
            "Customer": CustomerDashboard,
            "Clerk": ClerkDashboard,
            "Admin": AdminDashboard,
        }
        dashboard_class = dashboards.get(role)
        if not dashboard_class:
            self.error_label.config(text=f"Unknown role: {role}")
            return

        self.controller.switch_frame(dashboard_class, self.controller, user_data)

class CustomerDashboard(tk.Frame):
    def __init__(self, parent, controller, user_data):
        super().__init__(parent)
        self.controller=controller
        tk.Label(self, text=f"Welcome to your Dashboard, {user_data[1]}", font=("Arial", 16)).pack(pady=20)

class ClerkDashboard(tk.Frame):
    def __init__(self, parent, controller, user_data):
        super().__init__(parent)
        self.controller=controller
        tk.Label(self, text="Store Clerk Operational Command Console", font=("Arial", 16)).pack(pady=20)

class AdminDashboard(tk.Frame):
    def __init__(self, parent, controller, user_data):
        super().__init__(parent)
        self.controller=controller
        tk.Label(self, text="Main Admin Master Analytics Panel", font=("Arial", 16)).pack(pady=20)



