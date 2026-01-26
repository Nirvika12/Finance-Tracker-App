from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from typing import Annotated
from datetime import date
from app.database import get_db
from app.schema.transaction_schema import TransactionsCreate, TransactionRead, TransactionsUpdate, TransactionsCategory
from app.models.tables import transaction_model, user_model
from app.routers.auth import get_current_user

router = APIRouter(prefix="/transactions", tags=['Transactions'])

# ---------------------------
# Create a new transaction
# ---------------------------
@router.post('/', response_model=TransactionRead)
async def create_transactions(
    trans: TransactionsCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user_id: int = Depends(get_current_user)
):
    try:
        new_trans = transaction_model(**trans.model_dump(exclude_unset=True), user_id=current_user_id)
        db.add(new_trans)
        db.commit()
        db.refresh(new_trans)
        return new_trans
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating transaction: {e}")


# ---------------------------
# Get transactions by category
# ---------------------------
@router.get('/by-category', response_model=list[TransactionsCategory])
async def get_transactions_by_category_id(
    category_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    transactions = db.query(transaction_model).filter(
        transaction_model.user_id == current_user_id,
        transaction_model.category_id == category_id
    ).all()

    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found for this category")

    return [
        {
            "id": txn.id,
            "amount": txn.amount,
            "description": txn.description,
            "date": txn.date,
            "category_name": txn.category.name if txn.category else "Unknown",
            "is_expense": txn.category.is_expense if txn.category else True
        }
        for txn in transactions
    ]


# ---------------------------
# Get transactions by date range
# ---------------------------
@router.get('/by-date', response_model=list[TransactionsCategory])
async def get_transactions_by_date(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    transactions_bydate = db.query(transaction_model).filter(
        transaction_model.user_id == current_user_id,
        transaction_model.date >= start_date,
        transaction_model.date <= end_date
    ).all()

    if not transactions_bydate:
        raise HTTPException(status_code=404, detail='No transactions found between this date range.')

    return [
        {
            "id": txn.id,
            "amount": txn.amount,
            "description": txn.description,
            "date": txn.date,
            "category_name": txn.category.name if txn.category else "Unknown",
            "is_expense": txn.category.is_expense if txn.category else True
        }
        for txn in transactions_bydate
    ]


# ---------------------------
# Update a transaction
# ---------------------------
@router.put("/update/{tran_id}", response_model=TransactionRead)
async def update_transactions_byId(
    tran_id: int,
    trans: TransactionsUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user_id: int = Depends(get_current_user)
):
    db_trans = db.query(transaction_model).filter(
        transaction_model.id == tran_id,
        transaction_model.user_id == current_user_id
    ).first()

    if not db_trans:
        raise HTTPException(status_code=404, detail='Transaction not found or not yours.')

    db_trans.description = trans.description
    db_trans.amount = trans.amount
    db_trans.category_id = trans.category_id
    db_trans.date = trans.date

    db.commit()
    db.refresh(db_trans)
    return db_trans


# ---------------------------
# Delete a transaction
# ---------------------------
@router.delete("/delete/{tran_id}")
async def delete_transactions_byId(
    tran_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user_id: int = Depends(get_current_user)
):
    db_trans = db.query(transaction_model).filter(
        transaction_model.id == tran_id,
        transaction_model.user_id == current_user_id
    ).first()

    if not db_trans:
        raise HTTPException(status_code=404, detail='Transaction not found or not yours.')

    db.delete(db_trans)
    db.commit()
    return {"message": f"Transaction with id {tran_id} deleted successfully"}


# ---------------------------
# Get all transactions for current user
# ---------------------------
@router.get("/me", response_model=list[TransactionRead])
async def get_user_transactions(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    user = db.query(user_model).options(
        selectinload(user_model.transactions).joinedload(transaction_model.category)
    ).filter(user_model.id == current_user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return [
        {
            "id": txn.id,
            "amount": txn.amount,
            "description": txn.description,
            "date": txn.date,
            "category_name": txn.category.name if txn.category else "Unknown",
            "is_expense": txn.category.is_expense if txn.category else True
        }
        for txn in user.transactions
    ]
