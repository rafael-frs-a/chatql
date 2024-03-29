import os
from datetime import UTC
from src import utils

utils.load_env()

# App
APP_NAME = "ChatQL - API"
TIMEZONE = UTC

# API
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXP_SECONDS = 30 * 60  # 30 minutes
REFRESH_TOKEN_EXP_SECONDS = 1 * 60 * 60  # 1 hour
PUB_SUB_URL = os.getenv("PUB_SUB_URL", "memory://")

# Database
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING", "")
DB_NAME = os.getenv("DB_NAME", "")
