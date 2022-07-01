from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta

from .settings import metadata as meta, config
from .database import database
from .models.common import *
from .routers import users, admin
from .routers.operations import user_crud
from .dependencies import common as CDepends
from .schemas import common as CSchemas


SECRET_KEY = config.settings.secret_key
ALGORITHM = config.settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = int(config.settings.access_token_expire_minutes)

database.db.connect()
database.db.create_tables([User, Token, MailConfig, DatabaseConfig, ResetPasswordToken])
database.db.close()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
app.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(CDepends.get_db)],
    responses={404: {"description": "Not found"}},
)

@app.get("/")
def root():
    return {"message": "working"}

# we can also define admin roots in this file
# @admin_root.app.get("/sub")
# def read_sub():
#     return {"message": "Hello World from sub API"}

    
# @app.post("/token", response_model=CSchemas.Token)
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = user_crud.authenticate_user(form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = user_crud.create_access_token(
#         data={"sub": user.email}, expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer"}
