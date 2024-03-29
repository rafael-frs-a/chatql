from src import config


def test_config() -> None:
    assert config.APP_NAME
    assert config.TIMEZONE
    assert config.SECRET_KEY
    assert config.ALLOWED_ORIGINS
    assert config.JWT_ALGORITHM
    assert config.ACCESS_TOKEN_EXP_SECONDS
    assert config.REFRESH_TOKEN_EXP_SECONDS
    assert config.PUB_SUB_URL
    assert config.DB_CONNECTION_STRING
    assert config.DB_NAME
