from pydantic_settings import SettingsConfigDict, BaseSettings

class Fetcher(BaseSettings):
    
    base_url: str = "https://voe.com.ua/disconnection/detailed"
    
    cookie: str | None = None
    user_agent: dict[str, str] = {
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en-GB;q=0.9,en;q=0.8,uk-UA;q=0.7,uk;q=0.6,ru-RU;q=0.5,ru;q=0.4",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    }

    

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_nested_delimiter="__",
    )

    bot_token: str | None = None
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None

    fetcher: Fetcher = Fetcher()


settings = Settings()