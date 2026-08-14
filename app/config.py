import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    COGNO_URI: str = os.getenv("COGNO_URI", "bolt://localhost:7687")
    COGNO_USER: str = os.getenv("COGNO_USER", "cognodb")
    COGNO_PASSWORD: str = os.getenv("COGNO_PASSWORD", "password")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
