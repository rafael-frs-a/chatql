from enum import Enum


class TokenType(str, Enum):
    ACCESS_TOKEN = "ACCESS_TOKEN"  # nosec
    REFRESH_TOKEN = "REFRESH_TOKEN"  # nosec
