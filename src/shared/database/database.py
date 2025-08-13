from sqlmodel import SQLModel, Session, create_engine
from src.shared.config.config import get_settings

settings = get_settings()

engine = create_engine(
  settings.database_url,
  connect_args={"connect_timeout": 10},
)


def get_session():
  with Session(engine) as session:
    yield session
