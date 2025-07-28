from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)  # Made nullable for Google OAuth
    hashed_password = Column(String, nullable=True)  # Made nullable for Google OAuth
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Google OAuth fields
    google_id = Column(String, unique=True, index=True, nullable=True)
    profile_picture = Column(String, nullable=True)
    
    # Relationships
    invoices = relationship("Invoice", back_populates="user")
    expenses = relationship("Expense", back_populates="user")