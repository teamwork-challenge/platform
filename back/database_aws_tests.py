from database import get_db_engine
from sqlalchemy import text

from back.models_orm import Base


def test_connection():
    """
    Read README.md to know how to make it work!
    """
    engine = get_db_engine()
    with engine.connect() as conn:
        # Check if the connection is successful
        res = conn.execute(text("SELECT table_name from information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema = 'public'"))
        print(res.all())

def recreate_db_tables():
    engine = get_db_engine()
    Base.metadata.create_all(engine)
