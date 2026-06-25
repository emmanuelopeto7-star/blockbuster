import tkinter as tk
from tkinter import ttk

from actions import (
    authenticate_user,
    get_available_inventory,
    add_inventory_item,
    request_rental,
    get_rental_history,
    get_pending_rentals,
    approve_rental,
    deny_rental,
    get_active_rentals,
    process_return,
    get_all_rentals,
)

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
        self.member_number = user_data[0]

        header = tk.Frame(self)
        header.pack(fill="x", pady=10)
        tk.Label(header, text=f"Welcome to your Dashboard, {user_data[1]}", font=("Arial", 16)).pack(side="left", padx=20)
        tk.Button(header, text="Logout", command=lambda: self.controller.switch_frame(LoginScreen, self.controller)).pack(side="right", padx=20)

        self.status_label = tk.Label(self, text="")
        self.status_label.pack()

        inventory_frame = tk.LabelFrame(self, text="Available Items")
        inventory_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.inventory_tree = ttk.Treeview(
            inventory_frame, columns=("title", "type", "available"), show="headings", height=6
        )
        self.inventory_tree.heading("title", text="Title")
        self.inventory_tree.heading("type", text="Type")
        self.inventory_tree.heading("available", text="Available Copies")
        self.inventory_tree.pack(fill="both", expand=True, side="top")
        tk.Button(inventory_frame, text="Rent Selected", command=self.rent_selected).pack(pady=5)

        history_frame = tk.LabelFrame(self, text="My Rental & Return History")
        history_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=("title", "rented", "due", "returned", "status"),
            show="headings",
            height=6,
        )
        for col, label in [
            ("title", "Title"), ("rented", "Rented On"), ("due", "Due Date"),
            ("returned", "Returned On"), ("status", "Status"),
        ]:
            self.history_tree.heading(col, text=label)
        self.history_tree.pack(fill="both", expand=True)

        self.refresh()

    def refresh(self):
        for row in self.inventory_tree.get_children():
            self.inventory_tree.delete(row)
        for item_id, title, item_type, available in get_available_inventory():
            self.inventory_tree.insert("", "end", iid=str(item_id), values=(title, item_type, available))

        for row in self.history_tree.get_children():
            self.history_tree.delete(row)
        for rental_id, title, rental_date, due_date, return_date, status in get_rental_history(self.member_number):
            self.history_tree.insert(
                "", "end", iid=str(rental_id),
                values=(title, rental_date, due_date or "-", return_date or "-", status),
            )

    def rent_selected(self):
        selected = self.inventory_tree.selection()
        if not selected:
            self.status_label.config(text="Select an item to rent.", fg="red")
            return

        item_id = int(selected[0])
        success, message = request_rental(self.member_number, item_id)
        self.status_label.config(text=message, fg="green" if success else "red")
        if success:
            self.refresh()

class ClerkDashboard(tk.Frame):
    def __init__(self, parent, controller, user_data):
        super().__init__(parent)
        self.controller=controller

        header = tk.Frame(self)
        header.pack(fill="x", pady=10)
        tk.Label(header, text="Store Clerk Operational Command Console", font=("Arial", 16)).pack(side="left", padx=20)
        tk.Button(header, text="Logout", command=lambda: self.controller.switch_frame(LoginScreen, self.controller)).pack(side="right", padx=20)

        self.status_label = tk.Label(self, text="")
        self.status_label.pack()

        pending_frame = tk.LabelFrame(self, text="Pending Rental Requests")
        pending_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.pending_tree = ttk.Treeview(
            pending_frame, columns=("customer", "title", "requested"), show="headings", height=6
        )
        self.pending_tree.heading("customer", text="Customer")
        self.pending_tree.heading("title", text="Item")
        self.pending_tree.heading("requested", text="Requested On")
        self.pending_tree.pack(fill="both", expand=True, side="top")

        pending_buttons = tk.Frame(pending_frame)
        pending_buttons.pack(pady=5)
        tk.Button(pending_buttons, text="Approve Selected", command=self.approve_selected).pack(side="left", padx=5)
        tk.Button(pending_buttons, text="Deny Selected", command=self.deny_selected).pack(side="left", padx=5)

        active_frame = tk.LabelFrame(self, text="Active Rentals (Process Return)")
        active_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.active_tree = ttk.Treeview(
            active_frame, columns=("customer", "title", "due", "status"), show="headings", height=6
        )
        for col, label in [
            ("customer", "Customer"), ("title", "Item"), ("due", "Due Date"), ("status", "Status"),
        ]:
            self.active_tree.heading(col, text=label)
        self.active_tree.pack(fill="both", expand=True, side="top")
        tk.Button(active_frame, text="Process Return", command=self.process_return_selected).pack(pady=5)

        self._active_item_ids = {}
        self._pending_item_ids = {}
        self.refresh()

    def refresh(self):
        for row in self.pending_tree.get_children():
            self.pending_tree.delete(row)
        self._pending_item_ids = {}
        for rental_id, customer, title, requested, item_id in get_pending_rentals():
            self.pending_tree.insert("", "end", iid=str(rental_id), values=(customer, title, requested))
            self._pending_item_ids[str(rental_id)] = item_id

        self._active_item_ids = {}
        for row in self.active_tree.get_children():
            self.active_tree.delete(row)
        for rental_id, customer, title, item_id, due, status in get_active_rentals():
            self.active_tree.insert("", "end", iid=str(rental_id), values=(customer, title, due, status))
            self._active_item_ids[str(rental_id)] = item_id

    def approve_selected(self):
        selected = self.pending_tree.selection()
        if not selected:
            self.status_label.config(text="Select a pending request to approve.", fg="red")
            return

        rental_id = int(selected[0])
        success, message = approve_rental(rental_id)
        self.status_label.config(text=message, fg="green" if success else "red")
        if success:
            self.refresh()

    def deny_selected(self):
        selected = self.pending_tree.selection()
        if not selected:
            self.status_label.config(text="Select a pending request to deny.", fg="red")
            return

        rental_id = int(selected[0])
        item_id = self._pending_item_ids[selected[0]]
        success, message = deny_rental(rental_id, item_id)
        self.status_label.config(text=message, fg="green" if success else "red")
        if success:
            self.refresh()

    def process_return_selected(self):
        selected = self.active_tree.selection()
        if not selected:
            self.status_label.config(text="Select a rental to process its return.", fg="red")
            return

        rental_id = int(selected[0])
        item_id = self._active_item_ids[selected[0]]
        success, message = process_return(rental_id, item_id)
        self.status_label.config(text=message, fg="green" if success else "red")
        if success:
            self.refresh()

