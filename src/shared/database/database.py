# From .env file
import os

from sqlmodel import SQLModel, Session, create_engine

DB_ADDRESS = os.getenv("DB_ADDRESS")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(
  f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_ADDRESS}:{DB_PORT}/{DB_NAME}",
  connect_args={"connect_timeout": 10},
)


def get_session():
  with Session(engine) as session:
    yield session
