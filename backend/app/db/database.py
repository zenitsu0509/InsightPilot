from datetime import datetime, timedelta
import random

from sqlalchemy import create_engine, MetaData, inspect, text

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
metadata = MetaData()


def ensure_sales_dataset():
    inspector = inspect(engine)
    if inspector.has_table("sales"):
        return

    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
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
            """
        )

        categories = ["Electronics", "Clothing", "Home", "Books"]
        products = {
            "Electronics": ["Laptop", "Smartphone", "Headphones", "Monitor"],
            "Clothing": ["T-Shirt", "Jeans", "Jacket", "Sneakers"],
            "Home": ["Sofa", "Table", "Lamp", "Rug"],
            "Books": ["Fiction", "Non-Fiction", "Sci-Fi", "Biography"],
        }
        regions = ["North", "South", "East", "West"]

        rows = []
        start_date = datetime(2023, 1, 1)
        for _ in range(365):
            date = start_date + timedelta(days=random.randint(0, 364))
            category = random.choice(categories)
            product = random.choice(products[category])
            quantity = random.randint(1, 10)
            unit_price = round(random.uniform(10.0, 1200.0), 2)
            total_amount = round(quantity * unit_price, 2)
            region = random.choice(regions)

            rows.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "product_category": category,
                    "product_name": product,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_amount": total_amount,
                    "region": region,
                }
            )

        conn.execute(
            text(
                """
                INSERT INTO sales (date, product_category, product_name, quantity, unit_price, total_amount, region)
                VALUES (:date, :product_category, :product_name, :quantity, :unit_price, :total_amount, :region)
                """
            ),
            rows,
        )


ensure_sales_dataset()


def get_db_schema():
    metadata.reflect(bind=engine)
    schema_info = []
    for table in metadata.tables.values():
        columns = [f"{col.name} ({col.type})" for col in table.columns]
        schema_info.append(f"Table: {table.name}\nColumns: {', '.join(columns)}")
    return "\n\n".join(schema_info)
