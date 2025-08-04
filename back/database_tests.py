from sqlalchemy import text, inspect
from back.database import create_test_data, get_db_engine
from back.db_models import Base


def test_connection() -> None:
    """
    Read README.md to know how to make it work!
    Works with both PostgreSQL and SQLite.
    """
    engine = get_db_engine()
    with engine.connect() as conn:
        try:
            # Try a PostgreSQL-specific query to list tables
            res = conn.execute(text("SELECT table_name from information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema = 'public'"))
            print(res.all())
        except Exception:
            # Fallback to SQLAlchemy inspector for SQLite or generic backends
            insp = inspect(conn)
            print(insp.get_table_names())


def test_recreate_db_tables() -> None:
    engine = get_db_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(engine)
    create_test_data(engine)


# Run the test_recreate_db_tables function when this script is executed directly
if __name__ == "__main__":
    test_recreate_db_tables()
