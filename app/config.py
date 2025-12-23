from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Fetcher(BaseSettings):
    base_url: str = "https://voe.com.ua/disconnection/detailed"

    cookie: str | None = None

    accept_encoding: dict[str, str] = {"Accept-Encoding": "gzip, deflate, br"}
    accept_language: dict[str, str] = {
        "Accept-Language": "en-US,en-GB;q=0.9,en;q=0.8,uk-UA;q=0.7,uk;q=0.6,ru-RU;q=0.5,ru;q=0.4"
    }
    user_agent: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    }

    @computed_field
    @property
    def headers(self) -> dict[str, str]:
        headers = {**self.accept_encoding, **self.accept_language, **self.user_agent}
        return headers


class Flare(BaseSettings):
    url: str = "http://flaresolver:8191/v1"
    operating_mode: Literal["cookie", "proxy"] = "proxy"
    session: str = "voe-session"


class Notification(BaseSettings):
    interval: int = 900


class Redis(BaseSettings):
    host: str = "redis"
    port: int = 6379
    db: int = 0
    username: str = "default"
    password: str | None = None


class Webhook(BaseSettings):
    url: str = "http://googlecloudrun.com"
    path: str = "/webhook"
    secret_token: str | None = None
    port: int = 8080

    @computed_field
    @property
    def full_url(self) -> str:
        return f"{self.url}{self.path}"
    
class Messages_Loading(BaseSettings):
    loading_city: str = "Завантаження міст..."
    loading_street: str = "Завантаження вулиць..."
    loading_house: str = "Завантаження будинків..."
    
    loading_schedule: str = "Завантаження графіка відключень..."


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_nested_delimiter="__",
    )

    bot_token: str | None = None
    bot_mode: Literal["polling", "webhook"] = "polling"

    admin_id: int | None = None

    fetcher: Fetcher = Fetcher()
    redis: Redis = Redis()
    flare: Flare = Flare()
    notification: Notification = Notification()
    webhook: Webhook = Webhook()
    messages_loading: Messages_Loading = Messages_Loading()

settings = Settings()
