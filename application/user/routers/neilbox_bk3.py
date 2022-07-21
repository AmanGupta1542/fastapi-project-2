from fastapi import APIRouter, HTTPException, Depends, status, UploadFile
import re, os, shutil
from typing import Union
from cryptography.fernet import Fernet #file encryption
from fastapi.responses import FileResponse

from ..dependencies import common as CDepends
from ..schemas import common as CSchemas
from ..settings.config import settings, delimiter
from .operations import user_crud as UserO

# key generation
key = Fernet.generate_key()

# string the key in a file
with open('filekey.key', 'wb') as filekey:
   filekey.write(key)

# opening the key
with open('filekey.key', 'rb') as filekey:
    key = filekey.read()
 
# using the generated key
fernet = Fernet(key)

static_dir_path = settings.static_dir_path
router = APIRouter(
    prefix="/neilbox",
    tags=["NeilBox"],
    dependencies=[Depends(CDepends.get_db)],
    responses={404: {"description": "Not found"}},
)

@router.get('/validate-dir-name', response_model=CSchemas.StatusSchema)
def dir_name_validation(dir_name: str):
    if UserO.dir_validation(dir_name):
        return {'status': 'success'}
    else:
        return {'status': 'error'}

@router.get('/validate-path-name', response_model=CSchemas.StatusSchema)
def path_validation(path: str):
    if UserO.path_validation(path):
        return {'status': 'success'}
    else:
        return {'status': 'error'}

@router.post("/directories", response_model=CSchemas.MessageSchema)
def create_directory(data:CSchemas.DirReqData, current_User: CSchemas.User = Depends(UserO.get_current_active_user) ):
    UserO.dir_validation(data.dir_name)
    if data.path != None:
        UserO.path_validation(data.path)
    is_dir_exist = UserO.create_dir(current_User.id, data.dir_name) if data.path == None else UserO.create_dir(current_User.id, data.dir_name, data.path)
    if(is_dir_exist):
        return {'status': 'success', 'message': 'Folder created successfully'}
    else:
        return {'status': 'error', 'message': 'Folder already exist with this name'}

@router.post('/files/create', response_model=CSchemas.MessageSchema)
def create_file(
    data: CSchemas.CreateFileSchema,
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    if data.path != None:
        UserO.path_validation(data.path)
    is_created = UserO.create_file(current_User.id, data.file_name, data.path) if data.path != None else UserO.create_file(current_User.id, data.file_name)
    if is_created:
        return {'status': 'success', "message": "File created successfully"}
    else:
        return {'status': 'error', "message": "Already exist"}

@router.post("/files")
def create_files(
    files: list[UploadFile],
    dir_name: Union[str, None] = None, 
    current_User: CSchemas.User = Depends(UserO.get_current_active_user) ):
    
    if dir_name != None:
        UserO.dir_validation(dir_name)
    # if files == None:
    #     return {'status': 'error', "message": "No upload file sent"}

    is_dir = UserO.is_dir_exist(current_User.id, dir_name) if dir_name != None else True
    if is_dir:
        if dir_name != None:
            files_info = UserO.upload_files(current_User.id, files, dir_name)
        else:
            files_info = UserO.upload_files(current_User.id, files)
        return {'status': 'success', "message": "Files uploaded successfully", 'files_info': files_info}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Folder with this name not found',
        )

