from sqlmodel import SQLModel
from typing import Optional

class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    email: Optional[str] = None