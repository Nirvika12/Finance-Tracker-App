from pydantic import BaseModel
from typing import Optional

class BudgetCreate(BaseModel):
    category_id : int
    monthly_limit : float
    month : str

    class config:
        from_attribute = True

class BudgetStatus(BaseModel):
        category_id : int
        amount: Optional[float] = 0.0
        spent : Optional[float] = 0.0
        remaining: Optional[float] = 0.0
        progress: Optional[float] = 0.0

class MonthlyBudgetResponse(BaseModel):
    user_id: int
    month: str
    budgets: list[BudgetStatus]
        