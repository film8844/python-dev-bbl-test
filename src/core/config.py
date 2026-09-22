from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

AVAILABLE_SLOTS: tuple[str, ...] = (
    "09am-10am",
    "10am-11am",
    "11am-12pm",
    "01pm-02pm",
    "02pm-03pm",
    "03pm-04pm",
    "04pm-05pm",
)


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite:///database.db")
    jwt_secret: str = Field(default="dev-only-insecure-secret-change-me", min_length=32)
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration: int = Field(default=3600)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
