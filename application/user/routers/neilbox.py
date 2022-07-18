from fastapi import APIRouter, HTTPException, Depends, status, UploadFile
import re, os, shutil
from typing import Union

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


@router.post("/create-directory")
def create_directory(data:CSchemas.DirReqData, current_User: CSchemas.User = Depends(UserO.get_current_active_user) ):
    # /\:*?""<>|
    pattern = '[:*?"<>/|]'
    if re.search(pattern, data.dir_name):
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail='Folder name should not contains /\:*?"<>| characters',
        )
    print(data.path)
    is_dir_exist = UserO.create_dir(current_User.id, data.dir_name) if data.path == None else UserO.create_dir(current_User.id, data.dir_name, data.path)
    print(is_dir_exist)
    if(is_dir_exist):
        return {'status': 'success', 'message': 'Folder created successfully'}
    else:
        return {'status': 'error', 'message': 'Folder already exist with this name'}

@router.post("/upload-files")
def create_directory(
    files: list[UploadFile],
    dir_name: Union[str, None] = None, 
    current_User: CSchemas.User = Depends(UserO.get_current_active_user) ):
    if files == None:
        return {'status': 'error', "message": "No upload file sent"}

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

@router.get("/get-all-directories/")
def get_all_directories(
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    dir_info = []
    [dir_info.append(UserO.get_dir_metadata(static_dir_path+str(current_User.id)+'\\'+x)) for x in next(os.walk(static_dir_path+str(current_User.id)))[1]]
    return {'status': 'success', 'dirs': dir_info}


@router.get("/get-all-directories/{dir_name}")
def get_all_directories(
    dir_name: str, 
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    is_dir = UserO.is_dir_exist(current_User.id, dir_name)
    if is_dir:
        dir_list = [x for x in next(os.walk(static_dir_path+str(current_User.id)+'\\'+dir_name))[1]]
        return {'status': 'success', 'dirs': dir_list}
    else:
        return {'status': 'error', "message": "Folder not exist"}

@router.patch("/rename-directory")
def rename_directory(
    data: CSchemas.DirRename, 
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    is_dir = UserO.is_dir_exist(current_User.id, data.old_dir_name) if data.path == None else UserO.is_dir_exist(current_User.id, data.old_dir_name, data.path)
    dir_path = static_dir_path+str(current_User.id)+'\\' if data.path == None else static_dir_path+str(current_User.id)+ '\\'+ data.path + '\\'
    # print(dir_path+data.old_dir_name)

    file_name1, file_extension1 = os.path.splitext(dir_path+data.old_dir_name)
    file_name2, file_extension2 = os.path.splitext(dir_path+data.new_dir_name)
    if file_extension1 != file_extension2:
        return {'status': 'error', 'message': "can not update file extension."}

    # print(file_name1)
    # print(file_extension1)
    if is_dir:
        os.rename(dir_path+data.old_dir_name, dir_path+data.new_dir_name)
        return {'status': 'success', 'message': "Folder renamed successfully"}
    else:
        return {'status': 'error', "message": "Folder not exist"}

@router.patch("/delete-directory", description="Path is optional and if you are giving path then seperate path with double slash")
def rename_directory(
    data: CSchemas.DirReqData, 
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):
    is_dir = UserO.is_dir_exist(current_User.id, data.dir_name) if data.path == None else UserO.is_dir_exist(current_User.id, data.dir_name, data.path)
    dir_path = static_dir_path+str(current_User.id)+'\\' if data.path == None else static_dir_path+str(current_User.id)+ '\\'+ data.path + '\\'
    src_path = dir_path+data.dir_name
    if src_path.endswith("trash"):
        return {'status': 'error', 'message': "Can not delete trash folder"}
    if is_dir:
        dest_path = static_dir_path+str(current_User.id)+'\\'+'trash'
        # print(src_path)
        # print(dest_path)
        # shutil.rmtree(dir_path+data.dir_name)
        # shutil.copy2(src_path, dest_path)

        ######## trick ###########
        # if you want to delete folder permanently without moving it to the trash
        # send API body like this
        #{
        #    "path": "trash",
        #    "dir_name": "..\\folder_name"
        #}
        ##########################
        if data.path != None and data.path.startswith("trash"):
            shutil.rmtree(src_path)
        else:
            shutil.move(src_path, dest_path)
        return {'status': 'success', 'message': "Folder deleted successfully"}
    else:
        return {'status': 'error', "message": "Folder not exist"}


@router.patch("/get-dir-info")
def rename_directory(
    dir_name: Union[str, None] = None, 
    current_User: CSchemas.User = Depends(UserO.get_current_active_user)):

    dirs = []
    files = []
    dir_info = {}

    is_dir = UserO.is_dir_exist(current_User.id, dir_name) if dir_name != None else True
    dir_path = static_dir_path+str(current_User.id)+'\\'+dir_name if dir_name != None else static_dir_path+str(current_User.id)
    
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