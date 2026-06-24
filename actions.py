import sqlite3
from contextlib import closing

DB_NAME = "blockbuster.db"

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
