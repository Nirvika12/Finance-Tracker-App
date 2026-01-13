from pydantic import BaseModel

class BudgetCreate(BaseModel):
    user_id : int
    category_id : int
    monthly_limit : float
    month : str

    class config:
        from_attribute = True
