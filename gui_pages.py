import tkinter as tk

class LoginScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller=controller
        tk.Label(self, text="Login Portal Layout Base", font=("Arial", 16)).pack(pady=20)

class CustomerDashboard(tk.Frame):
    def __init__(self, parent, controller, user_data):
        super().__init__(parent)
        self.controller=controller
        tk.Label(self, text=f"Welcome to your Dashboard, {user_data[1]}", font=("Arial", 16)).pack(pady=20)
