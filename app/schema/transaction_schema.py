from pydantic import BaseModel
from datetime import date, datetime

class TransactionsCreate(BaseModel):
   
    user_id : int
    category_id : int
    amount : float
    description : str | None = None
    date : datetime

    class Config:
        from_attribute = True

class TransactionRead(BaseModel):
    id : int
    amount : float
    description : str | None = None
    date : datetime
    category_name: str 
    is_expense: bool 

    class Config:
        from_attribute = True


class TransactionsUpdate(BaseModel):
   
    category_id : int
    amount : float
    description : str | None = None
    date : date

    class Config:
        from_attribute = True

class TransactionsCategory(BaseModel):
    amount : float
    date : datetime
    description : str

    class Config:
        from_attribute = True
