from fastapi import APIRouter, HTTPException, Depends, status, UploadFile
import re, os, shutil

from pydantic import BaseModel

from ..dependencies import common as CDepends
from ..schemas import common as CSchemas
from ..settings import config
from .operations import user_crud as UserO

static_dir_path = config.settings.static_dir_path
router = APIRouter(
    prefix="/neilbox",
    tags=["NeilBox"],
    dependencies=[Depends(CDepends.get_db)],
    responses={404: {"description": "Not found"}},
)


@router.post("/create-directory/{dir_name}")
def create_directory(dir_name: str, current_User: CSchemas.User = Depends(UserO.get_current_active_user) ):
    # /\:*?""<>|
    pattern = '[:*?"<>/\|]'
    # pattern = re.compile('[/\:*?"<>|]')
    # if(pattern.search(dir_name) == None):
    #     print("String contains special characters.")
    # else:
    #     print("String does not contain any special character.")
    if re.search(pattern, dir_name):
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail='Folder name should not contains /\:*?"<>| characters',
            # headers={"WWW-Authenticate": "Bearer"},
        )
    is_dir_exist = UserO.create_dir(current_User.id, dir_name)
    if(is_dir_exist):
        # new directory created with dir_name
        return {'status': 'success', 'message': 'Folder created successfully'}
    else:
        # directory already exist with this dir_name
        return {'status': 'error', 'message': 'Folder already exist with this name'}

# def upload_files(user_id: int, dir_name: str, files: list[UploadFile]):
#     for file in files:
#         with open ('static/'+str(user_id)+'/'+dir_name +'/'+file.filename, 'wb+') as f:
#             f.write(file.file.read())

@router.post("/upload-files/{dir_name}")
def create_directory(
    files: list[UploadFile],
    dir_name: str, 
    current_User: CSchemas.User = Depends(UserO.get_current_active_user) ):
    if files == None:
        return {'status': 'error', "message": "No upload file sent"}

    is_dir = UserO.is_dir_exist(current_User.id, dir_name)
    if is_dir:
        files_info = UserO.upload_files(current_User.id, dir_name, files)
        return {'status': 'success', "message": "Files uploaded successfully", 'files_info': files_info}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Folder with this name not found',
        )

@router.get("/get-all-directories/")
def get_all_directories(
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    dir_info = []
    # print(static_dir_path+str(current_User.id))
    # print([x for x in os.walk('static/'+str(current_User.id))])
    # print([x for x in next(os.walk('static/'+str(current_User.id)))[1]])
    # UserO.get_dir_metadata()
    # print(static_dir_path+str(current_User.id)+'\\'+'a')
    # dir_list = [x for x in next(os.walk(static_dir_path+str(current_User.id)))[1]]
    [dir_info.append(UserO.get_dir_metadata(static_dir_path+str(current_User.id)+'\\'+x)) for x in next(os.walk(static_dir_path+str(current_User.id)))[1]]

    # for path, subdirs, files in os.walk('static\\'+str(current_User.id)):
    #     for name in subdirs:
    #         print(os.path.join(path, name))

    return {'status': 'success', 'dirs': dir_info}


@router.get("/get-all-directories/{dir_name}")
def get_all_directories(
    dir_name: str, 
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    is_dir = UserO.is_dir_exist(current_User.id, dir_name)
    # print('static/'+str(current_User.id)+'/'+dir_name)
    # print([x for x in os.walk('static/'+str(current_User.id)+'/'+dir_name)])
    if is_dir:
        dir_list = [x for x in next(os.walk('static/'+str(current_User.id)+'/'+dir_name))[1]]
        return {'status': 'success', 'dirs': dir_list}
    else:
        return {'status': 'error', "message": "Folder not exist"}

@router.patch("/rename-directory")
def rename_directory(
    data: CSchemas.DirRename, 
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    is_dir = UserO.is_dir_exist(current_User.id, data.old_dir_name)
    dir_path = static_dir_path+str(current_User.id)+'\\'
    if is_dir:
        os.rename(dir_path+data.old_dir_name, dir_path+data.new_dir_name)
        return {'status': 'success', 'message': "Folder renamed successfully"}
    else:
        return {'status': 'error', "message": "Folder not exist"}

@router.patch("/delete-directory/{dir_name}")
def rename_directory(
    dir_name: str, 
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    is_dir = UserO.is_dir_exist(current_User.id, dir_name)
    dir_path = static_dir_path+str(current_User.id)+'\\'
    if is_dir:
        # os.rmdir(dir_path+dir_name) # for remove empty directory
        shutil.rmtree(dir_path+dir_name)
        return {'status': 'success', 'message': "Folder deleted successfully"}
    else:
        return {'status': 'error', "message": "Folder not exist"}