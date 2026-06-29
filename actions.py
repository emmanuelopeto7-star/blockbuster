import hashlib
import sqlite3
from contextlib import closing
from datetime import date, timedelta

DB_NAME = "blockbuster.db"

# How long a customer gets to keep a rented item before it's considered late.
RENTAL_PERIOD_DAYS = 7

# Customers need at least this much cash on their account to rent anything.
MIN_CASH_BALANCE = 100
# Rental statuses that count as "currently out" / not yet resolved.
ACTIVE_RENTAL_STATUSES = ("Pending", "Approved", "Late")


def get_db_connection():
    """Opens a fresh SQLite connection with foreign key enforcement turned on."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def update_late_rentals():
    """Flips Approved rentals past their due date to Late."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE rentals SET status = 'Late' WHERE status = 'Approved' AND due_date < ?",
            (date.today().isoformat(),),
        )
        conn.commit()


# Clerk and Admin accounts share one fixed password per role instead of a
# per-account password, since they're staff logins rather than registered members.
ROLE_PASSWORDS = {
    "Clerk": "Clerk6969",
    "Admin": "admin6767",
}


def hash_password(password):
    """One-way hash for storing/comparing customer passwords (never store plaintext)."""
    return hashlib.sha256((password or "").encode("utf-8")).hexdigest()


def authenticate_user(email, password=None):
    """Looks up a member by email for login and returns their role-routing data.

    Clerk and Admin roles use their fixed role password; Customers are
    checked against the password set on their account at registration.
    """
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT member_number, name, email, cash_balance, role, password FROM users WHERE email = ?",
            (email,),
        )
        user = cursor.fetchone()
        if not user:
            return False, "No account found with that email.", None

        role = user[4]
        required_password = ROLE_PASSWORDS.get(role)
        if required_password is not None:
            # Staff account: compare against the fixed role password directly.
            if password != required_password:
                return False, "Incorrect password.", None
        elif hash_password(password) != user[5]:
            # Customer account: compare hashes against what's stored in the DB.
            return False, "Incorrect password.", None

        return True, "Login successful.", user[:5]


def get_available_inventory():
    """Returns all inventory items for display on the customer rental screen."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT item_id, title, item_type, available_copies FROM inventory ORDER BY title")
        return cursor.fetchall()


def add_inventory_item(title, item_type, copies):
    """Admin operation: Adds a new movie or piece of equipment to inventory."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO inventory (title, item_type, available_copies) VALUES (?, ?, ?)",
            (title, item_type, copies),
        )
        conn.commit()

        return True, f"Added '{title}' to inventory."


def add_member(name, email, cash_balance=0.0, role="Customer", password=""):
    """Admin/Clerk operation: Registers a new member account.

    The password is only meaningful for Customer accounts; Clerk and Admin
    accounts log in with their fixed role password regardless of what's stored.
    """
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, cash_balance, role, password) VALUES (?, ?, ?, ?, ?)",
                (name, email, cash_balance, role, hash_password(password)),
            )
        except sqlite3.IntegrityError:
            # email column is UNIQUE, so this fires when the address is already registered.
            return False, f"A member with email '{email}' already exists."
        conn.commit()

        return True, f"Member '{name}' registered successfully."


def set_member_password(email, new_password):
    """Clerk/Admin operation: Sets or resets a member's login password.
    """
    if not new_password:
        return False, "New password is required."

    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password = ? WHERE email = ?",
            (hash_password(new_password), email),
        )
        conn.commit()

        if cursor.rowcount == 0:
            return False, f"No member found with email '{email}'."
        return True, "Password updated successfully."


def request_rental(member_number, item_id):
    """Customer operation: Requests a rental if eligible and the item is in stock."""
    eligible, reason = check_rental_eligibility(member_number)
    if not eligible:
        return False, reason

    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT available_copies FROM inventory WHERE item_id = ?", (item_id,))
        item = cursor.fetchone()
        if not item:
            return False, "Item not found."
        if item[0] <= 0:
            return False, "No copies available for this item."

        # New rentals start as Pending until a clerk approves them, and the
        # due date is locked in up front based on the standard rental period.
        due_date = date.today() + timedelta(days=RENTAL_PERIOD_DAYS)
        cursor.execute(
            "INSERT INTO rentals (item_id, member_number, due_date, status) VALUES (?, ?, ?, 'Pending')",
            (item_id, member_number, due_date.isoformat()),
        )
        cursor.execute(
            "UPDATE inventory SET available_copies = available_copies - 1 WHERE item_id = ?",
            (item_id,),
        )
        conn.commit()

        return True, "Rental requested successfully."


