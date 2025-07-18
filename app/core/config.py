from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Backend"
    
    # Database configuration
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # PostgreSQL specific settings (used when DATABASE_URL is not set)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "fastapi_db"
    POSTGRES_USER: str = "fastapi_user"
    POSTGRES_PASSWORD: str = "fastapi_password"
    USE_POSTGRES: bool = False
    
    @property
    def get_database_url(self) -> str:
        """Get database URL, preferring environment variable or constructing from components"""
        if self.DATABASE_URL != "sqlite:///./app.db":
            return self.DATABASE_URL
        
        # If using PostgreSQL, construct the URL
        if self.USE_POSTGRES:
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
        return self.DATABASE_URL

    class Config:
        env_file = ".env"

settings = Settings() 