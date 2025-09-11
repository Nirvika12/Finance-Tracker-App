from pydantic import BaseModel, EmailStr
from app.schema.transactions_schema import TransactionRead
#from app.schema.budget_schema import BudgetRead
from datetime import datetime 
from typing import Optional, List

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password_hash: str  

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
    transactions: List[TransactionRead] = []

    class Config:
        from_attributes = True

# class UserRead(BaseModel):
#     id: int
#     name: str
#     email: str
#     created_at: datetime
#     updated_at: datetime
#     transactions: list["TransactionsRead"] = [] 
#     budgets: list["BudgetRead"] = []

#     class Config:
#         from_attribute = True

