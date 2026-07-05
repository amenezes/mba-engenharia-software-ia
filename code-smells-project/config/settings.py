import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-only-change-me"
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    DATABASE_PATH = os.environ.get("DATABASE_URL", "sqlite:///loja.db").replace(
        "sqlite:///", ""
    )
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", "8"))
