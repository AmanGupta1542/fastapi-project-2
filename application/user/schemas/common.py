from fastapi import Body, File, Path, UploadFile
from pydantic import BaseModel, EmailStr, Field
import peewee
from pydantic.utils import GetterDict
from typing import Any, Union


class PeeweeGetterDict(GetterDict):
    def get(self, key: Any, default: Any = None):
        res = getattr(self._obj, key, default)
        if isinstance(res, peewee.ModelSelect):
            return list(res)
        return res

class TokenData(BaseModel):
    email: Union[str , None] = None

class LoginData(BaseModel):
    email: str
    password: str

class ResetPassword(BaseModel):
    password: str = Field(
        title="Password of the user", min_length=6
    )

class Token(BaseModel):
    access_token: str
    token_type: str

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    firstName: str
    lastName: str
    password: str = Field(
        title="Password of the user", min_length=6
    )
    changedPassword: str
    changedEmail: str
    upline: str
    downline: str
    tree: str
    product : str
    marketingCampaign : str

class User(UserBase):
    id: int
    isActive: bool

    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict

class ChangePass(BaseModel):
    oldPassword: str = Field(min_length=6)
    newPassword: str = Field(min_length=6)

class PathSchema(BaseModel):
    path: Union[str, None] = None
    
class DirRename(PathSchema):
    old_dir_name: str
    new_dir_name: str

class DirReqData(PathSchema):
    dir_name: str