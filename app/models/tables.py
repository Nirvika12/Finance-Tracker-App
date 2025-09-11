from sqlalchemy import  Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class budget_model(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True, autoincrement = True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    monthly_limit = Column(Float, nullable=False)
    user = relationship("user_model", back_populates="budgets")
    category = relationship("category_model", back_populates="budgets")

class category_model(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, autoincrement = True, index=True)
    name = Column(String, unique=True, nullable=False)

    transactions = relationship("transaction_model", back_populates="category")
    budgets = relationship("budget_model", back_populates="category", cascade="all, delete-orphan")


class transaction_model(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement = True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.now) 
    user = relationship("user_model", back_populates="transactions")
    category = relationship("category_model", back_populates="transactions")

class user_model(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement = True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)
    transactions = relationship("transaction_model", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("budget_model", back_populates="user", cascade="all, delete-orphan")

