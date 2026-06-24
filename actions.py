import sqlite3
from datetime import datetime

DB_NAME="blockbuster.db"

def get_db_connection():
    return sqlite3.connect(DB_NAME)

def Check_rental_eligibility(member_number):
    """
    Enforces specification rules: Must be a registered member, 
    have a cash balance >= 100, and have zero active pending returns. [cite: 23]
    """
    conn= get_db_connection()
    cursor=conn.cursor()

    cursor.execute("SELECT cash_balance FROM users WHERE member_number = ?", (member_number,))
    user=cursor.fetchone()
    if not user:
        conn.close()
        return False,"Membership not found."
    
    cash_balance = user[0]
    if cash_balance < 100:
        conn.close()
        return False, f"Denied: Balance is {cash_balance}. Minimum 100 cash balance required." 
    
    cursor.excecute('''
        SELECT COUNT(*) FROM rentals 
        WHERE member_number = ? AND status IN ('Pending', 'Approved', 'Late')
    ''', (member_number,))

    pending_returns = cursor.fetchone()[0]
    conn.close()

    if pending_returns > 0:
        return False, f"Denied: Account has {pending_returns} unreturned item(s)."
    
    return True, "Eligible to request rentals."

def approve_rental(rental_id):
    """Clerk operation: Sets a pending rental status to Approved."""
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute("UPDATE rentals SET status = 'Approved' WHERE rental_id = ?", (rental_id,))
    conn.commit()
    conn.close()
    return True,"Rental request approved successfully."

def process_return(rental_id, item_id):
    """Clerk operation: Receives and inspects returns, restocking inventory logs."""
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute ("UPDATE rentals SET status = 'Returned' WHERE rental_id = ?", (rental_id,))
    conn.commit()
    conn.close()

    return True, "Item returned safely"

def clerk_approve_rental(rental_id):
    """Clerk updates a customer's rental request status from 'Pending' to 'Approved'."""
    conn=sqlite3.connect(DB_NAME)
    cursor=conn.cursor()
    cursor.execute("UPDATE rentals SET status = 'Approved' WHERE rental_id = ?", (rental_id,))
    conn.commit()
    conn.close()
    return True, "Rental request has been approved."





                    

    

