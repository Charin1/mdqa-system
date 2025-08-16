import os
from sqlmodel import create_engine, SQLModel, Session
from ..core.settings import settings
from ..models import database # Import to ensure models are registered

# Ensure the directory for the SQLite database exists
db_dir = os.path.dirname(settings.SQLITE_PATH)
os.makedirs(db_dir, exist_ok=True)

# The file path for the SQLite database
sqlite_url = f"sqlite:///{settings.SQLITE_PATH}"
engine = create_engine(sqlite_url, echo=False)

def init_db():
    """Creates all database tables based on SQLModel metadata."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Provides a database session for dependency injection."""
    with Session(engine) as session:
        yield session