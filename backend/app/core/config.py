from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Default to localhost for local tools (Alembic), Docker overrides this via env var
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5433/ecommerce_db"
    SECRET_KEY: str = "changethis_secret_key_for_dev_only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
