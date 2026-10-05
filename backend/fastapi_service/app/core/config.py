from pathlib import Path
import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BASE_DIR.parent.parent
ENV_FILE = PROJECT_ROOT / '.env'
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    DB_NAME: str = 'smart_ecommerce'
    DB_USER: str = 'smart_ecommerce_app'
    DB_PASSWORD: str = 'SmartEcomApp123!'
    DB_HOST: str = '127.0.0.1'
    DB_PORT: int = 3306
    FASTAPI_SECRET_KEY: str = 'dev-fastapi-secret'
    JWT_SECRET_KEY: str = 'dev-fastapi-secret'
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    FASTAPI_BASE_URL: str = 'http://127.0.0.1:8000'
    FRONTEND_BASE_URL: str = 'http://localhost:3000'
    CORS_ORIGINS: list[str] = ['http://localhost:3000', 'http://127.0.0.1:3000']
    STRIPE_SECRET_KEY: str = ''
    STRIPE_WEBHOOK_SECRET: str = ''
    AUTH0_DOMAIN: str = ''
    AUTH0_AUDIENCE: str = ''
    GOOGLE_CLIENT_ID: str = ''
    FACEBOOK_APP_ID: str = ''
    SMTP_HOST: str = ''
    SMTP_PORT: int = 1025
    SMTP_USER: str = ''
    SMTP_PASSWORD: str = ''
    SMTP_FROM: str = 'no-reply@example.com'

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra='ignore')


settings = Settings()
