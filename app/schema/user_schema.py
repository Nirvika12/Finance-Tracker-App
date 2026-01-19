from pydantic import BaseModel, EmailStr
from datetime import datetime 
from typing import Optional, List
from app.schema.transaction_schema import TransactionRead

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str  

    class Config:
        from_attribute = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password_hash: Optional[str] = None

    class Config:
        from_attribute = True

class UserRead(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attribute = True

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    transactions: list[TransactionRead] = [] 
    

    class Config:
        from_attribute = True

class UserLogin(BaseModel):
    email: str
    password: str

    class Config:
        from_attribute = True