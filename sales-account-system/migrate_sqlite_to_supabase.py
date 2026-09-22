"""Migrate the local SQLite database into the PostgreSQL database in DATABASE_URL.

Run this only when DATABASE_URL points to Supabase and the destination database
is empty or contains no rows from this application.
"""

import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from src.database import Base, create_tables, engine as target_engine
from src import models  # noqa: F401 - registers every model with Base.metadata


SOURCE_DATABASE_URL = os.environ.get(
    "SOURCE_DATABASE_URL",
    "sqlite:///data/sales_accounts.db",
)


def table_count(engine, table_name: str) -> int:
    with engine.connect() as connection:
        return connection.execute(
            text(f'SELECT COUNT(*) FROM "{table_name}"')
        ).scalar_one()


def migrate() -> None:
    if not SOURCE_DATABASE_URL.startswith("sqlite"):
        raise RuntimeError("SOURCE_DATABASE_URL must point to SQLite.")

    if target_engine.url.get_backend_name() == "sqlite":
        raise RuntimeError(
            "DATABASE_URL must point to Supabase PostgreSQL, not SQLite."
        )

    source_path = Path("data/sales_accounts.db")
    if not source_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {source_path}")

    source_engine = create_engine(SOURCE_DATABASE_URL)
    create_tables()

    source_tables = set(inspect(source_engine).get_table_names())
    target_tables = set(inspect(target_engine).get_table_names())
    table_names = [
        table.name
        for table in Base.metadata.sorted_tables
        if table.name in source_tables and table.name in target_tables
    ]

    if not table_names:
        raise RuntimeError("No matching application tables were found.")

    counts = {
        table_name: table_count(source_engine, table_name)
        for table_name in table_names
    }
    print("Source row counts:")
    for table_name, count in counts.items():
        print(f"  {table_name}: {count}")

    with source_engine.connect() as source_connection:
        source_rows = {
            table_name: source_connection.execute(
                text(f'SELECT * FROM "{table_name}"')
            ).mappings().all()
            for table_name in table_names
        }

    with Session(target_engine) as session:
        for table_name in table_names:
            rows = source_rows[table_name]
            if rows:
                session.execute(
                    Base.metadata.tables[table_name].insert(),
                    [dict(row) for row in rows],
                )
        session.commit()

    # PostgreSQL sequences do not automatically advance when explicit IDs are
    # inserted, so reset integer primary-key sequences to the current maximum.
    with target_engine.begin() as connection:
        for table_name in table_names:
            table = Base.metadata.tables[table_name]
            primary_keys = list(table.primary_key.columns)
            if len(primary_keys) != 1:
                continue
            primary_key = primary_keys[0]
            if primary_key.type.python_type is not int:
                continue
            sequence_name = f"{table_name}_{primary_key.name}_seq"
            connection.execute(
                text(
                    "SELECT setval('"
                    + sequence_name
                    + "', "
                    "COALESCE((SELECT MAX(\""
                    + primary_key.name
                    + "\") FROM \""
                    + table_name
                    + "\"), 1), true)"
                )
            )

    print("Migration completed successfully.")
    print("Destination row counts:")
    for table_name in table_names:
        print(f"  {table_name}: {table_count(target_engine, table_name)}")


if __name__ == "__main__":
    migrate()
