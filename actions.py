import sqlite3
from contextlib import closing
from datetime import date, timedelta

DB_NAME = "blockbuster.db"

RENTAL_PERIOD_DAYS = 7

MIN_CASH_BALANCE = 100
ACTIVE_RENTAL_STATUSES = ("Pending", "Approved", "Late")


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def authenticate_user(email):
    """Looks up a member by email for login and returns their role-routing data."""
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT member_number, name, email, cash_balance, role FROM users WHERE email = ?",
            (email,),
        )
        user = cursor.fetchone()
        if not user:
            return False, "No account found with that email.", None

        return True, "Login successful.", user


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

        cursor.execute(
            "UPDATE inventory SET available_copies = available_copies + 1 WHERE item_id = ?",
            (item_id,),
        )
        conn.commit()

        return True, "Rental request denied."


def get_active_rentals():
    """Clerk operation: Lists Approved/Late rentals that are out and awaiting return."""
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

        cursor.execute(
            "UPDATE inventory SET available_copies = available_copies + 1 WHERE item_id = ?",
            (item_id,),
        )
        conn.commit()

        return True, "Item returned safely."


def get_all_rentals():
    """Admin operation: Store-wide rental and return history, most recent first."""
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
