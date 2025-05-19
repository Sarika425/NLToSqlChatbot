# seed_data.py
import psycopg2

# Update these if your DB settings differ
DB_CONFIG = {
    "dbname": "custom",
    "user": "postgres",
    "password":  os.getenv("DB_PASSWORD", "postgres"),
    "host": "localhost",
    "port": 5434,
}

def seed_data():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS customers;

    CREATE TABLE customers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100),
        country VARCHAR(50)
    );

    CREATE TABLE orders (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER REFERENCES customers(id),
        product VARCHAR(100),
        amount NUMERIC,
        order_date DATE
    );

    INSERT INTO customers (name, email, country) VALUES
        ('Alice', 'alice@example.com', 'India'),
        ('Bob', 'bob@example.com', 'USA'),
        ('Charlie', 'charlie@example.com', 'UK');

    INSERT INTO orders (customer_id, product, amount, order_date) VALUES
        (1, 'Laptop', 1200.00, '2024-01-01'),
        (2, 'Smartphone', 800.00, '2024-01-15'),
        (1, 'Tablet', 400.00, '2024-02-10'),
        (3, 'Monitor', 300.00, '2024-03-05');
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Sample data inserted successfully.")

if __name__ == "__main__":
    seed_data()
