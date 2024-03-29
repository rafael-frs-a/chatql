from datetime import datetime
from dotenv import load_dotenv
from src import config


def load_env() -> bool:
    return load_dotenv(".env")


def now() -> datetime:
    return datetime.now(config.TIMEZONE)
