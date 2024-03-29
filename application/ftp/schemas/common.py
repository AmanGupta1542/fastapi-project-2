from dataclasses import field
from pydantic import BaseModel, Required
from typing import Any, Union

################################################################################################
################################################################################################
#
#                                   Request data schemas
#
################################################################################################
################################################################################################

class FTPData(BaseModel):
    host: str
    user: str
    password: str
    port: Union[int, None] = None


################################################################################################
################################################################################################
#
#                                   Request model schemas
#
################################################################################################
################################################################################################

class StatusSchema(BaseModel):
    status: str

class MessageSchema(StatusSchema):
    message: Any