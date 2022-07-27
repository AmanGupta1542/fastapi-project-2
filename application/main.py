from fastapi import FastAPI, Request
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from application.user.routers.operations.user_crud import auth_user_staticfiles

from .admin import main as admin_root
from .user import main as user_root
from .ftp import main as ftp_root
app = FastAPI()

token_auth_scheme = HTTPBearer()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:4200",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

app.mount("/api", user_root.app)
app.mount("/admin", admin_root.app)
app.mount("/ftp", ftp_root.app)

app.mount("/staticfiles", StaticFiles(directory="staticfiles"), name="staticfiles")

async def verify_username(request: Request) :
    token = None
    user = None
    for x in request.scope['headers']:
        if x[0] == b'authorization':
            token = x[1].decode("utf-8")
    if token != None:
        user = await auth_user_staticfiles(token)
    else: 
        print('Not getting token')
    if user != None:
        if request.scope['path'].startswith('/'+str(user.id)):
            return True
        else:
            return False
    else:
        return False


class AuthStaticFiles(StaticFiles):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def __call__(self, scope, receive, send) -> None:
        assert scope["type"] == "http"
        request = Request(scope, receive)
        is_user = await verify_username(request)
        if is_user:
            await super().__call__(scope, receive, send)

app.mount(
    "/static",
    AuthStaticFiles(directory=Path(__file__).parent.parent / "static"),
    name="static",
)