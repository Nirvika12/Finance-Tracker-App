from pydantic import BaseModel

class BudgetRead(BaseModel):
    id: int
    user_id: int
    category_id: int
    monthly_limit: float

    class Config:
        from_attribute = True