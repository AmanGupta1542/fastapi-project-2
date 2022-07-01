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
    access_token = UserO.create_access_token(
        data={"sub": user.email}, 
        expires_delta=timedelta(minutes=config.settings.access_token_expire_minutes)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/logout")
def logout(current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    return {"status":"success", "message": "logout successful"}

@router.get(
    "/{user_id}", response_model=CSchemas.User, dependencies=[Depends(CDepends.get_db)]
)
def read_user(user_id: int, current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    db_user = UserO.get_user_by_id(user_id)
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
        raise HTTPException(status_code=400, detail="Email not found")
    else:
        try:
            token = UserO.reset_password_token()
            url = "{}/api/reset-password/{}".format(request.client.host, token)
            template_data = {"url": url}
            create_token = CModels.ResetPasswordToken(owner = db_user, token= token)
            create_token.save()
            message = MessageSchema(
                subject="Reset Your Password",
                recipients=[data.email],  # List of recipients, as many as you can pass 
                template_body=template_data,
                )
            fm = FastMail(config.conf)
            async def sendMail():
                await fm.send_message(message, template_name="email.html")
            background_tasks.add_task(sendMail)
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