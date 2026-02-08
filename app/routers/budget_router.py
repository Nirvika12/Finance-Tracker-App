from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schema.budget_schema import BudgetCreate, BudgetStatus, MonthlyBudgetResponse
from app.models.tables import budget_model, transaction_model, category_model
from datetime import datetime
from app.routers.auth import get_current_user
from app.schema.responseModel import ResponseModel
from datetime import datetime

router = APIRouter(prefix="/budget",tags=['Budget'])


def compute_budget_status(category_id: int, month: str, db: Session, current_user_id: int) -> BudgetStatus | None:
  
    # Parse month and get start/end dates
    year, mon = map(int, month.split("-"))
    start_date = datetime(year, mon, 1)
    end_date = datetime(year + 1, 1, 1) if mon == 12 else datetime(year, mon + 1, 1)

    # Fetch the budget record
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
            transaction_model.date < end_date
        ).all()

        # Only sum amounts for expense categories
    spent = sum(abs(t.amount) for t in transactions)

    remaining = budget.monthly_limit - spent
    progress = round((spent / budget.monthly_limit) * 100, 2) if budget.monthly_limit > 0 else 0.0

    return BudgetStatus(
        category_id=category_id,
        amount=budget.monthly_limit,
        spent=spent,
        remaining=remaining,
        progress=progress
    )

    
@router.post("/create-or-update/", response_model=ResponseModel[BudgetStatus], status_code=status.HTTP_201_CREATED)
def create_or_update_budget(budget: BudgetCreate, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    """
    Add a new budget or update an existing budget for the same user, category, and month.
    """

    # Month validation
    try:
        year, mon = map(int, budget.month.split("-"))
        if not 1 <= mon <= 12:
            raise ValueError
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid month format. Use YYYY-MM"
        )
    
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
        budget_status = compute_budget_status(
            budget.category_id, budget.month, db, current_user_id
        )
        return ResponseModel(message="Budget updated successfully", data=budget_status, status_code=status.HTTP_200_OK)

    # Create new budget
    new_budget = budget_model(
        **budget.model_dump(exclude_unset=True),
        user_id=current_user_id
    )
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    budget_status = compute_budget_status(
        budget.category_id, budget.month, db, current_user_id
    )

    return ResponseModel(message="Budget created successfully", data=budget_status, status_code=status.HTTP_201_CREATED)



@router.get("/monthly-status/", response_model=ResponseModel[MonthlyBudgetResponse])
def get_monthly_budgets( month: str, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    
    try:
        year, mon = map(int, month.split("-"))
        if not 1 <= mon <= 12:
            raise ValueError
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid month format. Use YYYY-MM"
        )
    
    budgets = db.query(budget_model).filter(
        budget_model.user_id == current_user_id,
        budget_model.month == month
    ).all()

    results = []
    for b in budgets:
        budget_status = compute_budget_status(b.category_id, month, db, current_user_id)
        if budget_status:
            results.append(budget_status)


    return ResponseModel(
            message="Monthly budgets fetched successfully",
            data=MonthlyBudgetResponse(
                user_id=current_user_id,
                month=month,
                budgets=results
            ),
            status_code=status.HTTP_200_OK
        )