from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.security import hash_password
from dotenv import load_dotenv
from app.core.auth import validate_user
from app.database import engine, Base, get_db
from app.config import BASE_DIR
from datetime import datetime, timezone

load_dotenv()

templates = Jinja2Templates(directory=BASE_DIR / "templates")

app = FastAPI()

app.mount("/static",StaticFiles(directory=BASE_DIR / "static"), name="static")

# Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):

    return templates.TemplateResponse("home.html", {"request": request})