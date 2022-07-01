from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List

from ...user.models.common import MailConfig, DatabaseConfig
from ..dependencies import common as CDepends
from ..schemas import common as CSchemas

router = APIRouter()

@router.get("/read-email-configs", response_model= List[CSchemas.EmailConfig])
def read_email_configs(active_user : Any = Depends(CDepends.get_active_user)):
    mail_server_settings = list(MailConfig.select())
    return mail_server_settings

@router.get("/get-email-configs/{id}", response_model=CSchemas.EmailConfig)
def get_email_configs(id:int, active_user : Any = Depends(CDepends.get_active_user)):
    mail_server_settings = MailConfig.filter(MailConfig.id == id).first()
    # return mail_server_settings
    if mail_server_settings is None:
        raise HTTPException(status_code=404, detail="Not found")
    return mail_server_settings