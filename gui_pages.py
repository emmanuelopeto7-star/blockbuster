from tkinter import ttk

import customtkinter as ctk

from actions import (
    authenticate_user,
    get_available_inventory,
    add_inventory_item,
    add_member,
    set_member_password,
    request_rental,
    get_rental_history,
    get_pending_rentals,
    approve_rental,
    deny_rental,
    get_active_rentals,
    process_return,
    get_all_rentals,
)


def configure_treeview_style():
    """Restyles ttk.Treeview (no CTk equivalent) to match the CustomTkinter dark theme."""
    style = ttk.Style()
    style.theme_use("default")
    style.configure(
        "Treeview",
        background="#2a2d2e",
        foreground="white",
        fieldbackground="#2a2d2e",
        bordercolor="#2a2d2e",
        borderwidth=0,
        rowheight=26,
    )
    style.map("Treeview", background=[("selected", "#1f6aa5")])
    style.configure(
        "Treeview.Heading",
        background="#1f1f1f",
        foreground="white",
        relief="flat",
        borderwidth=0,
    )
    style.map("Treeview.Heading", background=[("active", "#1f1f1f")])


def create_section(parent, title, fill="x", expand=False):
    """Builds a titled CTkFrame section to stand in for tkinter's LabelFrame and returns its content area."""
    section = ctk.CTkFrame(parent)
    section.pack(fill=fill, expand=expand, padx=20, pady=10)
    ctk.CTkLabel(section, text=title, font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 0))
    content = ctk.CTkFrame(section, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=10, pady=(4, 10))
    return content


