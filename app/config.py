from functools import lru_cache
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str

    # jwt
    JWT_ACCESS_SECRET: str
    JWT_REFRESH_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    model_config = { 
        "env_file": ".env",      # Loads .env from project root
    }

@lru_cache() # ensures singleton-like access without repeated instantiation
def get_config() -> Config:
    return Config()