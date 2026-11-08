import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        env_file_encoding="utf-8",
    )
    database_url: str
    jwt_secret: str
    token_hours: int = 12
    token_hours_remember: int = 720
    # Первый администратор создаётся сидом, только если заданы оба значения
    admin_email: str | None = None
    admin_password: str | None = None
    admin_full_name: str = "Администратор"
