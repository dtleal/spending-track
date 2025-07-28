from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Float, JSON, Enum
from sqlalchemy.orm import relationship
import enum
from app.db.base import BaseModel


class ExpenseCategory(str, enum.Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    SHOPPING = "shopping"
    HEALTH = "health"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    EDUCATION = "education"
    OTHER = "other"


class Expense(BaseModel):
    __tablename__ = "expenses"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    date = Column(DateTime(timezone=True), nullable=False)
    merchant = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(Enum(ExpenseCategory), default=ExpenseCategory.OTHER)
    ai_category = Column(Enum(ExpenseCategory))
    description = Column(String)
    tags = Column(JSON)
    expense_metadata = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="expenses")
    invoice = relationship("Invoice", back_populates="expenses")