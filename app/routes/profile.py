from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.users import User
from app.core.auth import validate_user
from app.schemas.profile import UpdateName
from app.database import get_db
from app.config import BASE_DIR

router = APIRouter(prefix="/profile")

templates = Jinja2Templates(directory=BASE_DIR / "templates")

# the page template endpoint with some user info
@router.get("/page")
def profile_page(request: Request, db: Session = Depends(get_db)):
    try:
        token = request.cookies.get("access_token")
        user_id, user_role = validate_user(token)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except HTTPException:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("profile.html", {"request": request,
                                                        "first_name": user.first_name,
                                                        "last_name": user.last_name,
                                                        "email": user.email})


# the user can update his first and last name
@router.patch("/update_name")
def update_name(request: Request, payload: UpdateName, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    user_id, user_role = validate_user(token)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    try:
        if payload.first_name is not None:
            user.first_name = payload.first_name
        if payload.last_name is not None:
            user.last_name = payload.last_name
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return {"first_name": payload.first_name, "last_name": payload.last_name}


