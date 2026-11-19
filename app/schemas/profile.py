from pydantic import BaseModel

class UpdateName(BaseModel):
    first_name: str = None
    last_name: str = None