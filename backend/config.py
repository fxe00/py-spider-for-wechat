import os
from dataclasses import dataclass


@dataclass
class Settings:
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db: str = os.getenv("MONGO_DB", "wechat_spider")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MIN", "1440"))
    cors_allow_origin: str = os.getenv("CORS_ALLOW_ORIGIN", "*")
    scheduler_timezone: str = os.getenv("SCHEDULER_TZ", "Asia/Shanghai")
    default_admin_user: str = os.getenv("ADMIN_USER", "admin")
    default_admin_pass: str = os.getenv("ADMIN_PASS", "admin123")
    request_min_delay: float = float(os.getenv("REQUEST_MIN_DELAY", "1.0"))
    request_max_delay: float = float(os.getenv("REQUEST_MAX_DELAY", "2.0"))
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "10.0"))
    request_retries: int = int(os.getenv("REQUEST_RETRIES", "3"))


def get_settings() -> Settings:
    return Settings()
