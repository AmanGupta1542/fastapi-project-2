from fastapi import FastAPI, Depends
from .routers import users, settings
from fastapi.security import HTTPBearer 

from ..user.routers.operations.user_crud import get_current_active_user
from ..user.dependencies.common import get_db
from .dependencies import common as CDepends

auth_admin = HTTPBearer()

app = FastAPI(dependencies=[Depends(get_db), Depends(CDepends.get_active_user)])

app.include_router(users.router)
app.include_router(settings.router)