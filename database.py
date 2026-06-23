import sqlite3

DB_NAME="blockbuster.db"

def initialize_db():
    conn=sqlite3.connect(DB_NAME)
    cursor=conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS movies (
            movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT,
            release_year INTEGER,
            rental_price REAL NOT NULL DEFAULT 0,
            stock_total INTEGER NOT NULL DEFAULT 0,
            stock_available INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            join_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rentals (
            rental_id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            rental_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            due_date TEXT NOT NULL,
            return_date TEXT,
            returned INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (movie_id) REFERENCES movies (movie_id),
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
        """
    )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_db()
    print(f"Initialized {DB_NAME} with movies, customers, and rentals tables")

def seed_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELLECT COUNT (* FROM users")
    if cursor.fetchone()[0] ==0:
        cursor.executemany('''
            INSERT INTO users (name, email, cash_balance, role) VALUES (?, ?, ?, ?)
        ''', [
            ('Main Admin', 'admin@blockbuster.com', 0.0, 'Admin'),
            ('Store Clerk', 'clerk@blockbuster.com', 0.0, 'Clerk'),            
            ('John Doe', 'john@customer.com', 45.0, 'Customer')               
        ])
    cursor.executemany('''
            INSERT INTO inventory (title, item_type, available_copies) VALUES (?, ?, ?)
        ''', [
            ('The Matrix VHS', 'VHS', 2),
            ('Interstellar CD', 'CD', 4),
            ('Sony DVD Player', 'Equipment', 2)
        ])     

    conn.commit()
    conn.close()
    print("Database schema complete and sample records seeded")

if __name__=="__main__":
    initialize_db()
    seed_data()       
        
