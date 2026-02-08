from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from typing import Annotated
from datetime import date, datetime
from app.database import get_db
from app.schema.transaction_schema import TransactionsCreate, TransactionRead, TransactionsUpdate
from app.models.tables import transaction_model, user_model
from app.routers.auth import get_current_user
from app.schema.responseModel import ResponseModel

router = APIRouter(prefix="/transactions", tags=['Transactions'])


def format_transaction(txn: transaction_model) -> TransactionRead:
    return TransactionRead(
        id=txn.id,
        amount=txn.amount,
        description=txn.description,
        date=txn.date,
        category_name=txn.category.name if txn.category else "Unknown",
        is_expense=txn.category.is_expense if txn.category else True
    )


# ---------------------------
# Create a new transaction
# ---------------------------
@router.post('/', response_model=ResponseModel[TransactionRead], status_code=status.HTTP_201_CREATED)
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
        return ResponseModel(
            message="Transaction created successfully",
            data=format_transaction(new_trans),
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating transaction: {e}")


# ---------------------------
# Get transactions by category
# ---------------------------
@router.get('/by-category', response_model=ResponseModel[dict])
async def get_transactions_by_category_id(
    category_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    query = db.query(transaction_model).filter(
        transaction_model.user_id == current_user_id,
        transaction_model.category_id == category_id
    )
    total = query.count()
    transactions = query.order_by(transaction_model.date.desc()).offset(skip).limit(limit).all()

    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found for this category")

    return ResponseModel(
        message=f"Transactions for category {category_id} fetched successfully",
        data={"transactions": [format_transaction(txn) for txn in transactions], "total": total},
        status_code=status.HTTP_200_OK
    )


# ---------------------------
# Get transactions by date range
# ---------------------------
@router.get('/by-date', response_model=ResponseModel[dict])
async def get_transactions_by_date(
    start_date: date,
    end_date: date,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    query = db.query(transaction_model).filter(
        transaction_model.user_id == current_user_id,
        transaction_model.date >= start_datetime,
        transaction_model.date <= end_datetime
    )
    total = query.count()
    transactions_bydate = query.order_by(transaction_model.date.desc()).offset(skip).limit(limit).all()

    if not transactions_bydate:
        raise HTTPException(status_code=404, detail='No transactions found between this date range.')

    return ResponseModel(
        message="Transactions fetched for the given date range successfully",
        data={"transactions": [format_transaction(txn) for txn in transactions_bydate], "total": total},
        status_code=status.HTTP_200_OK
    )


# ---------------------------
# Update a transaction
# ---------------------------
@router.put("/update/{tran_id}", response_model=ResponseModel[TransactionRead])
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
    return ResponseModel(
        message="Transaction updated successfully",
        data=format_transaction(db_trans),
        status_code=status.HTTP_200_OK
    )


# ---------------------------
# Delete a transaction
# ---------------------------
@router.delete("/delete/{tran_id}", response_model=ResponseModel[dict])
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
    return ResponseModel(
        message=f"Transaction with id {tran_id} deleted successfully",
        data={"transaction_id": tran_id},
        status_code=status.HTTP_200_OK
    )


# ---------------------------
# Get all transactions for current user
# ---------------------------
@router.get("/me", response_model=ResponseModel[dict])
async def get_user_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    user = db.query(user_model).options(
        selectinload(user_model.transactions).joinedload(transaction_model.category)
    ).filter(user_model.id == current_user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total = len(user.transactions)
    transactions = sorted(user.transactions, key=lambda t: t.date, reverse=True)[skip: skip + limit]

    return ResponseModel(
        message="User transactions fetched successfully",
        data={"transactions": [format_transaction(txn) for txn in transactions], "total": total},
        status_code=status.HTTP_200_OK
    )
