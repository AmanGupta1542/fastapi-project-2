from fastapi import APIRouter
import ftplib

from .operations import *
from ..schemas import common as CSchemas

router = APIRouter(
    responses={404: {"description": "Not found"}},
)

@router.post("/server-connection")
def server_connection(data: CSchemas.FTPData):
    res_status = ftp_connection(data) #this return a tuple
    files = []
    if res_status[0]:
        try:
            ftp_server = res_status[1]
            ftp_server.dir(files.append)
            # print(ftp_server.dir())

            # ftp_server.quit()
            return {"status": "success", "message": "Connected successfully", "dirs": files}
        except Exception as e:
            # print(e)
            return {"status": "error", "message": 'Something went wrong please check your credentials'}
        finally:
            # print('connection closed')
            ftp_server.quit()

    return {"status": "error", "message": 'Something went wrong please check your credentials'}