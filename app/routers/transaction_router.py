from fastapi import APIRouter, Depends, HTTPException, Query 
from sqlalchemy.orm import Session, selectinload
from typing import Annotated
from app.database import get_db
from app.schema.transaction_schema import TransactionsCreate, TransactionRead, TransactionsUpdate, TransactionsCategory
from app.schema.user_schema import UserRead, UserResponse
from app.models.tables import transaction_model, user_model
from datetime import date

router = APIRouter(prefix="/transactions", tags=['Transactions'])

@router.post('/')
async def create_transactions(db : Annotated[Session, Depends(get_db)], trans : TransactionsCreate):
    try:
        if trans:
            new_trans = transaction_model(**trans.model_dump(exclude_unset=True))
            db.add(new_trans)
            db.commit()
            db.refresh(new_trans)
            return new_trans
    except:
        pass


@router.get('/by-category', response_model=list[TransactionsCategory])
async def get_transactions_by_category_id(user_id: int, category_id: int, db: Session = Depends(get_db)):
        transactions = db.query(transaction_model).filter(transaction_model.user_id == user_id, transaction_model.category_id == category_id).all()
        if not transactions:
            raise HTTPException(status_code=404, detail="No transactions found for this category")
    
        transactions_with_category = []
        for txn in transactions:
            transactions_with_category.append({
                "amount": txn.amount,
                "description": txn.description,
                "date": txn.date,
                "category_name": txn.category.name if txn.category else "Unknown"
            })
    
        return transactions_with_category

@router.get('/by-date')
async def get_transactions_by_date(start_date: date, end_date: date, db : Session = Depends(get_db)):
    
        transactions_bydate = db.query(transaction_model).filter(transaction_model.date >= start_date, 
                                                                 transaction_model.date <= end_date).all()
        if not transactions_bydate:
             raise HTTPException(status_code=404, detail='No transactions found between this date range.')
        
        return transactions_bydate


@router.put("/update/{tran_id}")
async def update_transactions_byId(tran_id : int, trans : TransactionsUpdate, db : Annotated[Session, Depends(get_db)]):
   
        trans = db.query(transaction_model).filter(transaction_model.id == tran_id).first()

        if not trans:
            raise HTTPException(status_code=404, detail='No transactions found.')
        update_trans = transaction_model(
            category_id = trans.category_id,
            descript = trans.description,
            amount = trans.amount,
            date = trans.date
        )

        db.commit()
        db.refresh(update_trans)
        return {"Message" : "Transaction updated succesfully" , "transaction" : update_trans}

@router.delete("/delete/{tran_id}")
async def delete_transactions_byId(tran_id : int, db : Annotated[Session, Depends(get_db)]):
        trans = db.query(transaction_model).filter(transaction_model.id == tran_id).first()
        if not trans:
            raise HTTPException(status_code=404, detail='No transactions found.')
        
        db.delete(trans)
        db.commit()

        return {"message": f"Transaction with id {tran_id} deleted successfully"}

  

@router.get("/{user_id}", response_model=list[TransactionRead])
async def get_user_transactions(db: Session = Depends(get_db), user_id: int = 0):
    user = db.query(user_model).options(
        selectinload(user_model.transactions).joinedload(transaction_model.category)
    ).filter(user_model.id == user_id).first()

    if not user or not user.transactions:
        raise HTTPException(status_code=404, detail="No transactions found for this user")

    transactions_with_category = []
    for txn in user.transactions:
        transactions_with_category.append({
            "id" : txn.id,
            "amount": txn.amount,
            "description": txn.description,
            "date": txn.date,
            "category_name": txn.category.name if txn.category else "Unknown"
        })

    return transactions_with_category


