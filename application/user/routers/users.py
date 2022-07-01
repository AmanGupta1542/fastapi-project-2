import csv
from fastapi import APIRouter, Depends, HTTPException, Path, status, Body, BackgroundTasks
from fastapi_mail import FastMail, MessageSchema
from fastapi.requests import Request
from typing import List, Union, Any
from datetime import datetime, timedelta, timezone
from pydantic import EmailStr
import pytz
from pydantic import BaseModel

from ..dependencies import common as CDepends
from ..schemas import common as CSchemas
from ..settings import config
from .operations import user_crud as UserO
from ..models import common as CModels

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(CDepends.get_db)],
    responses={404: {"description": "Not found"}},
)

@router.post("/login", response_model=CSchemas.Token)
def login(login_data: CSchemas.LoginData = Body()):
    user = UserO.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_tokens_list = user.token.select().dicts()
    is_token_exist = True if len(user_tokens_list) > 0 else False
    if not is_token_exist:
        access_token = UserO.save_access_token(user, timedelta(minutes=15))
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        last_created_token = user_tokens_list[-1]['token']
        token_time = datetime.now(timezone.utc) - user_tokens_list[-1]['createdAt'].astimezone(pytz.UTC)

        if token_time.total_seconds()/60 > 15:
            token_for_del = CModels.Token.delete().where(CModels.Token.owner_id == user.id)
            token_for_del.execute()
            access_token = UserO.save_access_token(user, timedelta(minutes=15))
            return {"access_token": access_token, "token_type": "bearer"}
        else:
            return {"access_token": last_created_token, "token_type": "bearer"}

@router.post("/logout")
def logout(user_id: int = Body()):
    token_for_del = CModels.Token.delete().where(CModels.Token.owner_id == user_id)
    token_for_del.execute()
    return {"message": "logout successful"}

@router.get(
    "/{user_id}", response_model=CSchemas.User, dependencies=[Depends(CDepends.get_db)]
)
def read_user(user_id: int, current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    db_user = UserO.get_user_data(user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if current_User.id != db_user.id:
        raise HTTPException(status_code=400, detail="Can't access this user")
    return db_user

@router.post("/register", response_model=CSchemas.User, dependencies=[Depends(CDepends.get_db)])
def create_user(user: CSchemas.UserCreate):
    db_user = UserO.get_user(email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return UserO.create_user(user=user)

@router.post("/forget-password")
async def forget_password(request: Request, background_tasks: BackgroundTasks, data: CSchemas.UserBase):
    db_user = UserO.get_user(email=data.email)
    if not db_user:
        # raise HTTPException(status_code=400, detail="Email not found")
        return {"status": "error", "message": "Email not found"}
    else:
        try:
            token = UserO.reset_password_token()
            create_token = CModels.ResetPasswordToken(owner = db_user, token= token)
            create_token.save()
            message = MessageSchema(
                subject="Reset Your Password",
                recipients=[data.email],  # List of recipients, as many as you can pass 
                # body="<a href='http://127.0.0.1:8000/api/reset-password/"+token+"'>Click Here</a>",
                body="{}/api/reset-password/{}".format(request.client.host, token),
                subtype="html"
                )
            fm = FastMail(config.conf)
            background_tasks.add_task(fm.send_message,message)

            return {"status": "success", "message": "Reset password link sent to your email"}
        except: 
            return {"status": "error", "message": "Something went wrong"}

@router.patch("/reset-password/{token}")
def reset_password(data: CSchemas.ResetPassword, token: str = Path(max_length=24)):
    try:
        user_token = CModels.ResetPasswordToken.get(CModels.ResetPasswordToken.token == token)
    except:
        return {"status": "error", "message": "Invalid Token"}

    if (datetime.now() - user_token.createdAt).days >= 1 or user_token.isExpire:
        return {"status": "error", "message": "Token expires"}
    else:
        user = UserO.get_user_by_id(user_token.owner)
        user.password = UserO.get_password_hash(data.password)
        user.save()
        user_token.isExpire = True
        user_token.save()
        return {"status": "success", "message": "Password reset successfully"}