import os


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    if value not in {"true", "false", "1", "0", "yes", "no", "on", "off"}:
        raise ValueError(f"{name} must be true or false")
    return value in {"true", "1", "yes", "on"}


class Settings:
    app_name = "Home Network Inventory"
    app_host = os.getenv("APP_HOST", "127.0.0.1")
    app_port = int(os.getenv("APP_PORT", "8420"))
    database_url = os.getenv("DATABASE_URL", "sqlite:///./home_network.db")
    session_secret = os.getenv("SESSION_SECRET", "")
    if len(session_secret.strip()) < 32:
        raise ValueError("Set SESSION_SECRET to a random string of at least 32 characters")
    session_https_only = env_bool("SESSION_HTTPS_ONLY", True)

    session_timeout_seconds = int(os.getenv("SESSION_TIMEOUT_SECONDS", "7200"))

settings = Settings()

