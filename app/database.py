from sqlmodel import SQLModel, Session, create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///travelintel.db")

# For SQLite, use the file in the project root
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "travelintel.db")
engine = create_engine(f"sqlite:///{db_path}", echo=False)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
