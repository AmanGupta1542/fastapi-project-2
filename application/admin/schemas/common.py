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

class UserBase(BaseModel):
    email: EmailStr
    
class User(UserBase):
    id: int
    isActive: bool

    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict

class EmailConfig(BaseModel):
    id: int
    username: str
    password: str
    fromEmail: str
    port: int
    server: str
    tls: bool
    ssl: bool
    use_credentials: bool
    validate_certs: bool
    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict