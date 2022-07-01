from fastapi import Depends, Request, APIRouter
from ..dependencies import common as CDepends
from ..schemas import common as CSchemas
from typing import Any , List
from passlib.context import CryptContext

from ...user.models.common import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(
    # dependencies=[Depends(CDepends.get_db)],
    responses={404: {"description": "Not found"}},
)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@router.get("/user-details", response_model=List[CSchemas.User])
def get_users(skip: int = 0, limit: int = 100, all_users: bool=False):
    if all_users :
        return list(User.select())
    else :
        return list(User.select().offset(skip).limit(limit))