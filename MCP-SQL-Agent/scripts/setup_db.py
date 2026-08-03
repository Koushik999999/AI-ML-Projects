"""Create the sample SQLite database for the MCP Text-to-SQL project."""

import sqlite3
from pathlib import Path


# ---------------------------------------------------------
# Database location
# ---------------------------------------------------------

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sample.db"


def setup() -> None:

    # Create data/ directory if it doesn't exist
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Delete old DB so every run starts clean
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # =====================================================
    # 1. EMPLOYEES
    # =====================================================

    cur.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            salary REAL NOT NULL,
            city TEXT NOT NULL
        );
    """)

    cur.executemany(
        """
        INSERT INTO employees
        (id, name, department, salary, city)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (1, "Alice", "Engineering", 95000, "Berlin"),
            (2, "Bob", "Sales", 72000, "London"),
            (3, "Charlie", "Engineering", 105000, "Paris"),
            (4, "David", "Marketing", 68000, "Madrid"),
            (5, "Eva", "Finance", 88000, "Berlin"),
            (6, "Frank", "Sales", 76000, "Amsterdam"),
            (7, "Grace", "Engineering", 99000, "London"),
            (8, "Henry", "Finance", 92000, "Paris"),
            (9, "Irene", "Marketing", 71000, "Rome"),
            (10, "Jack", "Engineering", 110000, "Berlin"),
        ],
    )

    # =====================================================
    # 2. CUSTOMERS
    # =====================================================

    cur.execute("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            company_name TEXT NOT NULL,
            country TEXT NOT NULL,
            currency TEXT NOT NULL,
            credit_limit REAL NOT NULL
        );
    """)

    cur.executemany(
        """
        INSERT INTO customers
        (id, company_name, country, currency, credit_limit)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (1, "Acme GmbH", "Germany", "EUR", 15400.50),
            (2, "Prague Widgets", "Czech Republic", "CZK", 342000.00),
            (3, "Berlin Tech", "Germany", "EUR", 88200.00),
            (4, "London Analytics", "United Kingdom", "GBP", 45000.00),
            (5, "CZ Solutions", "Czech Republic", "CZK", 198000.00),
            (6, "Euro Supplies", "France", "EUR", 23100.75),
            (7, "Nordic Data", "Sweden", "SEK", 67000.00),
            (8, "Praha Services", "Czech Republic", "CZK", 410000.00),
            (9, "Milan Corp", "Italy", "EUR", 54200.00),
            (10, "Swiss Holdings", "Switzerland", "CHF", 120000.00),
        ],
    )

    # =====================================================
    # 3. PRODUCTS
    # =====================================================

    cur.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL
        );
    """)

    cur.executemany(
        """
        INSERT INTO products
        (id, product_name, category, price, stock_quantity)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (1, "Widget A", "Hardware", 2500.00, 45),
            (2, "Widget B", "Hardware", 1800.00, 70),
            (3, "Gadget X", "Electronics", 5400.00, 20),
            (4, "Gadget Y", "Electronics", 3200.00, 35),
            (5, "Service Pro", "Software", 9000.00, 100),
            (6, "Analytics Basic", "Software", 4500.00, 100),
            (7, "Analytics Pro", "Software", 12000.00, 100),
            (8, "Sensor X", "Hardware", 2700.00, 60),
            (9, "Sensor Pro", "Hardware", 4200.00, 25),
            (10, "Cloud Enterprise", "Software", 15000.00, 100),
        ],
    )

    # =====================================================
    # 4. ORDERS
    # =====================================================

    cur.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            amount REAL NOT NULL,
            order_date TEXT NOT NULL,

            FOREIGN KEY (customer_id)
                REFERENCES customers(id),

            FOREIGN KEY (product_id)
                REFERENCES products(id)
        );
    """)

    cur.executemany(
        """
        INSERT INTO orders
        (id, customer_id, product_id, quantity, amount, order_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (1, 1, 1, 1, 2500.00, "2024-11-15"),
            (2, 1, 2, 2, 3600.00, "2025-01-10"),
            (3, 2, 3, 1, 5400.00, "2025-02-01"),
            (4, 3, 1, 2, 5000.00, "2025-01-20"),
            (5, 4, 5, 1, 9000.00, "2025-03-05"),
            (6, 5, 3, 3, 16200.00, "2024-12-22"),
            (7, 6, 2, 4, 7200.00, "2025-02-14"),
            (8, 7, 8, 2, 5400.00, "2025-03-18"),
            (9, 8, 7, 1, 12000.00, "2025-04-02"),
            (10, 9, 4, 3, 9600.00, "2025-04-15"),
            (11, 10, 10, 1, 15000.00, "2025-05-01"),
            (12, 3, 9, 2, 8400.00, "2025-05-12"),
            (13, 1, 6, 1, 4500.00, "2025-06-07"),
            (14, 6, 5, 2, 18000.00, "2025-06-21"),
            (15, 4, 7, 1, 12000.00, "2025-07-03"),
        ],
    )

    # Save changes
    conn.commit()
    conn.close()

    print(f"Sample database created successfully at:")
    print(DB_PATH)


if __name__ == "__main__":
    setup()