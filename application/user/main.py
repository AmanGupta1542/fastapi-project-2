from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import metadata as meta, config
from .database import database
from .models.common import *
from .routers import users, neilbox

database.db.connect()
database.db.create_tables([User, UserKYC, TokenBlocklist, MailConfig, DatabaseConfig, ResetPasswordToken])
database.db.close()

app = FastAPI(
    # getting title from .env file
    title = config.settings.app_name,
    description = meta.description,
    version = meta.version,
    terms_of_service = meta.terms_of_service,
    contact = meta.contact,
    license_info = meta.license_info,
    openapi_tags= meta.tags_metadata,
    docs_url = meta.docs_url, 
    redoc_url = meta.redoc_url,
    openapi_url = meta.openapi_url
)


app.add_middleware(
    CORSMiddleware,
    allow_origins = meta.origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

app.include_router(users.router)
app.include_router(neilbox.router)

@app.get("/")
def root():
    return {"message": "working"}