@router.get("/directories")
def get_all_directories(
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    dir_info = []
    if UserO.is_dir_exist(current_User.id, ''):
        return {'status': 'error', 'message': 'User static files not exist'}
    try:
        [dir_info.append(UserO.get_dir_metadata(static_dir_path+str(current_User.id)+delimiter+x)) for x in next(os.walk(static_dir_path+str(current_User.id)))[1]]
        return {'status': 'success', 'dirs': dir_info}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')


@router.get("/directories/{dir_name}")
def directories(
    dir_name: str, 
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    UserO.dir_validation(dir_name)
    is_dir = UserO.is_dir_exist(current_User.id, dir_name)
    if is_dir:
        dir_list = [x for x in next(os.walk(static_dir_path+str(current_User.id)+delimiter+dir_name))[1]]
        return {'status': 'success', 'dirs': dir_list}
    else:
        return {'status': 'error', "message": "Folder not exist"}

@router.patch("/directory")
def rename_directory(
    data: CSchemas.DirRename, 
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    """
    Rename folder or file

    - **Scenario 1**: Path and folder names should valid
    - **Scenario 2**: Can not modify trash folder
    - **Scenario 3**: Can not modify file extension
    - **Scenario 4**: Folder and file should be exist
    """
    UserO.dir_validation(data.old_dir_name)
    UserO.dir_validation(data.new_dir_name)
    if data.path != None:
        UserO.path_validation(data.path)

    if data.old_dir_name.lower() == 'trash' or data.new_dir_name.lower() == 'trash':
        return {'status': 'error', 'message': "Can not modify trash."}

    is_dir = UserO.is_dir_exist(current_User.id, data.old_dir_name) if data.path == None else UserO.is_dir_exist(current_User.id, data.old_dir_name, data.path)
    dir_path = static_dir_path+str(current_User.id)+delimiter if data.path == None else static_dir_path+str(current_User.id)+ delimiter+ data.path + delimiter
    # print(dir_path+data.old_dir_name)

    file_name1, file_extension1 = os.path.splitext(dir_path+data.old_dir_name)
    file_name2, file_extension2 = os.path.splitext(dir_path+data.new_dir_name)
    if file_extension1 != file_extension2:
        return {'status': 'error', 'message': "Can not update file extension."}

    # print(file_name1)
    # print(file_extension1)
    if is_dir:
        os.rename(dir_path+data.old_dir_name, dir_path+data.new_dir_name)
        return {'status': 'success', 'message': "Folder renamed successfully"}
    else:
        return {'status': 'error', "message": "Folder does not exist"}

@router.delete(
    "/directory", 
    description="Path is optional and if you are giving path then seperate path with double slash",
    response_model=CSchemas.MessageSchema)
def delete_directory(
    data: CSchemas.DirReqData, 
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    UserO.dir_validation(data.dir_name)
    if data.path != None:
        UserO.path_validation(data.path)
    user_dir_path = static_dir_path+str(current_User.id)
    is_dir = UserO.is_dir_exist(current_User.id, data.dir_name) if data.path == None else UserO.is_dir_exist(current_User.id, data.dir_name, data.path)
    dir_path = user_dir_path+delimiter if data.path == None else user_dir_path+ delimiter+ data.path + delimiter
    if data.dir_name.lower().endswith("trash"):
        return {'status': 'error', 'message': "Can not delete trash folder"}
    if is_dir:
        dest_path = user_dir_path+delimiter+'trash'
        if data.path != None and data.path.startswith("trash"):
            shutil.rmtree( dir_path+data.dir_name)
        else:
            shutil.move( dir_path+data.dir_name, dest_path)
        return {'status': 'success', 'message': "Folder deleted successfully"}
    else:
        return {'status': 'error', "message": "Folder does not exist"}


@router.get("/get-dir-info")
def direcotry_details(
    dir_name: Union[str, None] = None, 
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):

    dirs = []
    files = []
    dir_info = {}

    is_dir = UserO.is_dir_exist(current_User.id, dir_name) if dir_name != None else True
    dir_path = static_dir_path+str(current_User.id)+delimiter+dir_name if dir_name != None else static_dir_path+str(current_User.id)
    
    if is_dir:
        with os.scandir(dir_path) as it:
            for entry in it:
                if not entry.name.startswith('.') and entry.is_file():
                    files.append(entry.name)
                    # print(entry.name)
                if not entry.name.startswith('.') and entry.is_dir():
                    dirs.append(entry.name)
                    # print(entry.name)
        dir_info['dirs'] = dirs
        dir_info['files'] = files
        return {'status': 'success', 'dir_info': dir_info}
    else:
        return {'status': 'error', "message": "Folder not exist"}

# @router.get('/encrypt-file/{dir_name}', response_class=FileResponse)
# def encrypt_file(
#     dir_name: str,
#     current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
#     path = static_dir_path+str(current_User.id)+delimiter+dir_name
#     # opening the original file to encrypt
#     with open(path, 'rb') as file:
#         original = file.read()
    
#     encrypted = fernet.encrypt(original)
#     with open (path, 'wb') as enc_file:
#         enc_file.write(encrypted)
        
#     # return {'status': 'success', 'file': FileResponse(path)}
#     return FileResponse(path)

# @router.post('/create-shortcut')
# def create_shortcut(
#     data: CSchemas.DIRShortcut,
#     current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
#     src = static_dir_path+str(current_User.id)+delimiter+data.source_path
#     dest = static_dir_path+str(current_User.id)+delimiter+data.destination_path
#     return {'status': 'success', 'src': src, 'dest': dest}

@router.post('/starred')
def post_starred_files(
    data: CSchemas.DIRStarred,
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    """
    Insert starred file into database

    - **Scenario 1**: If same data already exist, means check for duplication first, raise error
    - **Scenario 2**: If data not exist , insert it
    """
    file_data = {}

    path = static_dir_path+str(current_User.id)+delimiter+data.path if data.path != None else static_dir_path+str(current_User.id)
    dir_name = path+delimiter+data.dir_name
    file_data['owner'] = current_User
    file_data['path'] = path
    file_data['dir_name'] = data.dir_name
    is_stored = UserO.strore_data(file_data)
    if is_stored != False:
        return {'status': 'success', 'data': is_stored}
    else:
        return {'status': 'error', 'message': 'something went wrong'}

@router.get('/starred', response_model=CSchemas.StarredData)
def get_starred_files(current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    """
    Get all starred files

    - **Scenario 1**: Send all existing data for request user
    """
    data = UserO.get_starred_data(current_User.id)
    if data != False:
        return {'status': 'success', 'data': data}
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR , detail="Internal server error")

@router.get('/starred/{id}', response_model=CSchemas.SingleStarredData)
def get_starred_file(id: int, current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    """
    Get single record

    - **Scenario 1**: If id not exist
    - **Scenario 2**: If id exist
    """
    data = UserO.get_starred_data(current_User.id, id)
    if data != False:
        return {'status': 'success', 'data': data}
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR , detail="Internal server error")

@router.delete('/starred/{id}', response_model=CSchemas.MessageSchema)
def delete_starred_files(id: int, current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    """
    Delete starred file

    - **Scenario 1**: If id not exist
    - **Scenario 2**: If id exist
    """
    is_deleted = UserO.delete_starred_data(current_User.id, id)
    if is_deleted:
        return {'status': 'success', 'message': 'Removed'}
    else:
        return {'status': 'error', 'message': 'something went wrong'}