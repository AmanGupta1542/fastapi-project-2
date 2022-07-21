from fastapi import Depends, HTTPException, status, UploadFile
from typing import Union
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import HTTPBearer  , http
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

async def auth_user_staticfiles(token: str):
    token = http.HTTPAuthorizationCredentials(scheme="Bearer", credentials=token[7:])
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
    if user == False:
        raise credentials_exception
    return user

async def get_current_user(token: str = Depends(token_auth_scheme)):
    print(type(token))
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
    if user == False:
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
        product = user.product,
        marketingCampaign= user.marketingCampaign,
        isActive =0, 
        role=2
        )
    db_user.save()
    return db_user

###################################################################################################
###################################################################################################
#
#                            Neilbox Functions
#
###################################################################################################
###################################################################################################

def dir_validation(dir_name: str):
    # /\:*?""<>|
    pattern = '[:*?"<>/|]'
    exc = HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail='Folder name should not contains /\:*?"<>| characters',
        )
    if dir_name.find('\\') != -1:
        raise exc
    if re.search(pattern, dir_name):
        raise exc
    return True

def path_validation(path: str):
    exc = HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail="Path should not contain '.'",
        )
    if path.startswith('.'):
        raise exc
    if path.find('.') != -1:
        raise exc
    return True
    
def create_dir(user_id:int, file_name:str, dir_path: Union[str, None] = None):
    print(dir_path)
    if not os.path.exists('static\\'+str(user_id)):
        os.makedirs('static\\'+str(user_id))
    f = str(file_name) if dir_path == None else dir_path + '\\' + str(file_name)
    if not os.path.exists('static\\'+str(user_id)+'\\'+ f):
        if dir_path == None:
            os.makedirs('static\\'+str(user_id)+'\\'+str(file_name))
        else:
            os.makedirs('static\\'+str(user_id)+'\\'+ dir_path + '\\' + str(file_name))
        return True # id requested directory not exist
    else:
        return False # id requested directory already exist

def is_dir_exist(user_id: int, dir_name: str, dir_path: Union[str, None] = None):
    if os.path.exists('static\\'+str(user_id)):
        if dir_path == None:
            if os.path.exists('static\\'+str(user_id)+'\\'+str(dir_name)):
                return True
            else: 
                return False
        else:
            if os.path.exists('static\\'+str(user_id)+'\\'+dir_path+'\\'+str(dir_name)):
                return True
            else: 
                return False
    return False

def get_file_metadata(file_path: str):
    file_info = {}
    file_info['file'] = file_path
    file_info['access time'] = time.ctime(os.path.getatime(file_path))
    file_info['modified time'] = time.ctime(os.path.getmtime(file_path))
    file_info['change time'] = time.ctime(os.path.getctime(file_path))
    file_info['size'] = "{:.1f}".format(os.path.getsize(file_path)/1024)
    return file_info

def upload_files(user_id: int, files: list[UploadFile], dir_name: Union[str, None]= None):
    files_info = []
    dir_path = 'static\\'+str(user_id)+'\\'+dir_name +'\\' if dir_name != None else 'static\\'+str(user_id)+'\\'
    for file in files:
        with open (dir_path+file.filename, 'wb+') as f:
            f.write(file.file.read())
        files_info.append(get_file_metadata(dir_path+file.filename))
    return files_info

def get_dir_metadata(dir_path: str):
    dir_info = {}
    dir_info['file'] = dir_path
    dir_info['access time'] = time.ctime(os.path.getatime(dir_path))
    dir_info['modified time'] = time.ctime(os.path.getmtime(dir_path))
    dir_info['created time'] = time.ctime(os.path.getctime(dir_path))
    dir_info['size'] = "{:.1f}".format(os.path.getsize(dir_path)/1024)
    return dir_info

def is_starredfile_exist(user_id:int, filePath: str, fileName: str):
    row_count = CModel.StarredFiles.select().where(
        CModel.StarredFiles.owner == user_id, 
        CModel.StarredFiles.filePath == filePath.lower(),
        CModel.StarredFiles.fileName == fileName.lower()).count()
    if row_count:
        return False
    else:
        return True
def strore_data(data):
    if is_starredfile_exist(data['owner'], data['path'], data['dir_name']):
        store = CModel.StarredFiles(owner= data['owner'], filePath=data['path'], fileName= data['dir_name'])
        store.save()
        return store
    else:
        raise HTTPException(status_code=status.HTTP_302_FOUND, detail="already exist")

def get_starred_data(user_id, file_id: Union[int, None] = None):
    # if file id to without list else list
    try:
        print(user_id)
        print(file_id)
        if file_id == None:
            print('if')
            data= list(CModel.StarredFiles.filter(CModel.StarredFiles.owner == user_id)) 
        else:  
            print('else')
            data = CModel.StarredFiles.get(CModel.StarredFiles.owner == user_id, CModel.StarredFiles.id == file_id)
        print(data)
        return data
    except CModel.StarredFiles.DoesNotExist as e:
        # if not exist
        raise HTTPException(status_code=404, detail="Not found")
    except Exception as e:
        print(e)
        return False

def delete_starred_data(user_id, file_id):
    try:
        # Find existrance of the row
        CModel.StarredFiles.get(CModel.StarredFiles.owner == user_id, CModel.StarredFiles.id == file_id).delete_instance()
        
        return True
    except CModel.StarredFiles.DoesNotExist as e:
        # if not exist
        raise HTTPException(status_code=404, detail="Not found")
    except Exception as e:
        # Any unexpexted errors
        print(e)
        return False