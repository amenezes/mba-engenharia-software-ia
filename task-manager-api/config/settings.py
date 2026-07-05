import os

from dotenv import load_dotenv

load_dotenv()


def _require_env(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise RuntimeError(f"Variável de ambiente obrigatória não definida: {key}")
    return val


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-only-change-me"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///tasks.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", "8"))

    SEED_ADMIN_PASSWORD = _require_env("SEED_ADMIN_PASSWORD")
    SEED_USER_PASSWORD = _require_env("SEED_USER_PASSWORD")
    SEED_MANAGER_PASSWORD = _require_env("SEED_MANAGER_PASSWORD")
