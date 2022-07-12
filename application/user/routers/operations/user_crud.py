from fastapi import Depends, HTTPException, status, UploadFile
from typing import Union
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import HTTPBearer  
import string, random
import os, re, time

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

async def get_current_user(token: str = Depends(token_auth_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        if not CModel.TokenBlocklist.select().where(CModel.TokenBlocklist.token == token.credentials).count():
            payload = jwt.decode(token.credentials, config.settings.secret_key, algorithms=[config.settings.algorithm])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
            token_data = CSchemas.TokenData(email=email)
        else:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: CSchemas.User = Depends(get_current_user)):
    print(current_user)
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
        product = user.product,
        marketingCampaign= user.marketingCampaign,
        isActive =0, 
        role=2
        )
    db_user.save()
    return db_user

# def store_kyc_data(user: CSchemas.UserCreate):
#     db_user = CModel.UserKYC(
#         user = user,
#         document_name = 
#         document = 
#         )
#     db_user.save()
#     return db_user


###################################################################################################
###################################################################################################
#
#                            Neilbox Functions
#
###################################################################################################
###################################################################################################


def create_dir(user_id:int, file_name:str):
    if not os.path.exists('static/'+str(user_id)):
        os.makedirs('static/'+str(user_id))
    if not os.path.exists('static/'+str(user_id)+'/'+str(file_name)):
        os.makedirs('static/'+str(user_id)+'/'+str(file_name))
        return True # id requested directory not exist
    else:
        return False # id requested directory already exist
    with open ('static/'+str(user_id)+'/'+file.filename, 'wb+') as user_kyc_file:
        user_kyc_file.write(file.file.read()) 

def is_dir_exist(user_id: int, dir_name: str):
    if os.path.exists('static/'+str(user_id)):
        if os.path.exists('static/'+str(user_id)+'/'+str(dir_name)):
            return True
        else: 
            return False
    return False

def get_file_metadata(file_path: str):
    file_info = {}
    # for this user_crud.py file info
    # print('File         :', __file__)
    # print('Access time  :', time.ctime(os.path.getatime(__file__)))
    # print('Modified time:', time.ctime(os.path.getmtime(__file__)))
    # print('Change time  :', time.ctime(os.path.getctime(__file__)))
    # print('Size         :', os.path.getsize(__file__))

    # specified file info
    # print('File         :', file_path)
    # print('Access time  :', time.ctime(os.path.getatime(file_path)))
    # print('Modified time:', time.ctime(os.path.getmtime(file_path)))
    # print('Change time  :', time.ctime(os.path.getctime(file_path)))
    # print('Size         :', os.path.getsize(file_path))
    # print("{:.1f}".format(os.path.getsize(file_path)/1024))
    file_info['file'] = file_path
    file_info['access time'] = time.ctime(os.path.getatime(file_path))
    file_info['modified time'] = time.ctime(os.path.getmtime(file_path))
    file_info['change time'] = time.ctime(os.path.getctime(file_path))
    file_info['size'] = "{:.1f}".format(os.path.getsize(file_path)/1024)
    return file_info

def upload_files(user_id: int, dir_name: str, files: list[UploadFile]):
    files_info = []
    dir_path = 'static/'+str(user_id)+'/'+dir_name +'/'
    for file in files:
        # print(file.file._file.__dict__)
        with open (dir_path+file.filename, 'wb+') as f:
            f.write(file.file.read())
        files_info.append(get_file_metadata(dir_path+file.filename))
    return files_info
        # print(os.path.getsize(dir_path+file.filename))
        # print(os.path.getmtime(dir_path+file.filename))
        # print(os.path.getctime(dir_path+file.filename))
        # print(os.stat(dir_path+file.filename))
        # os.stat(dir_path+file.filename).st_uid = user_id
        # print(os.stat(dir_path+file.filename))

        # for this user_crud.py file info
        # print('File         :', __file__)
        # print('Access time  :', time.ctime(os.path.getatime(__file__)))
        # print('Modified time:', time.ctime(os.path.getmtime(__file__)))
        # print('Change time  :', time.ctime(os.path.getctime(__file__)))
        # print('Size         :', os.path.getsize(__file__))

        # # specified file info
        # print('File         :', dir_path+file.filename)
        # print('Access time  :', time.ctime(os.path.getatime(dir_path+file.filename)))
        # print('Modified time:', time.ctime(os.path.getmtime(dir_path+file.filename)))
        # print('Change time  :', time.ctime(os.path.getctime(dir_path+file.filename)))
        # print('Size         :', os.path.getsize(dir_path+file.filename))
        # print("{:.1f}".format(os.path.getsize(dir_path+file.filename)/1024))

def get_dir_metadata(dir_path: str):
    # with os.scandir() as dir_entries:
    #     for entry in dir_entries:
    #         info = entry.stat()
    #         print(info.st_mtime)

    dir_info = {}
    dir_info['file'] = dir_path
    dir_info['access time'] = time.ctime(os.path.getatime(dir_path))
    dir_info['modified time'] = time.ctime(os.path.getmtime(dir_path))
    dir_info['created time'] = time.ctime(os.path.getctime(dir_path))
    dir_info['size'] = "{:.1f}".format(os.path.getsize(dir_path)/1024)
    return dir_info