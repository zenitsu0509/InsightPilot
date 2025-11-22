import sqlite3
import pandas as pd
import random
from datetime import datetime, timedelta

def create_dummy_db():
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    
    # Create Sales Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE,
        product_category TEXT,
        product_name TEXT,
        quantity INTEGER,
        unit_price REAL,
        total_amount REAL,
        region TEXT
    )
    ''')
    
    # Generate sample data
    categories = ['Electronics', 'Clothing', 'Home', 'Books']
    products = {
        'Electronics': ['Laptop', 'Smartphone', 'Headphones', 'Monitor'],
        'Clothing': ['T-Shirt', 'Jeans', 'Jacket', 'Sneakers'],
        'Home': ['Sofa', 'Table', 'Lamp', 'Rug'],
        'Books': ['Fiction', 'Non-Fiction', 'Sci-Fi', 'Biography']
    }
    regions = ['North', 'South', 'East', 'West']
    
    data = []
    start_date = datetime(2023, 1, 1)
    for i in range(100):
        date = start_date + timedelta(days=random.randint(0, 365))
        category = random.choice(categories)
        product = random.choice(products[category])
        quantity = random.randint(1, 5)
        unit_price = round(random.uniform(10.0, 1000.0), 2)
        total_amount = round(quantity * unit_price, 2)
        region = random.choice(regions)
        
        data.append((date.strftime('%Y-%m-%d'), category, product, quantity, unit_price, total_amount, region))
        
    cursor.executemany('''
    INSERT INTO sales (date, product_category, product_name, quantity, unit_price, total_amount, region)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', data)
    
    conn.commit()
    conn.close()
    print("Dummy database created successfully.")

if __name__ == "__main__":
    create_dummy_db()
