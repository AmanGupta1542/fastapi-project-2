from fastapi import FastAPI

from .admin import main as admin_root
from .user import main as user_root
app = FastAPI()

app.mount("/api", user_root.app)
app.mount("/admin", admin_root.app)