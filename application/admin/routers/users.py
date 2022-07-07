from fastapi import Depends, Request, APIRouter, BackgroundTasks
from fastapi_mail import FastMail, MessageSchema
from ..dependencies import common as CDepends
from ..schemas import common as CSchemas
from ...user.settings import config
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

def get_user_by_id(id: int):
    try:
        existing_user = User.get(User.id == id)
        return existing_user
    except:
        return False


def send_mail(user, mail_subject, html_file, background_tasks):
    try:
        template_data = {
            "user": user.email
        }
        message = MessageSchema(
            subject=mail_subject,
            recipients=[user.email],  # List of recipients, as many as you can pass 
            template_body=template_data,
            )
        fm = FastMail(config.conf)
        async def sendMail():
            await fm.send_message(message, template_name= html_file+".html")
        background_tasks.add_task(sendMail)
        print('Email sent')
        # return {"status": "success", "message": "Reset password link sent to your email"}
    except:
        print('Email not sent')
        # return {"status": "error", "message": "Something went wrong"}

@router.get("/auth_user_kyc/{user_id}/{is_accept}")
def get_users(user_id: int, is_accept: str, background_tasks: BackgroundTasks):
    user = get_user_by_id(user_id)
    if is_accept == "accept".lower():
        if user :
            user.kyc = True
            user.save()
            mail_subject = "KYC request is accepted"
            send_mail(user, mail_subject, 'accept_kyc', background_tasks)
            return {"status":"success", "message":"KYC authenticated"}
        else :
            return {"status":"error", "message":"User not found"}
    else:
        mail_subject = "KYC request is rejected"
        send_mail(user, mail_subject, 'reject_kyc', background_tasks)
        return {"status":"success", "message":"KYC not authenticated"}