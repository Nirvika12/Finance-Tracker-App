from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tables import user_model
from app.schema.user_schema import UserCreate, UserUpdate
from datetime import datetime

router = APIRouter(prefix="/users",tags=['Users'])

@router.get('/')
async def get_users(db : Session = Depends(get_db)):
    users = db.query(user_model).all()

    if not users:
        raise HTTPException(status_code=404, detail='No users found.')
    return users

@router.post('/')
async def create_users(user : UserCreate, db : Session = Depends(get_db)):
    existing_user = db.query(user_model).filter(user_model.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=404, detail='Email already exists')
    
    new_user = user_model(**user.model_dump(exclude_unset=True))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.put('/{user_id}')
async def update_user(user_id : int, user : UserUpdate, db : Session = Depends(get_db)):
    db_user = db.query(user_model).filter(user_model.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.name is not None:
        db_user.name = user.name
    if user.email is not None:
        existing_user = db.query(user_model).filter(user_model.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=404, detail='Email already exists')
        db_user.email = user.email

    if user.password_hash is not None:
        db_user.password_hash = user.password_hash

    db_user.updated_at = datetime.now()

    db.commit()
    db.refresh(db_user)

    return {"message": "User updated successfully", "user": db_user}

#selectinload , withloadercritieria, 