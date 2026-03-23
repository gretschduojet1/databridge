from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    All configuration comes from environment variables.
    Pydantic reads them automatically — no manual os.getenv() calls needed.

    In Docker, these are set in docker-compose.yml under `environment:`.
    Locally, you can put them in a .env file and pydantic reads that too.
    """

    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"  # optional local override, ignored if file doesn't exist


# Single shared instance — import this anywhere you need config
settings = Settings()
