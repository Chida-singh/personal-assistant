import os
from sqlmodel import SQLModel, create_engine, Session

# Get the DB URL from the environment (defaulting to a local sqlite for quick testing if Postgres isn't ready)
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "sqlite:///./todos.db"
)

# Convert postgres:// to postgresql:// for SQLAlchemy if necessary
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Connect args needed for SQLite, ignored by Postgres
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def create_db_and_tables():
    # In a production app with Alembic, we wouldn't use this directly, 
    # but for this iteration, it automatically creates the tables.
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
