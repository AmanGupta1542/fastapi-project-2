from pydantic import BaseSettings
from pathlib import Path
from fastapi_mail import ConnectionConfig
class Settings(BaseSettings):
    app_name: str = "Fast API"
    admin_email: str = "aman@mistpl.com"
    
    database_name: str
    user : str
    password : str
    host : str
    port : str

    secret_key : str
    algorithm : str
    access_token_expire_minutes : str

    class Config:
        env_file = ".env"

settings = Settings()

conf = ConnectionConfig(
    MAIL_USERNAME = "amangupta1542@gmail.com",
    MAIL_PASSWORD = "ofeasqzmvrjcsxaf",
    MAIL_FROM = "amangupta1542@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_FROM_NAME="Aman Gupta",
    MAIL_TLS = True,
    MAIL_SSL = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True,
    TEMPLATE_FOLDER = Path(__file__).parent / 'templates'
)