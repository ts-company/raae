from fastapi import APIRouter, Depends, status, HTTPException, Request, Body
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.users import User
from app.core.security import verify_password
from app.core.auth import create_access_token
from app.database import get_db
from app.schemas.users import UserLogin, UserCreate, ResetPasswordRequest
from app.services.email import send_password_reset_email, serializer
from app.core.security import hash_password
from app.config import BASE_DIR
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from datetime import datetime, timezone
from app.core.limiter import limiter
from itsdangerous import SignatureExpired, BadSignature
import os

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
PASSWORD_RESET_SALT = os.getenv("PASSWORD_RESET_SALT")

router = APIRouter(prefix="/auth")

templates = Jinja2Templates(directory=BASE_DIR / "templates")

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "google_client_id": GOOGLE_CLIENT_ID})

@router.post("/login_data")
@limiter.limit("5/minute")
async def login(request: Request,
                userlogin: UserLogin,
                db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == userlogin.email).first()
    if user is not None:
        if not user.password:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    if not user or not verify_password(userlogin.password, user.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })

    response = JSONResponse({"role": user.role})

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )
    # for deployment
    # samesite = "none",
    # secure = True,

    return response

@router.post("/google")
async def google_login(request: Request, payload: dict, db: Session = Depends(get_db)):
    try:
        idinfo = id_token.verify_oauth2_token(
            payload["credential"], google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    if not idinfo.get("email_verified"):
        raise HTTPException(status_code=401, detail="Google email not verified")
    google_sub = idinfo["sub"]
    email = idinfo["email"]
    first_name = idinfo.get("given_name", "")
    last_name = idinfo.get("family_name", "")

    try:
        user = db.query(User).filter(User.google_sub == google_sub).first()
        if not user:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.google_sub = google_sub
            else:
                user = User(google_sub=google_sub,
                            email=email,
                            first_name=first_name,
                            last_name=last_name,
                            role="user",
                            balance=0,
                            date_joined=datetime.now(timezone.utc),
                            is_active=True)

                db.add(user)
            db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })

    response = JSONResponse({"role": user.role})

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )
    # for deployment
    # samesite = "none",
    # secure = True,

    return response

@router.get("/signup")
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "google_client_id": GOOGLE_CLIENT_ID})

@router.post("/get_signup")
async def signup(request: Request,
                 usercreate: UserCreate,
                db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email==usercreate.email).first()
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    try:
        new_user = User(
            first_name=usercreate.first_name,
            last_name=usercreate.last_name,
            email=usercreate.email,
            password=hash_password(usercreate.password),
            role='user',
            balance=0,
            date_joined=datetime.now(timezone.utc),
            is_active=True,
        )

        db.add(new_user)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    token = create_access_token({
        "sub": str(new_user.id),
        "role": new_user.role
    })

    response = JSONResponse({"success": True})

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )
    # for deployment
    # samesite = "none",
    # secure = True,

    return response

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie(
        key="access_token",
        path="/",
    )
    return response


@router.post("/forgot_password")
@limiter.limit("3/minute")
def forgot_password(request: Request, email: str = Body(..., embed=True), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if user:
        send_password_reset_email(user.id, user.email)

    return {"success": True}


@router.get("/reset_password/{token}")
def reset_password_page(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})


@router.post("/reset_password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        data = serializer.loads(payload.token, salt=PASSWORD_RESET_SALT, max_age=600)  # 10 min
    except SignatureExpired:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset link has expired")
    except BadSignature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset link")

    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user or user.email != data["email"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This link is no longer valid")

    if len(payload.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters")

    user.password = hash_password(payload.new_password)

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return {"success": True}