from fastapi import Depends, FastAPI, Request, HTTPException, status
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
from application.user.routers.operations.user_crud import get_current_active_user, get_current_userS

from .admin import main as admin_root
from .user import main as user_root
app = FastAPI()

token_auth_scheme = HTTPBearer()

app.mount("/api", user_root.app)
app.mount("/admin", admin_root.app)
# app.mount("/static", StaticFiles(directory="static"), name="static", Depends=(get_current_active_user))


async def verify_username(request: Request) :
    # print('ok')
    token = None
    user = None
    for x in request.scope['headers']:
        if x[0] == b'authorization':
            token = x[1].decode("utf-8")
    if token != None:
        user = await get_current_userS(token)
    else: 
        print('Not getting token')
    if user != None:
        # print(user.id)
        if request.scope['path'].startswith('/'+str(user.id)):
            # print('ok path')
            return True
        else:
            # print('/'+str(user.id))
            return False
    else:
        return False
    # [print(x[1]) if x[0] == b'authorization' else 'pass' for x in request.scope['headers']]
    # print(request.scope['path'])
    # print(token)
    # credentials = await security(request)

    # correct_username = secrets.compare_digest(credentials.username, "user")
    # correct_password = secrets.compare_digest(credentials.password, "password")
    # if not (correct_username and correct_password):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Incorrect email or password",
    #         headers={"WWW-Authenticate": "Basic"},
    #     )
    return True


class AuthStaticFiles(StaticFiles):
    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)

    async def __call__(self, scope, receive, send) -> None:
        # print('ok')
        assert scope["type"] == "http"

        request = Request(scope, receive)
        is_user = await verify_username(request)
        # print(get_current_active_user)
        # print('ok')
        if is_user:
            await super().__call__(scope, receive, send)
# print(Path(__file__).parent.parent)
# AuthStaticFiles()
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
