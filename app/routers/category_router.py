from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.models.tables import category_model
from app.schema.category_schema import CategoryRead, CategoryCreate
from sqlalchemy.orm import Session


router = APIRouter(prefix="/category",tags=['Category'])

@router.get('/')
def get_categories(db : Session = Depends(get_db)):
    categories = db.query(category_model).all()
    if not categories:
        raise HTTPException(status_code=404, detail='No Category exists')
    
    return categories

@router.post('/')
def add_category(category : CategoryCreate, db : Session = Depends(get_db)):
    existing_category = db.query(category_model).filter(category_model.name == category.name).first()
    if existing_category:
        raise HTTPException(status_code=404, detail='Category already exists')
    
    new_category = category_model(
        name = category.name
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.put('/{category_id}')
def update_category(category_id : int, category :CategoryCreate, db : Session = Depends(get_db)):
    db_category = db.query(category_model).filter(category_model.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail='Category not found')
    db_category.name = category.name
    db.commit()
    db.refresh(db_category)

    return {"message": "Category updated successfully", "category": db_category}

@router.delete('/{category_id}')
async def delete_category(category_id: int, db : Session = Depends(get_db)):
    db_category = db.query(category_model).filter(category_model.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail='Category not found')
    
    db.delete(db_category)
    db.commit()

    return {"message": f"Category with id {category_id} deleted successfully"}



