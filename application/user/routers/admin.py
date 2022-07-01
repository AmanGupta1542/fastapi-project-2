from fastapi import APIRouter, Depends, HTTPException
from typing import List, Union

from ..dependencies import common

router = APIRouter()