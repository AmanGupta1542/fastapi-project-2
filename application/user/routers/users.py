import os
import re
from fastapi import APIRouter, Depends, HTTPException, Path, status, Body, BackgroundTasks, Request, File, UploadFile
from fastapi_mail import FastMail, MessageSchema
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from typing import Union, List

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
def logout(request: Request, current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    try:
        CModels.TokenBlocklist(token=request.headers['Authorization'].split(' ')[-1].strip()).save()
        return {"status":"success", "message": "logout successful"}
    except:
        return {"status":"error", "message": "Internal server error"}

@router.get(
    "/profile", response_model=CSchemas.User, dependencies=[Depends(CDepends.get_db)]
)
def read_user(current_user: CSchemas.User = Depends(UserO.get_current_active_user)):
    db_user = UserO.get_user(current_user.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
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
            url = "{}/api/users/password-reset/{}".format(config.settings.domain, token)
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

@router.get("/password-reset/{token}")
def reset_password(token: str, request: Request):
    try:
        user_token = CModels.ResetPasswordToken.get(CModels.ResetPasswordToken.token == token)
    except:
        # return RedirectResponse(config.settings.protocol+"://"+config.settings.domain, status_code=307)
        # return {"status": "error", "message": "Invalid Token"}
        return config.templates.TemplateResponse("reset-password.html", {"request": request, "status": "error", "message": "Invalid Token", "domain": config.settings.protocol+"://"+config.settings.domain})

    if (datetime.now() - user_token.createdAt).days >= 1 or user_token.isExpire:
        # return RedirectResponse(config.settings.protocol+"://"+config.settings.domain, status_code=307)
        # return {"status": "error", "message": "Token expires"}
        return config.templates.TemplateResponse("reset-password.html", {"request": request, "status": "error", "message": "Token expires", "domain": config.settings.protocol+"://"+config.settings.domain})
    else:
        return config.templates.TemplateResponse("reset-password.html", {"request": request, "status": "success"})

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
        # return RedirectResponse(config.settings.protocol+"://"+config.settings.domain, status_code=307)
        return {"status": "success", "message": "Password reset successfully"}

@router.patch("/change-password")
def change_password(passwords: CSchemas.ChangePass, current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    is_password = UserO.verify_password(passwords.oldPassword, current_User.password)
    if is_password : 
        current_User.password = UserO.get_password_hash(passwords.newPassword)
        current_User.save()
        return {"status": "success", "message": "Password changes successfully"}
    else:
        return {"status": "error", "message": "Old password is not correct"}

@router.post("/kyc/")
async def create_upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    document_name: str,
    file: Union[UploadFile , None] = File(description="Getting file for kyc verificaiton", default=None),
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)
    ):
    if not file:
        return {"message": "No upload file sent"}
    elif not (file.content_type == "image/png" or file.content_type == "image/jpg" or file.content_type == "image/jpeg"):
        return {"status": "error", "message": "Only jpg, jpeg and png files are accepted."}
    else:
        # print(file.content_type)
        if not os.path.exists('static/'+str(current_User.id)):
            os.makedirs('static/'+str(current_User.id))
        with open ('static/'+str(current_User.id)+'/'+file.filename, 'wb+') as user_kyc_file:
            user_kyc_file.write(file.file.read())
        db_user = CModels.UserKYC(owner=current_User, KYCDocumentName= document_name, fileName = file.filename)
        db_user.save()

        try:
            template_data = {
                "user": current_User.email
            }
            message = MessageSchema(
                subject="Authenticate user KYC",
                recipients=[config.settings.admin_email],  # List of recipients, as many as you can pass 
                template_body=template_data,
                attachments=[
                    {
                        "file": 'static/'+str(current_User.id)+'/'+file.filename,
                        "headers": {"Content-ID": "<KYC_document>"},
                        # "mime_type": "image",
                        # "mime_subtype": "png",
                    }
                ],
                )
            fm = FastMail(config.conf)
            async def sendMail():
                await fm.send_message(message, template_name="auth_kyc.html")
            background_tasks.add_task(sendMail)
            print('Email sent')
            # return {"status": "success", "message": "Reset password link sent to your email"}
        except:
            print('Email not sent')
            # return {"status": "error", "message": "Something went wrong"}

        return {"status":"success", "message":"Document upload successfully", "document_name": file.filename}


# def get_user_dir(user_id:int, file_name:str):
#     if not os.path.exists('static/'+str(user_id)):
#         os.makedirs('static/'+str(user_id))
#     if not os.path.exists('static/'+str(user_id)+'/'+str(file_name)):
#         os.makedirs('static/'+str(user_id)+'/'+str(file_name))
#         return True # id requested directory not exist
#     else:
#         return False # id requested directory already exist
#     with open ('static/'+str(user_id)+'/'+file.filename, 'wb+') as user_kyc_file:
#         user_kyc_file.write(file.file.read()) 

# def is_dir_exist(user_id: int, dir_name: str):
#     if os.path.exists('static/'+str(user_id)):
#         if os.path.exists('static/'+str(user_id)+'/'+str(dir_name)):
#             return True
#         else: 
#             return False
#     return False


# @router.post("/create-directory/{dir_name}")
# def create_directory(dir_name: str, current_User: CSchemas.User = Depends(UserO.get_current_active_user) ):
#     # /\:*?""<>|
#     pattern = '[:*?"<>/\|]'
#     # pattern = re.compile('[/\:*?"<>|]')
#     # if(pattern.search(dir_name) == None):
#     #     print("String contains special characters.")
#     # else:
#     #     print("String does not contain any special character.")
#     if re.search(pattern, dir_name):
#         raise HTTPException(
#             status_code=status.HTTP_302_FOUND,
#             detail='Folder name should not contains /\:*?"<>| characters',
#             # headers={"WWW-Authenticate": "Bearer"},
#         )
#     is_dir_exist = get_user_dir(current_User.id, dir_name)
#     if(is_dir_exist):
#         # new directory created with dir_name
#         return {'status': 'success', 'message': 'Folder created successfully'}
#     else:
#         # directory already exist with this dir_name
#         return {'status': 'error', 'message': 'Folder already exist with this name'}

# def upload_files(user_id: int, dir_name: str, files: list[UploadFile]):
#     for file in files:
#         with open ('static/'+str(user_id)+'/'+dir_name +'/'+file.filename, 'wb+') as f:
#             f.write(file.file.read())

# @router.post("/upload-files/{dir_name}")
# def create_directory(
#     files: list[UploadFile],
#     dir_name: str, 
#     current_User: CSchemas.User = Depends(UserO.get_current_active_user) ):
#     if files == None:
#         return {'status': 'error', "message": "No upload file sent"}

#     is_dir = is_dir_exist(current_User.id, dir_name)
#     if is_dir:
#         upload_files(current_User.id, dir_name, files)
#         return {'status': 'success', "message": "Files uploaded successfully"}
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail='Folder with this name not found',
#         )