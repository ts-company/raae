from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    google_sub = Column(String, nullable=True, unique=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=True)
    email = Column(String(100), nullable=False, unique=True)
    password = Column(String, nullable=True)
    role = Column(String, nullable=False)
    balance = Column(Numeric(24, 2), nullable=False)
    date_joined = Column(DateTime, nullable=False)
    is_active = Column(Boolean, nullable=False)