class LoginScreen(ctk.CTkFrame):
    """First screen shown on launch. Authenticates the user and routes them
    to the dashboard that matches their role (Customer/Clerk/Admin)."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ctk.CTkLabel(self, text="Blockbuster Login", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 5))

        ctk.CTkLabel(
            self,
            text=(
                "Every title on our shelves is offered strictly as a rental,\n"
                "kept in circulation to help preserve the heritage of physical media."
            ),
            font=ctk.CTkFont(size=12),
            text_color="gray70",
            justify="center",
        ).pack(pady=(0, 15))

        ctk.CTkLabel(self, text="Email:").pack()
        self.email_entry = ctk.CTkEntry(self, width=220)
        self.email_entry.pack(pady=5)
        self.email_entry.bind("<Return>", lambda event: self.attempt_login())
        self.email_entry.focus_set()

        ctk.CTkLabel(self, text="Password:").pack()
        self.password_entry = ctk.CTkEntry(self, width=220, show="*")
        self.password_entry.pack(pady=5)
        self.password_entry.bind("<Return>", lambda event: self.attempt_login())

        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.pack(pady=5)

        ctk.CTkButton(self, text="Login", command=self.attempt_login).pack(pady=10)

    def attempt_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        if not email:
            self.error_label.configure(text="Please enter an email.")
            return

        success, message, user_data = authenticate_user(email, password)
        if not success:
            self.error_label.configure(text=message)
            return

        # Route to the correct dashboard based on the account's role.
        role = user_data[4]
        dashboards = {
            "Customer": CustomerDashboard,
            "Clerk": ClerkDashboard,
            "Admin": AdminDashboard,
        }
        dashboard_class = dashboards.get(role)
        if not dashboard_class:
            self.error_label.configure(text=f"Unknown role: {role}")
            return

        self.controller.switch_frame(dashboard_class, self.controller, user_data)


class CustomerDashboard(ctk.CTkFrame):
    """Customer-facing screen: browse available inventory, rent an item, and
    review your own rental/return history."""

    def __init__(self, parent, controller, user_data):
        super().__init__(parent)
        self.controller = controller
        self.member_number = user_data[0]

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=10)
        ctk.CTkLabel(header, text=f"Welcome to your Dashboard, {user_data[1]}", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20)
        ctk.CTkButton(header, text="Logout", command=lambda: self.controller.switch_frame(LoginScreen, self.controller)).pack(side="right", padx=20)

        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack()

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Available items table, with a button to rent whatever row is selected.
        inventory_frame = create_section(body, "Available Items", fill="both", expand=True)
        self.inventory_tree = ttk.Treeview(
            inventory_frame, columns=("title", "type", "available"), show="headings", height=6
        )
        self.inventory_tree.heading("title", text="Title")
        self.inventory_tree.heading("type", text="Type")
        self.inventory_tree.heading("available", text="Available Copies")
        self.inventory_tree.pack(fill="both", expand=True, side="top")
        ctk.CTkButton(inventory_frame, text="Rent Selected", command=self.rent_selected).pack(pady=5)

        # Read-only history of this customer's own rentals and returns.
        history_frame = create_section(body, "My Rental & Return History", fill="both", expand=True)
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
        """Reloads both tables from the database, replacing all rows currently shown."""
        for row in self.inventory_tree.get_children():
            self.inventory_tree.delete(row)
        for item_id, title, item_type, available in get_available_inventory():
            # Treeview iid is set to the item_id so we can map a selection back to a row's primary key.
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
            self.status_label.configure(text="Select an item to rent.", text_color="red")
            return

        item_id = int(selected[0])
        success, message = request_rental(self.member_number, item_id)
        self.status_label.configure(text=message, text_color="green" if success else "red")
        if success:
            self.refresh()


class ClerkDashboard(ctk.CTkFrame):
    """Clerk-facing screen: day-to-day store operations - register members,
    reset customer passwords, approve/deny rental requests, and process returns."""

    def __init__(self, parent, controller, user_data):
        super().__init__(parent)
        self.controller = controller

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=10)
        ctk.CTkLabel(header, text="Store Clerk Operational Command Console", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20)
        ctk.CTkButton(header, text="Logout", command=lambda: self.controller.switch_frame(LoginScreen, self.controller)).pack(side="right", padx=20)

        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack()

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # --- Register New Member form ---
        member_frame = create_section(body, "Register New Member")

        ctk.CTkLabel(member_frame, text="Name:").grid(row=0, column=0, padx=5, pady=8, sticky="e")
        self.new_member_name_entry = ctk.CTkEntry(member_frame, width=160)
        self.new_member_name_entry.grid(row=0, column=1, padx=5, pady=8)

        ctk.CTkLabel(member_frame, text="Email:").grid(row=0, column=2, padx=5, pady=8, sticky="e")
        self.new_member_email_entry = ctk.CTkEntry(member_frame, width=200)
        self.new_member_email_entry.grid(row=0, column=3, padx=5, pady=8)

        ctk.CTkLabel(member_frame, text="Starting Balance:").grid(row=0, column=4, padx=5, pady=8, sticky="e")
        self.new_member_balance_entry = ctk.CTkEntry(member_frame, width=80)
        self.new_member_balance_entry.insert(0, "0")
        self.new_member_balance_entry.grid(row=0, column=5, padx=5, pady=8)

        ctk.CTkLabel(member_frame, text="Password:").grid(row=0, column=6, padx=5, pady=8, sticky="e")
        self.new_member_password_entry = ctk.CTkEntry(member_frame, width=140, show="*")
        self.new_member_password_entry.grid(row=0, column=7, padx=5, pady=8)

        ctk.CTkButton(member_frame, text="Register Member", command=self.add_member).grid(row=0, column=8, padx=10, pady=8)

        # --- Reset Customer Password form ---
        password_frame = create_section(body, "Reset Customer Password")

        ctk.CTkLabel(password_frame, text="Email:").grid(row=0, column=0, padx=5, pady=8, sticky="e")
        self.reset_password_email_entry = ctk.CTkEntry(password_frame, width=200)
        self.reset_password_email_entry.grid(row=0, column=1, padx=5, pady=8)

        ctk.CTkLabel(password_frame, text="New Password:").grid(row=0, column=2, padx=5, pady=8, sticky="e")
        self.reset_password_entry = ctk.CTkEntry(password_frame, width=140, show="*")
        self.reset_password_entry.grid(row=0, column=3, padx=5, pady=8)

        ctk.CTkButton(password_frame, text="Set Password", command=self.reset_password).grid(row=0, column=4, padx=10, pady=8)

        # --- Pending rental requests, awaiting approve/deny ---
        pending_frame = create_section(body, "Pending Rental Requests", fill="both", expand=True)
        self.pending_tree = ttk.Treeview(
            pending_frame, columns=("customer", "title", "requested"), show="headings", height=6
        )
        self.pending_tree.heading("customer", text="Customer")
        self.pending_tree.heading("title", text="Item")
        self.pending_tree.heading("requested", text="Requested On")
        self.pending_tree.pack(fill="both", expand=True, side="top")

        pending_buttons = ctk.CTkFrame(pending_frame, fg_color="transparent")
        pending_buttons.pack(pady=5)
        ctk.CTkButton(pending_buttons, text="Approve Selected", command=self.approve_selected).pack(side="left", padx=5)
        ctk.CTkButton(pending_buttons, text="Deny Selected", command=self.deny_selected).pack(side="left", padx=5)

        # --- Active (approved/late) rentals, awaiting return ---
        active_frame = create_section(body, "Active Rentals (Process Return)", fill="both", expand=True)
        self.active_tree = ttk.Treeview(
            active_frame, columns=("customer", "title", "due", "status"), show="headings", height=6
        )
        for col, label in [
            ("customer", "Customer"), ("title", "Item"), ("due", "Due Date"), ("status", "Status"),
        ]:
            self.active_tree.heading(col, text=label)
        self.active_tree.pack(fill="both", expand=True, side="top")
        ctk.CTkButton(active_frame, text="Process Return", command=self.process_return_selected).pack(pady=5)

        # Treeview rows only store what's shown on screen, so we keep a
        # rental_id -> item_id lookup on the side for actions that need the item too.
        self._active_item_ids = {}
        self._pending_item_ids = {}
        self.refresh()

    def refresh(self):
        """Reloads the pending and active rental tables from the database."""
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

    def add_member(self):
        name = self.new_member_name_entry.get().strip()
        email = self.new_member_email_entry.get().strip()
        balance_text = self.new_member_balance_entry.get().strip()
        password = self.new_member_password_entry.get()

        if not name or not email or not password:
            self.status_label.configure(text="Name, email, and password are required.", text_color="red")
            return
        try:
            balance = float(balance_text)
        except ValueError:
            self.status_label.configure(text="Starting balance must be a number.", text_color="red")
            return

        # Clerks can only register Customer accounts (no role field on this form).
        success, message = add_member(name, email, balance, "Customer", password)
        self.status_label.configure(text=message, text_color="green" if success else "red")
        if success:
            self.new_member_name_entry.delete(0, "end")
            self.new_member_email_entry.delete(0, "end")
            self.new_member_balance_entry.delete(0, "end")
            self.new_member_balance_entry.insert(0, "0")
            self.new_member_password_entry.delete(0, "end")

    def reset_password(self):
        email = self.reset_password_email_entry.get().strip()
        new_password = self.reset_password_entry.get()

        if not email or not new_password:
            self.status_label.configure(text="Email and new password are required.", text_color="red")
            return

        success, message = set_member_password(email, new_password)
        self.status_label.configure(text=message, text_color="green" if success else "red")
        if success:
            self.reset_password_email_entry.delete(0, "end")
            self.reset_password_entry.delete(0, "end")

    def approve_selected(self):
        selected = self.pending_tree.selection()
        if not selected:
            self.status_label.configure(text="Select a pending request to approve.", text_color="red")
            return

        rental_id = int(selected[0])
        success, message = approve_rental(rental_id)
        self.status_label.configure(text=message, text_color="green" if success else "red")
        if success:
            self.refresh()

    def deny_selected(self):
        selected = self.pending_tree.selection()
        if not selected:
            self.status_label.configure(text="Select a pending request to deny.", text_color="red")
            return

        rental_id = int(selected[0])
        item_id = self._pending_item_ids[selected[0]]  # need item_id too, so the copy can be restocked
        success, message = deny_rental(rental_id, item_id)
        self.status_label.configure(text=message, text_color="green" if success else "red")
        if success:
            self.refresh()

    def process_return_selected(self):
        selected = self.active_tree.selection()
        if not selected:
            self.status_label.configure(text="Select a rental to process its return.", text_color="red")
            return

        rental_id = int(selected[0])
        item_id = self._active_item_ids[selected[0]]
        success, message = process_return(rental_id, item_id)
        self.status_label.configure(text=message, text_color="green" if success else "red")
        if success:
            self.refresh()


class AdminDashboard(ctk.CTkFrame):
    """Admin-facing screen: everything a clerk can do plus catalog management
    (adding inventory), registering members of any role, and a store-wide
    view of all rentals/returns."""

    def __init__(self, parent, controller, user_data):
        super().__init__(parent)
        self.controller = controller

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=10)
        ctk.CTkLabel(header, text="Main Admin Master Analytics Panel", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20)
        ctk.CTkButton(header, text="Logout", command=lambda: self.controller.switch_frame(LoginScreen, self.controller)).pack(side="right", padx=20)
        ctk.CTkButton(header, text="Refresh", command=lambda: self.refresh()).pack(side="right", padx=5)

        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack()

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # --- Add New Movie / Equipment form ---
        add_frame = create_section(body, "Add New Movie / Equipment")

        ctk.CTkLabel(add_frame, text="Title:").grid(row=0, column=0, padx=5, pady=8, sticky="e")
        self.new_title_entry = ctk.CTkEntry(add_frame, width=180)
        self.new_title_entry.grid(row=0, column=1, padx=5, pady=8)

        ctk.CTkLabel(add_frame, text="Type:").grid(row=0, column=2, padx=5, pady=8, sticky="e")
        self.new_type_combo = ctk.CTkComboBox(add_frame, values=["VHS", "DVD", "CD", "Equipment"], width=110)
        self.new_type_combo.set("VHS")
        self.new_type_combo.grid(row=0, column=3, padx=5, pady=8)

        ctk.CTkLabel(add_frame, text="Copies:").grid(row=0, column=4, padx=5, pady=8, sticky="e")
        self.new_copies_entry = ctk.CTkEntry(add_frame, width=60)
        self.new_copies_entry.insert(0, "1")
        self.new_copies_entry.grid(row=0, column=5, padx=5, pady=8)

        ctk.CTkButton(add_frame, text="Add Item", command=self.add_item).grid(row=0, column=6, padx=10, pady=8)

        # --- Register New Member form (admin version: includes a role picker) ---
        member_frame = create_section(body, "Register New Member")

        ctk.CTkLabel(member_frame, text="Name:").grid(row=0, column=0, padx=5, pady=8, sticky="e")
        self.new_member_name_entry = ctk.CTkEntry(member_frame, width=160)
        self.new_member_name_entry.grid(row=0, column=1, padx=5, pady=8)

        ctk.CTkLabel(member_frame, text="Email:").grid(row=0, column=2, padx=5, pady=8, sticky="e")
        self.new_member_email_entry = ctk.CTkEntry(member_frame, width=200)
        self.new_member_email_entry.grid(row=0, column=3, padx=5, pady=8)

        ctk.CTkLabel(member_frame, text="Balance:").grid(row=0, column=4, padx=5, pady=8, sticky="e")
        self.new_member_balance_entry = ctk.CTkEntry(member_frame, width=80)
        self.new_member_balance_entry.insert(0, "0")
        self.new_member_balance_entry.grid(row=0, column=5, padx=5, pady=8)

        ctk.CTkLabel(member_frame, text="Role:").grid(row=0, column=6, padx=5, pady=8, sticky="e")
        self.new_member_role_combo = ctk.CTkComboBox(member_frame, values=["Customer", "Clerk", "Admin"], width=100)
        self.new_member_role_combo.set("Customer")
        self.new_member_role_combo.grid(row=0, column=7, padx=5, pady=8)

        ctk.CTkLabel(member_frame, text="Password:").grid(row=0, column=8, padx=5, pady=8, sticky="e")
        self.new_member_password_entry = ctk.CTkEntry(member_frame, width=140, show="*", placeholder_text="Customers only")
        self.new_member_password_entry.grid(row=0, column=9, padx=5, pady=8)

        ctk.CTkButton(member_frame, text="Register Member", command=self.add_member).grid(row=0, column=10, padx=10, pady=8)

        # --- Reset Customer Password form ---
        password_frame = create_section(body, "Reset Customer Password")

        ctk.CTkLabel(password_frame, text="Email:").grid(row=0, column=0, padx=5, pady=8, sticky="e")
        self.reset_password_email_entry = ctk.CTkEntry(password_frame, width=200)
        self.reset_password_email_entry.grid(row=0, column=1, padx=5, pady=8)

        ctk.CTkLabel(password_frame, text="New Password:").grid(row=0, column=2, padx=5, pady=8, sticky="e")
        self.reset_password_entry = ctk.CTkEntry(password_frame, width=140, show="*")
        self.reset_password_entry.grid(row=0, column=3, padx=5, pady=8)

        ctk.CTkButton(password_frame, text="Set Password", command=self.reset_password).grid(row=0, column=4, padx=10, pady=8)

        # --- Read-only current inventory table ---
        inventory_frame = create_section(body, "Current Inventory", fill="both", expand=True)
        self.inventory_tree = ttk.Treeview(
            inventory_frame, columns=("title", "type", "available"), show="headings", height=5
        )
        self.inventory_tree.heading("title", text="Title")
        self.inventory_tree.heading("type", text="Type")
        self.inventory_tree.heading("available", text="Available Copies")
        self.inventory_tree.pack(fill="both", expand=True)

        # --- Store-wide rentals/returns, with an approve action available here too ---
        overview_frame = create_section(body, "All Rentals & Returns", fill="both", expand=True)
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
        ctk.CTkButton(overview_frame, text="Approve Selected", command=self.approve_selected).pack(pady=5)

        self.refresh()

    def refresh(self):
        """Reloads the inventory and store-wide rentals tables from the database."""
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
            self.status_label.configure(text="Title and type are required.", text_color="red")
            return
        if not copies_text.isdigit():
            self.status_label.configure(text="Copies must be a whole number.", text_color="red")
            return

        success, message = add_inventory_item(title, item_type, int(copies_text))
        self.status_label.configure(text=message, text_color="green" if success else "red")
        if success:
            self.new_title_entry.delete(0, "end")
            self.new_copies_entry.delete(0, "end")
            self.new_copies_entry.insert(0, "1")
            self.refresh()

    def add_member(self):
        name = self.new_member_name_entry.get().strip()
        email = self.new_member_email_entry.get().strip()
        balance_text = self.new_member_balance_entry.get().strip()
        role = self.new_member_role_combo.get().strip()
        password = self.new_member_password_entry.get()

        if not name or not email or not role:
            self.status_label.configure(text="Name, email, and role are required.", text_color="red")
            return
        # Clerk/Admin accounts use the fixed role password, so only Customer
        # registrations need a password entered here.
        if role == "Customer" and not password:
            self.status_label.configure(text="Password is required for customer accounts.", text_color="red")
            return
        try:
            balance = float(balance_text)
        except ValueError:
            self.status_label.configure(text="Balance must be a number.", text_color="red")
            return

        success, message = add_member(name, email, balance, role, password)
        self.status_label.configure(text=message, text_color="green" if success else "red")
        if success:
            self.new_member_name_entry.delete(0, "end")
            self.new_member_email_entry.delete(0, "end")
            self.new_member_balance_entry.delete(0, "end")
            self.new_member_balance_entry.insert(0, "0")
            self.new_member_role_combo.set("Customer")
            self.new_member_password_entry.delete(0, "end")

    def reset_password(self):
        email = self.reset_password_email_entry.get().strip()
        new_password = self.reset_password_entry.get()

        if not email or not new_password:
            self.status_label.configure(text="Email and new password are required.", text_color="red")
            return

        success, message = set_member_password(email, new_password)
        self.status_label.configure(text=message, text_color="green" if success else "red")
        if success:
            self.reset_password_email_entry.delete(0, "end")
            self.reset_password_entry.delete(0, "end")

    def approve_selected(self):
        selected = self.overview_tree.selection()
        if not selected:
            self.status_label.configure(text="Select a pending request to approve.", text_color="red")
            return

        rental_id = int(selected[0])
        success, message = approve_rental(rental_id)
        self.status_label.configure(text=message, text_color="green" if success else "red")
        if success:
            self.refresh()
