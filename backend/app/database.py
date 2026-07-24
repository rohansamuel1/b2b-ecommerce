from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./b2b_ecommerce.db")

engine_options = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, **engine_options)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def apply_compatibility_migrations():
    """Small idempotent migrations for the existing demo SQLite database."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    wanted = {
        "products": {"category_id": "INTEGER", "brand": "VARCHAR", "rating": "FLOAT DEFAULT 0", "attributes_json": "TEXT DEFAULT '{}'"},
        "orders": {"coupon_code": "VARCHAR", "discount_amount": "FLOAT DEFAULT 0"},
    }
    with engine.begin() as connection:
        inspector = inspect(connection)
        for table_name, columns in wanted.items():
            if table_name not in inspector.get_table_names():
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for name, sql_type in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {name} {sql_type}"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
