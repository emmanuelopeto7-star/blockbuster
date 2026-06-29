import sqlite3

from actions import hash_password

DB_NAME = "blockbuster.db"


def initialize_db():
    """Creates the users/inventory/rentals tables if they don't exist yet, and
    runs a small migration to add the password column to older databases."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    # Member accounts: Customer / Clerk / Admin, distinguished by `role`.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            member_number INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            cash_balance REAL NOT NULL DEFAULT 0,
            role TEXT NOT NULL DEFAULT 'Customer',
            password TEXT NOT NULL DEFAULT ''
        )
        """
    )

    # Older copies of blockbuster.db may predate the password column, so add
    # it on the fly and seed a known password for the original demo customer.
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if "password" not in existing_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN password TEXT NOT NULL DEFAULT ''")
        cursor.execute(
            "UPDATE users SET password = ? WHERE email = ? AND password = ''",
            (hash_password("customer123"), "john@customer.com"),
        )

    # Catalog of rentable items (VHS, DVD, CD, equipment, etc.).
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            item_type TEXT NOT NULL,
            available_copies INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    # One row per rental request; status tracks it through its lifecycle
    # (Pending -> Approved -> Late/Returned, or Denied).
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rentals (
            rental_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            member_number INTEGER NOT NULL,
            rental_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            due_date TEXT,
            return_date TEXT,
            status TEXT NOT NULL DEFAULT 'Pending',
            FOREIGN KEY (item_id) REFERENCES inventory (item_id),
            FOREIGN KEY (member_number) REFERENCES users (member_number)
        )
        """
    )

    conn.commit()
    conn.close()


def seed_data():
    """Inserts demo accounts and inventory the first time the database is empty."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Only seed users if the table is completely empty, so this is safe to
    # call repeatedly without duplicating data.
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO users (name, email, cash_balance, role, password) VALUES (?, ?, ?, ?, ?)",
            [
                ("Main Admin", "admin@blockbuster.com", 0.0, "Admin", hash_password("admin6767")),
                ("Store Clerk", "clerk@blockbuster.com", 0.0, "Clerk", hash_password("Clerk6969")),
                ("John Doe", "john@customer.com", 45.0, "Customer", hash_password("customer123")),
            ],
        )

    # Same idea for inventory: seed a few sample items only on a fresh database.
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO inventory (title, item_type, available_copies) VALUES (?, ?, ?)",
            [
                ("The Matrix VHS", "VHS", 2),
                ("Interstellar CD", "CD", 4),
                ("Sony DVD Player", "Equipment", 2),
            ],
        )

    conn.commit()
    conn.close()
    print("Database schema complete and sample records seeded")


# Allows running `python database.py` directly to (re)build and seed the
# database without launching the GUI.
if __name__ == "__main__":
    initialize_db()
    seed_data()
