from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List
from app.database import get_db
from app.models.tables import transaction_model, budget_model, category_model
from app.models.tables import user_model

router = APIRouter(prefix="/dashboard", tags=['Dashboard'])

# --- Dashboard KPIs: Balance, Income, Expenses, Remaining Budget ---
@router.get("/kpis/")
def get_dashboard_kpis(user_id: int, month: str = None, db: Session = Depends(get_db)):
    """
    Returns key KPIs for a user: total balance, income, expenses, remaining budget
    """
    today = date.today()
    if not month:
        month = today.strftime("%Y-%m")
    
    # Parse month
    year, mon = map(int, month.split("-"))
    start = datetime(year, mon, 1)
    end = datetime(year+1, 1, 1) if mon == 12 else datetime(year, mon+1, 1)

    # Transactions
    transactions = db.query(transaction_model).filter(
        transaction_model.user_id == user_id,
        transaction_model.date >= start,
        transaction_model.date < end
    ).all()

    total_income = sum(t.amount for t in transactions if t.amount > 0)
    total_expense = sum(abs(t.amount) for t in transactions if t.amount < 0)
    balance = total_income - total_expense

    # Budget
    budgets = db.query(budget_model).filter(
        budget_model.user_id == user_id,
        budget_model.month == month
    ).all()
    total_budget = sum(b.monthly_limit for b in budgets)
    spent_budget = sum(
        sum(abs(t.amount) for t in transactions if t.category_id == b.category_id and t.amount < 0)
        for b in budgets
    )
    remaining_budget = total_budget - spent_budget

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "total_budget": total_budget,
        "spent_budget": spent_budget,
        "remaining_budget": remaining_budget
    }


# --- Expense by Category ---
@router.get("/expenses-category/")
def get_expenses_by_category(user_id: int, start_date: date = None, end_date: date = None, db: Session = Depends(get_db)):
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()

    categories = db.query(category_model).all()
    result = []

    for cat in categories:
        transactions = db.query(transaction_model).filter(
            transaction_model.user_id == user_id,
            transaction_model.category_id == cat.id,
            transaction_model.date >= start_date,
            transaction_model.date <= end_date,
            transaction_model.amount < 0
        ).all()
        total = sum(abs(t.amount) for t in transactions)
        result.append({
            "category_id": cat.id,
            "category_name": cat.name,
            "spent": total
        })
    return result

# --- Income vs Expenses Over Time ---
@router.get("/income-expenses/")
def get_income_expenses_over_time(user_id: int, start_date: date = None, end_date: date = None, db: Session = Depends(get_db)):
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()

    transactions = db.query(transaction_model).filter(
        transaction_model.user_id == user_id,
        transaction_model.date >= start_date,
        transaction_model.date <= end_date
    ).all()

    data = {}
    for t in transactions:
        d = t.date.strftime("%Y-%m-%d")
        if d not in data:
            data[d] = {"Income": 0, "Expense": 0}
        if t.amount > 0:
            data[d]["Income"] += t.amount
        else:
            data[d]["Expense"] += abs(t.amount)
    result = [{"date": k, "income": v["Income"], "expense": v["Expense"]} for k, v in sorted(data.items())]
    return result

# --- Latest Transactions ---
@router.get("/latest/")
def get_latest_transactions(user_id: int, limit: int = 5, db: Session = Depends(get_db)):
    transactions = db.query(transaction_model).filter(
        transaction_model.user_id == user_id
    ).order_by(transaction_model.date.desc()).limit(limit).all()

    result = []
    for t in transactions:
        result.append({
            "id": t.id,
            "description": t.description,
            "amount": t.amount,
            "date": t.date,
            "category_name": t.category.name if t.category else "Unknown"
        })
    return result

@router.get("/budget-category/")
def get_budget_vs_spent_by_category(user_id: int, month: str = None, db: Session = Depends(get_db)):
    """
    Returns the budget vs spent for each category for a user for a given month.
    If month is not provided, defaults to current month.
    """
    # Default to current month if not provided
    if not month:
        month = date.today().strftime("%Y-%m")

    try:
        year, mon = map(int, month.split("-"))
        start_date = datetime(year, mon, 1)
        # End date is first day of next month
        if mon == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, mon + 1, 1)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM.")

    # Fetch all budgets for this user and month
    budgets = db.query(budget_model).filter(
        budget_model.user_id == user_id,
        budget_model.month == month
    ).all()

    if not budgets:
        raise HTTPException(status_code=404, detail="No budgets found for this month.")

    result = []
    for b in budgets:
        # Compute total spent for this category
        transactions = db.query(transaction_model).filter(
            transaction_model.user_id == user_id,
            transaction_model.category_id == b.category_id,
            transaction_model.date >= start_date,
            transaction_model.date < end_date,
            transaction_model.amount < 0  # Only expenses
        ).all()

        spent = sum(abs(t.amount) for t in transactions)
        remaining = b.monthly_limit - spent
        progress = round((spent / b.monthly_limit) * 100, 2) if b.monthly_limit > 0 else 0

        # Fetch category name safely
        category = db.query(category_model).filter(category_model.id == b.category_id).first()
        category_name = category.name if category else "Unknown"

        result.append({
            "category_id": b.category_id,
            "category_name": category_name,
            "budget": b.monthly_limit,
            "spent": spent,
            "remaining": remaining,
            "progress": progress
        })

    return {
        "user_id": user_id,
        "month": month,
        "budgets": result
    }