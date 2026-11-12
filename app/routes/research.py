from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.models.users import User
from app.core.auth import validate_user
from app.database import get_db
from app.config import BASE_DIR

router = APIRouter(prefix="/research")

templates = Jinja2Templates(directory=BASE_DIR / "templates")

@router.get("/page")
def login_page(request: Request):
    return templates.TemplateResponse("research.html", {"request": request})