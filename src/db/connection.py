from sqlalchemy import create_engine
from config import DB_PATH

def get_engine():
    """Returns a SQLAlchemy engine connected to the SQLite database."""
    engine = create_engine(DB_PATH)
    return engine
