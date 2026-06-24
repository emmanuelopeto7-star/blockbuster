import sqlite3

DB_NAME = "blockbuster.db"


def initialize_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            member_number INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            cash_balance REAL NOT NULL DEFAULT 0,
            role TEXT NOT NULL DEFAULT 'Customer'
        )
        """
    )

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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO users (name, email, cash_balance, role) VALUES (?, ?, ?, ?)",
            [
                ("Main Admin", "admin@blockbuster.com", 0.0, "Admin"),
                ("Store Clerk", "clerk@blockbuster.com", 0.0, "Clerk"),
                ("John Doe", "john@customer.com", 45.0, "Customer"),
            ],
        )

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


if __name__ == "__main__":
    initialize_db()
    seed_data()
