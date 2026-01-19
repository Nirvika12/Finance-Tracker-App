from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tables import user_model
from app.schema.user_schema import UserCreate, UserUpdate, UserRead, UserLogin
from datetime import datetime
from passlib.context import CryptContext


router = APIRouter(prefix="/users",tags=['Users'])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

@router.post('/login')
def login(request: UserLogin, db: Session = Depends(get_db)):
    print("Login attempt:", repr(request.email), repr(request.password))
    user = db.query(user_model).filter(user_model.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"message": "Login successful", "user_id": user.id, "name": user.name}


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(request : UserCreate, db: Session = Depends(get_db)):
    user = db.query(user_model).filter(user_model.email == request.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = user_model(
        name = request.name,
        email = request.email,
        password_hash = hash_password(request.password),
        created_at = datetime.now(),
        updated_at = datetime.now()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user_id": new_user.id}

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

@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(user_model).filter(user_model.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