class AdminDashboard(tk.Frame):
    def __init__(self, parent, controller, user_data):
        super().__init__(parent)
        self.controller=controller

        header = tk.Frame(self)
        header.pack(fill="x", pady=10)
        tk.Label(header, text="Main Admin Master Analytics Panel", font=("Arial", 16)).pack(side="left", padx=20)
        tk.Button(header, text="Logout", command=lambda: self.controller.switch_frame(LoginScreen, self.controller)).pack(side="right", padx=20)
        tk.Button(header, text="Refresh", command=lambda: self.refresh()).pack(side="right", padx=5)

        self.status_label = tk.Label(self, text="")
        self.status_label.pack()

        add_frame = tk.LabelFrame(self, text="Add New Movie / Equipment")
        add_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(add_frame, text="Title:").grid(row=0, column=0, padx=5, pady=8, sticky="e")
        self.new_title_entry = tk.Entry(add_frame, width=25)
        self.new_title_entry.grid(row=0, column=1, padx=5, pady=8)

        tk.Label(add_frame, text="Type:").grid(row=0, column=2, padx=5, pady=8, sticky="e")
        self.new_type_combo = ttk.Combobox(add_frame, values=["VHS", "DVD", "CD", "Equipment"], width=12)
        self.new_type_combo.set("VHS")
        self.new_type_combo.grid(row=0, column=3, padx=5, pady=8)

        tk.Label(add_frame, text="Copies:").grid(row=0, column=4, padx=5, pady=8, sticky="e")
        self.new_copies_entry = tk.Entry(add_frame, width=5)
        self.new_copies_entry.insert(0, "1")
        self.new_copies_entry.grid(row=0, column=5, padx=5, pady=8)

        tk.Button(add_frame, text="Add Item", command=self.add_item).grid(row=0, column=6, padx=10, pady=8)

        inventory_frame = tk.LabelFrame(self, text="Current Inventory")
        inventory_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.inventory_tree = ttk.Treeview(
            inventory_frame, columns=("title", "type", "available"), show="headings", height=5
        )
        self.inventory_tree.heading("title", text="Title")
        self.inventory_tree.heading("type", text="Type")
        self.inventory_tree.heading("available", text="Available Copies")
        self.inventory_tree.pack(fill="both", expand=True)

        overview_frame = tk.LabelFrame(self, text="All Rentals & Returns")
        overview_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.overview_tree = ttk.Treeview(
            overview_frame,
            columns=("customer", "title", "rented", "due", "returned", "status"),
            show="headings",
            height=6,
        )
        for col, label in [
            ("customer", "Customer"), ("title", "Item"), ("rented", "Rented On"),
            ("due", "Due Date"), ("returned", "Returned On"), ("status", "Status"),
        ]:
            self.overview_tree.heading(col, text=label)
        self.overview_tree.pack(fill="both", expand=True, side="top")
        tk.Button(overview_frame, text="Approve Selected", command=self.approve_selected).pack(pady=5)

        self.refresh()

    def refresh(self):
        for row in self.inventory_tree.get_children():
            self.inventory_tree.delete(row)
        for item_id, title, item_type, available in get_available_inventory():
            self.inventory_tree.insert("", "end", iid=str(item_id), values=(title, item_type, available))

        for row in self.overview_tree.get_children():
            self.overview_tree.delete(row)
        for rental_id, customer, title, rented, due, returned, status in get_all_rentals():
            self.overview_tree.insert(
                "", "end", iid=str(rental_id),
                values=(customer, title, rented, due or "-", returned or "-", status),
            )

    def add_item(self):
        title = self.new_title_entry.get().strip()
        item_type = self.new_type_combo.get().strip()
        copies_text = self.new_copies_entry.get().strip()

        if not title or not item_type:
            self.status_label.config(text="Title and type are required.", fg="red")
            return
        if not copies_text.isdigit():
            self.status_label.config(text="Copies must be a whole number.", fg="red")
            return

        success, message = add_inventory_item(title, item_type, int(copies_text))
        self.status_label.config(text=message, fg="green" if success else "red")
        if success:
            self.new_title_entry.delete(0, "end")
            self.new_copies_entry.delete(0, "end")
            self.new_copies_entry.insert(0, "1")
            self.refresh()

    def approve_selected(self):
        selected = self.overview_tree.selection()
        if not selected:
            self.status_label.config(text="Select a pending request to approve.", fg="red")
            return

        rental_id = int(selected[0])
        success, message = approve_rental(rental_id)
        self.status_label.config(text=message, fg="green" if success else "red")
        if success:
            self.refresh()



