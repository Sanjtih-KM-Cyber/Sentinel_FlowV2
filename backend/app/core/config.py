from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AEGIS Security Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "NOT_A_SECRET_CHANGE_IN_PRODUCTION"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    ALGORITHM: str = "HS256"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "aegis_db"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    REDIS_URL: Optional[str] = None
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 5
    
    ALLOWED_ORIGINS: list[str] = ["http://localhost", "http://localhost:3000"]

    class Config:
        case_sensitive = True
        env_file = ".env"

    def get_database_uri(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

settings = Settings()
