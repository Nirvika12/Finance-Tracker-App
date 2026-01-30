from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schema.budget_schema import BudgetCreate, ResponseModel
from app.models.tables import budget_model, transaction_model
from datetime import datetime
from app.routers.auth import get_current_user

router = APIRouter(prefix="/budget",tags=['Budget'])

    
@router.post("/create-or-update/")
async def create_or_update_budget(budget: BudgetCreate, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    """
    Add a new budget or update an existing budget for the same user, category, and month.
    """
    # Check if a budget already exists for this user, category, and month
    existing_budget = db.query(budget_model).filter(
        budget_model.user_id == current_user_id,
        budget_model.category_id == budget.category_id,
        budget_model.month == budget.month
    ).first()

    if existing_budget:
        # Update existing budget
        existing_budget.monthly_limit = budget.monthly_limit
        db.commit()
        db.refresh(existing_budget)
        return ResponseModel(Message="Updated Budget successfully", Data=existing_budget, StatusCode=status.HTTP_200_OK)

    # Create new budget
    new_budget = budget_model(**existing_budget.model_dump(exclude_unset=True), user_id=current_user_id)
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)

    return ResponseModel(Message="Budget added successfully", Data=new_budget, StatusCode=status.HTTP_200_OK)


def compute_budget_status(category_id: int, month: str, db: Session, current_user_id: int = Depends(get_current_user)):

    year, mon = map(int, month.split("-"))
    start_date = datetime(year, mon, 1)
    end_date = datetime(year + 1, 1, 1) if mon == 12 else datetime(year, mon + 1, 1)

    budget = db.query(budget_model).filter(
        budget_model.user_id == current_user_id,
        budget_model.category_id == category_id,
        budget_model.month == month
    ).first()

    if not budget:
        return None

    transactions = db.query(transaction_model).filter(
        transaction_model.user_id == current_user_id,
        transaction_model.category_id == category_id,
        transaction_model.date >= start_date,
        transaction_model.date < end_date,
        transaction_model.amount < 0
    ).all()

    spent = sum(abs(t.amount) for t in transactions)
    remaining = budget.monthly_limit - spent
    progress = round((spent / budget.monthly_limit) * 100, 2) if budget.monthly_limit > 0 else 0

    return {
        "category_id": category_id,
        "amount": budget.monthly_limit,
        "spent": spent,
        "remaining": remaining,
        "progress": progress
    }

@router.get("/monthly-status/")
async def get_monthly_budgets( month: str, db: Session = Depends(get_db),current_user_id: int = Depends(get_current_user)):
    budgets = db.query(budget_model).filter(
        budget_model.user_id == current_user_id,
        budget_model.month == month
    ).all()

    results = []
    for b in budgets:
        status = compute_budget_status(b.category_id, month, db, current_user_id)
        if status:
            results.append(status)

    return {"user_id": current_user_id, "month": month, "budgets": results}