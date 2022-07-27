from fastapi import FastAPI

from .routers import server_access


app = FastAPI()

app.include_router(server_access.router)