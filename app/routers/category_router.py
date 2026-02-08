from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.models.tables import category_model, user_model, transaction_model
from app.schema.category_schema import CategoryRead, CategoryCreate
from sqlalchemy.orm import Session 
from datetime import datetime
from app.routers.auth import get_current_user
from app.schema.responseModel import ResponseModel

router = APIRouter(prefix="/category", tags=["Category"])


@router.get('/', response_model=ResponseModel[list[CategoryRead]], status_code=status.HTTP_200_OK)
def get_categories(db : Session = Depends(get_db)):
    categories = db.query(category_model).all()
   
    return ResponseModel(
        message="Categories fetched successfully",
        data=categories,
        status_code=status.HTTP_200_OK
    )

@router.post('/', response_model=ResponseModel[CategoryRead], status_code=status.HTTP_201_CREATED)
def add_category(category : CategoryCreate, db : Session = Depends(get_db)):
    existing_category = db.query(category_model).filter(category_model.name == category.name).first()
    if existing_category:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Category already exists')
    
    new_category = category_model(
        name = category.name
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return ResponseModel(
        message="Category created successfully",
        data=new_category,
        status_code=status.HTTP_201_CREATED
    )


@router.put('/{category_id}', response_model=ResponseModel[CategoryRead], status_code=status.HTTP_200_OK)
def update_category(category_id : int, category :CategoryCreate, db : Session = Depends(get_db)):
    db_category = db.query(category_model).filter(category_model.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Category not found')
    
    existing_category = (
        db.query(category_model)
        .filter(
            category_model.name == category.name,
            category_model.id != category_id
        )
        .first()
    )

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category name already exists"
        )

    db_category.name = category.name
    db.commit()
    db.refresh(db_category)

    return ResponseModel(
        message="Category updated successfully",
        data=db_category,
        status_code=status.HTTP_200_OK
    )

@router.delete('/{category_id}', response_model=ResponseModel[None], status_code=status.HTTP_200_OK)
def delete_category(category_id: int, db : Session = Depends(get_db)):
    db_category = db.query(category_model).filter(category_model.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Category not found')
    
    db.delete(db_category)
    db.commit()

    return ResponseModel(
        message=f"Category with id {category_id} deleted successfully",
        data=None,
        status_code=status.HTTP_200_OK
    )


@router.get('/category_spending', response_model=ResponseModel[dict], status_code=status.HTTP_200_OK)
def get_category_spending(month: str, db: Session = Depends(get_db),current_user_id: int = Depends(get_current_user)):
    try:
        year, month_num = map(int, month.split("-"))
        if not 1 <= month_num <= 12:
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    start = datetime(year, month_num, 1)
    end = datetime(year + (month_num == 12), (month_num % 12) + 1, 1)

    transactions = (
        db.query(transaction_model)
        .join(category_model)
        .filter(
            transaction_model.user_id == current_user_id,
            transaction_model.date >= start,
            transaction_model.date < end
        )
        .all()
    )  

    category_spending = {}
    total_spent = 0     

    for t in transactions:
        # Determine if this transaction is an expense based on the category flag
        if t.category and t.category.is_expense:  
            amount = abs(t.amount)  # expense
            category_spending[t.category.name] = category_spending.get(t.category.name, 0) + amount
            total_spent += amount

    return ResponseModel(
        message="Category-wise spending fetched successfully",
        data={
            "user_id": current_user_id,
            "month": month,
            "category_spending": category_spending,
            "total_spent": total_spent
        },
        status_code=status.HTTP_200_OK
    )