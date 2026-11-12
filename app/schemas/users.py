from pydantic import BaseModel

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserEdit(BaseModel):
    first_name: str = None
    last_name: str = None
    bio: str = None
    password: str = None

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class UserPassword(BaseModel):
    password: str

class AddUser(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    role: str