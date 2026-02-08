from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tables import user_model
from app.schema.user_schema import UserCreate, UserUpdate, UserRead, UserLogin
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
from app.routers.auth import get_current_user
from app.routers import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.schema.responseModel import ResponseModel

router = APIRouter(prefix="/users", tags=['Users'])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------
# LOGIN
# ---------------------------
@router.post('/login', response_model=ResponseModel[dict])
def login(request: UserLogin, db: Session = Depends(get_db)):
    user = db.query(user_model).filter(user_model.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return ResponseModel(
        message="Login successful",
        data={"access_token": access_token, "token_type": "bearer"},
        status_code=status.HTTP_200_OK
    )


# ---------------------------
# SIGNUP
# ---------------------------
@router.post("/signup", response_model=ResponseModel[dict], status_code=status.HTTP_201_CREATED)
def signup(request: UserCreate, db: Session = Depends(get_db)):
    user = db.query(user_model).filter(user_model.email == request.email).first()
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    new_user = user_model(
        name=request.name,
        email=request.email,
        password_hash=hash_password(request.password),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return ResponseModel(
        message="User created successfully",
        data={"user_id": new_user.id},
        status_code=status.HTTP_201_CREATED
    )


# ---------------------------
# UPDATE CURRENT USER
# ---------------------------
@router.put("/me", response_model=ResponseModel[UserRead])
async def update_user(
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    db_user = db.query(user_model).filter(user_model.id == current_user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.name is not None:
        db_user.name = user.name
    if user.email is not None:
        existing_user = db.query(user_model).filter(
            user_model.email == user.email,
            user_model.id != current_user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        db_user.email = user.email
    if user.password is not None:
        db_user.password_hash = hash_password(user.password)

    db_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_user)

    return ResponseModel(
        message="User updated successfully",
        data=db_user,
        status_code=status.HTTP_200_OK
    )


# ---------------------------
# GET CURRENT USER
# ---------------------------
@router.get("/me", response_model=ResponseModel[UserRead])
def get_user(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    user = db.query(user_model).filter(user_model.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return ResponseModel(
        message="User fetched successfully",
        data=user,
        status_code=status.HTTP_200_OK
    )
