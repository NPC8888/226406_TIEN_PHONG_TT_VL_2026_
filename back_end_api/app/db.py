import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

def build_database_url():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    mysql_host = os.getenv("MYSQL_HOST")
    mysql_port = os.getenv("MYSQL_PORT", "3306")
    mysql_user = os.getenv("MYSQL_USER")
    mysql_password = os.getenv("MYSQL_PASSWORD")
    mysql_database = os.getenv("MYSQL_DATABASE")

    required_values = {
        "MYSQL_HOST": mysql_host,
        "MYSQL_USER": mysql_user,
        "MYSQL_PASSWORD": mysql_password,
        "MYSQL_DATABASE": mysql_database,
    }
    missing_keys = [key for key, value in required_values.items() if not value]
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise RuntimeError(
            f"Missing database configuration. Set DATABASE_URL or provide these .env values: {missing}"
        )

    return f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"


DATABASE_URL = build_database_url()

engine = create_engine(DATABASE_URL, future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