def get_rental_history(member_number):
    """Returns a customer's own rental and return history, most recent first."""
    update_late_rentals()
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.rental_id, i.title, r.rental_date, r.due_date, r.return_date, r.status
            FROM rentals r
            JOIN inventory i ON r.item_id = i.item_id
            WHERE r.member_number = ?
            ORDER BY r.rental_date DESC
            """,
            (member_number,),
        )
        return cursor.fetchall()


def check_rental_eligibility(member_number):
    """
    Enforces specification rules: Must be a registered member,
    have a cash balance >= 100, and have zero active pending returns.
    """
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT cash_balance FROM users WHERE member_number = ?", (member_number,))
        user = cursor.fetchone()
        if not user:
            return False, "Membership not found."

        cash_balance = user[0]
        if cash_balance < MIN_CASH_BALANCE:
            return False, f"Denied: Balance is {cash_balance}. Minimum {MIN_CASH_BALANCE} cash balance required."

        # Count anything still Pending/Approved/Late - those are items the
        # member hasn't settled yet, so they block new rental requests.
        cursor.execute(
            f"""
            SELECT COUNT(*) FROM rentals
            WHERE member_number = ? AND status IN ({",".join("?" * len(ACTIVE_RENTAL_STATUSES))})
            """,
            (member_number, *ACTIVE_RENTAL_STATUSES),
        )
        pending_returns = cursor.fetchone()[0]

        if pending_returns > 0:
            return False, f"Denied: Account has {pending_returns} unreturned item(s)."

        return True, "Eligible to request rentals."


def get_pending_rentals():
    """Clerk operation: Lists all rentals awaiting approval, oldest first."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.rental_id, u.name, i.title, r.rental_date, r.item_id
            FROM rentals r
            JOIN users u ON r.member_number = u.member_number
            JOIN inventory i ON r.item_id = i.item_id
            WHERE r.status = 'Pending'
            ORDER BY r.rental_date
            """
        )
        return cursor.fetchall()


def approve_rental(rental_id):
    """Clerk operation: Sets a Pending rental's status to Approved."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE rentals SET status = 'Approved' WHERE rental_id = ? AND status = 'Pending'",
            (rental_id,),
        )
        conn.commit()

        if cursor.rowcount == 0:
            # rowcount is 0 if the rental doesn't exist or already moved out of Pending.
            return False, "Rental not found or is not awaiting approval."
        return True, "Rental request approved successfully."


def deny_rental(rental_id, item_id):
    """Clerk operation: Sets a Pending rental's status to Denied and restocks the item."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE rentals SET status = 'Denied' WHERE rental_id = ? AND status = 'Pending'",
            (rental_id,),
        )
        if cursor.rowcount == 0:
            conn.commit()
            return False, "Rental not found or is not awaiting approval."

        # The copy was reserved (decremented) when the request was made, so
        # denying it has to give that copy back to inventory.
        cursor.execute(
            "UPDATE inventory SET available_copies = available_copies + 1 WHERE item_id = ?",
            (item_id,),
        )
        conn.commit()

        return True, "Rental request denied."


def get_active_rentals():
    """Clerk operation: Lists Approved/Late rentals that are out and awaiting return."""
    update_late_rentals()
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.rental_id, u.name, i.title, r.item_id, r.due_date, r.status
            FROM rentals r
            JOIN users u ON r.member_number = u.member_number
            JOIN inventory i ON r.item_id = i.item_id
            WHERE r.status IN ('Approved', 'Late')
            ORDER BY r.due_date
            """
        )
        return cursor.fetchall()


def process_return(rental_id, item_id):
    """Clerk operation: Receives and inspects returns, restocking inventory."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE rentals SET status = 'Returned', return_date = CURRENT_TIMESTAMP WHERE rental_id = ?",
            (rental_id,),
        )
        if cursor.rowcount == 0:
            conn.commit()
            return False, "Rental not found."

        # Returning the item frees up a copy for the next customer to rent.
        cursor.execute(
            "UPDATE inventory SET available_copies = available_copies + 1 WHERE item_id = ?",
            (item_id,),
        )
        conn.commit()

        return True, "Item returned safely."


def get_all_rentals():
    """Admin operation: Store-wide rental and return history, most recent first."""
    update_late_rentals()
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.rental_id, u.name, i.title, r.rental_date, r.due_date, r.return_date, r.status
            FROM rentals r
            JOIN users u ON r.member_number = u.member_number
            JOIN inventory i ON r.item_id = i.item_id
            ORDER BY r.rental_date DESC
            """
        )
        return cursor.fetchall()
