from fastapi import Depends, FastAPI
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from application.user.routers.operations.user_crud import get_current_active_user

from .admin import main as admin_root
from .user import main as user_root
app = FastAPI()

app.mount("/api", user_root.app)
app.mount("/admin", admin_root.app)
# app.mount("/static", StaticFiles(directory="static"), name="static", Depends=(get_current_active_user))

class AuthStaticFiles(StaticFiles):
    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)

    async def __call__(self, scope, receive, send) -> None:

        assert scope["type"] == "http"

        # request = Request(scope, receive)
        # await verify_username(request)
        get_current_active_user
        await super().__call__(scope, receive, send)
print(Path(__file__).parent.parent)
app.mount(
    "/static",
    AuthStaticFiles(directory=Path(__file__).parent.parent / "static"),
    name="static",
)

# try:
#     os.makedirs('static/a')
# except OSError as e:
#     print(e)

# if not os.path.exists('static/b'):
#     os.makedirs('static/b')
# else:
#     print('exist')


# import typing
# from pathlib import Path
# import secrets

# from fastapi import FastAPI, Request, HTTPException, status
# from fastapi.staticfiles import StaticFiles
# from fastapi.security import HTTPBasic, HTTPBasicCredentials


# PathLike = typing.Union[str, "os.PathLike[str]"]
# app = FastAPI()
# security = HTTPBasic()


# async def verify_username(request: Request) -> HTTPBasicCredentials:

#     credentials = await security(request)

#     correct_username = secrets.compare_digest(credentials.username, "user")
#     correct_password = secrets.compare_digest(credentials.password, "password")
#     if not (correct_username and correct_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Basic"},
#         )
#     return credentials.username


# class AuthStaticFiles(StaticFiles):
#     def __init__(self, *args, **kwargs) -> None:

#         super().__init__(*args, **kwargs)

#     async def __call__(self, scope, receive, send) -> None:

#         assert scope["type"] == "http"

#         request = Request(scope, receive)
#         await verify_username(request)
#         await super().__call__(scope, receive, send)


# app.mount(
#     "/static",
#     AuthStaticFiles(directory=Path(__file__).parent / "static"),
#     name="static",
# )
