import os
import pytz
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


timezonetash = pytz.timezone("Asia/Tashkent")

load_dotenv()



class Settings(BaseSettings):
    # Application settings
    app_name: str = "Finance Systems Project"
    version: str = "1.0.0"

    BASE_URL: str = os.getenv("BASE_URL")
    DB_URL: str = os.getenv("DB_URL")
    SQLALCHEMY_URL: str = os.getenv("SQLALCHEMY_URL")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
    ALGORITHM: str = os.getenv("ALGORITHM", 'HS256')
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    admin_role: str = os.getenv("ADMIN_ROLE")
    admin_password: str = os.getenv("ADMIN_PASSWORD")
    BOT_USER: str = os.getenv("BOT_USER")
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")

    # admin_role:str = os.getenv('ADMIN_ROLE')
    # admin_password:str = os.getenv('ADMIN_PASSWORD')


    class Config:
        env_file = ".env"  # Specify the environment file to load


# Initialize settings
settings = Settings()
