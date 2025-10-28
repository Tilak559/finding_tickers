import pydantic_settings
from pydantic_settings import BaseSettings

class config(BaseSettings):
    finnhub_api_key: str

    class Config:
        env_file = ".env"

config = config()