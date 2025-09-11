from fastapi import APIRouter, Depends, HTTPException, Query # type: ignore
from sqlalchemy.orm import Session, selectinload# type: ignore
from typing import Annotated
from app.database import get_db
from app.schema.transactions_schema import TransactionsCreate, TransactionRead, TransactionsUpdate
from app.schema.user_schema import UserRead
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

@router.get("/")
async def get_transactions(db : Annotated[Session, Depends(get_db)]):
    try:
        trans = db.query(transaction_model).all()

        if not trans:
            raise HTTPException(status_code=404, detail='No transactions found.')
        return trans
    except:
        pass

@router.get('/by-category')
async def get_transactions_by_category_id(user_id: int, category_id: int, db: Session = Depends(get_db)):
        transactions = db.query(transaction_model).filter(transaction_model.user_id == user_id, transaction_model.category_id == category_id).all()
        if not transactions:
            raise HTTPException(status_code=404, detail="No transactions found for this category")
    
        return  transactions

@router.get('/by-date')
async def get_transactions_by_date(start_date: date, end_date: date, db : Session = Depends(get_db)):
    
        transactions_bydate = db.query(transaction_model).filter(transaction_model.date >= start_date, 
                                                                 transaction_model.date <= end_date).first()
        if not transactions_bydate:
             raise HTTPException(status_code=404, detail='No transactions found between this date range.')
        
        return transactions_bydate


@router.put("/{tran_id}")
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

@router.delete("/{tran_id}")
async def delete_transactions_byId(tran_id : int, db : Annotated[Session, Depends(get_db)]):
        trans = db.query(transaction_model).filter(transaction_model.id == tran_id).first()
        if not trans:
            raise HTTPException(status_code=404, detail='No transactions found.')
        
        db.delete(trans)
        db.commit()

        return {"message": f"Transaction with id {tran_id} deleted successfully"}

    
@router.get("/{user_id}", response_model=UserRead)
async def get_user_with_transactions(db : Annotated[Session, Depends(get_db)], user_id: int):
    user =  db.query(user_model).options(selectinload(user_model.transactions)).filter(user_model.id == user_id).first()
    if not user: 
        raise HTTPException(status_code=404, detail="No transactions found for this user")
    return user


