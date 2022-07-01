import os
from fastapi import Depends, HTTPException, status
from typing import Union
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import HTTPBearer  
import string, random

from ...settings import config
from ...dependencies import common as CDepends
from ...models import common as CModel
from ...schemas import common as CSchemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
token_auth_scheme = HTTPBearer()

def reset_password_token(size=24, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def verify_password(plain_password, password):
    return pwd_context.verify(plain_password, password)

def get_password_hash(password):
    return pwd_context.hash(password)
   
def get_user(email: str):
    try:
        existing_user = CModel.User.get(CModel.User.email == email)
        return existing_user
    except:
        return False

def get_user_by_id(id: int):
    try:
        existing_user = CModel.User.get(CModel.User.id == id)
        return existing_user
    except:
        return False


def authenticate_user(email: str, password: str, dependencies=[Depends(CDepends.get_db)]):
    user = get_user(email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Union[timedelta , None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.settings.secret_key, algorithm=config.settings.algorithm)
    return encoded_jwt

def save_access_token(user, expires_in):
    access_token = create_access_token(data={"sub": user.email}, expires_delta=expires_in)
    token = CModel.Token(owner_id = user, token= access_token)
    token.save()
    return access_token


def get_user_data(user_id: int):
    return CModel.User.filter(CModel.User.id == user_id).first()

async def get_current_user(token: str = Depends(token_auth_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, config.settings.secret_key, algorithms=[config.settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = CSchemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: CSchemas.User = Depends(get_current_user)):
    if not current_user.isActive:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def create_user(user: CSchemas.UserCreate):
    fake_hashed_password = get_password_hash(user.password)
    db_user = CModel.User(
        firstName= user.firstName,
        lastName= user.lastName,
        email=user.email,
        password=fake_hashed_password,
        changedPassword= user.changedPassword,
        changedEmail= user.changedEmail,
        upline= user.upline,
        downline= user.downline,
        tree= user.tree,
        kyc= user.kyc,
        product = user.product,
        marketingCampaign= user.marketingCampaign,
        isActive =0, 
        role=2
        )
    db_user.save()
    return db_user