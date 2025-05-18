import os
from typing import Literal, Optional # Added Optional
from pydantic_settings import BaseSettings, SettingsConfigDict # Import SettingsConfigDict
from functools import lru_cache # Good practice for get_settings

# No need for load_dotenv if pydantic-settings is handling .env
# from dotenv import load_dotenv
# load_dotenv() # pydantic-settings handles this via model_config

class CoreSettings(BaseSettings):
    ENV: Literal["development", "production"] = "development"
    DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8080
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARN", "ERROR", "FATAL"] = "DEBUG"

    # Central place for model_config to handle .env and extra fields
    # This will be inherited by the final Settings class.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra environment variables not defined in the models
    )

class TestSettings(BaseSettings):
    PYTEST: bool = False
    PYTEST_UNIT: bool = False
    model_config = SettingsConfigDict(extra="ignore") # Also allow ignore here

class DatabaseSettings(BaseSettings):
    # This default is for local non-Docker. Docker will override via environment.
    SQLALCHEMY_POSTGRES_URI: str = "postgresql+asyncpg://nam:thangcho@localhost:5432/codemate"
    SQLALCHEMY_ECHO: bool = False
    model_config = SettingsConfigDict(extra="ignore")

class RedisSettings(BaseSettings):
    # This default is for local non-Docker. Docker will override.
    REDIS_URL: str = "redis://localhost:6379"
    model_config = SettingsConfigDict(extra="ignore")

class Neo4jSettings(BaseSettings):
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    model_config = SettingsConfigDict(extra="ignore")

class GoogleGenAISettings(BaseSettings):
    GOOGLE_GENAI_API_KEY: Optional[str] = None # Make optional if not always present
    GEMINI_API_KEY: Optional[str] = None       # Make optional
    model_config = SettingsConfigDict(extra="ignore")

class OpenAISettings(BaseSettings):
    OPENAI_API_KEY: str = "" # Or Optional[str] = None
    model_config = SettingsConfigDict(extra="ignore")

class EmailSettings(BaseSettings):
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None
    MAIL_PORT: Optional[int] = 587
    MAIL_SERVER: Optional[str] = "smtp.gmail.com"
    MAIL_STARTTLS: Optional[bool] = True
    MAIL_SSL_TLS: Optional[bool] = False
    USE_CREDENTIALS: Optional[bool] = True
    model_config = SettingsConfigDict(extra="ignore")

class JWTSettings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_SECRET_KEY: str
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    model_config = SettingsConfigDict(extra="ignore")

class ExcelLinkSettings(BaseSettings):
    EXCEL_FILE_PATH: Optional[str] = None # Make optional if not always critical
    model_config = SettingsConfigDict(extra="ignore")

class GoogleAPISettings(BaseSettings): # Renamed for clarity
    CLIENT_AUTH: Optional[str] = None
    GOOGLE_API_URL: Optional[str] = "https://www.googleapis.com/auth/drive.file"
    model_config = SettingsConfigDict(extra="ignore")

class AWS3Settings(BaseSettings):
    AWS3_ACCESS_KEY_ID: Optional[str] = None
    AWS3_SECRET_ACCESS_KEY: Optional[str] = None
    AWS3_REGION: Optional[str] = None
    AWS3_BUCKET_NAME: Optional[str] = None
    model_config = SettingsConfigDict(extra="ignore")

class Judge0Settings(BaseSettings):
    # JUDGE0_URL is not in your .env, RAPIDAPI_KEY is
    RAPIDAPI_KEY: Optional[str] = None
    # Defaults if you want them, but better to load from .env if they are there
    # JUDGE0_URL: str = "https://judge0-ce.p.rapidapi.com"
    # RAPIDAPI_HOST: str = "judge0-ce.p.rapidapi.com"
    model_config = SettingsConfigDict(extra="ignore")

# The final Settings class will inherit model_config from CoreSettings (and others if they also define it,
# but the first one in MRO with a complete config usually takes precedence for common keys like 'extra').
# It's good practice for the MAIN settings accumulator to define its own comprehensive model_config.
class Settings(
    CoreSettings, # CoreSettings already has a model_config
    TestSettings,
    DatabaseSettings,
    RedisSettings,
    EmailSettings,
    JWTSettings,
    ExcelLinkSettings,
    GoogleAPISettings, # Renamed
    Neo4jSettings,
    GoogleGenAISettings,
    OpenAISettings,
    AWS3Settings,
    Judge0Settings
):
    # You can define a specific model_config here too, it will override/merge.
    # For simplicity, relying on CoreSettings' model_config is fine if it covers the .env loading.
    # If you want to be explicit for the combined class:
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class DevelopmentSettings(Settings):
    # Development specific overrides can go here
    # DEBUG is already True in CoreSettings, LOG_LEVEL is already DEBUG
    SQLALCHEMY_ECHO: bool = True # Example override

class ProductionSettings(Settings):
    DEBUG: bool = False
    LOG_LEVEL: Literal["INFO", "WARN", "ERROR", "FATAL"] = "INFO" # Example override

@lru_cache() # Cache the settings object
def get_settings() -> Settings:
    env = os.getenv("ENV", "development")
    if env == "development":
        return DevelopmentSettings()
    elif env == "production":
        return ProductionSettings()
    # Fallback or raise an error for unknown ENV
    raise ValueError(f"Unknown ENV value: {env}. Expected 'development' or 'production'.")

settings = get_settings()