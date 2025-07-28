from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
import enum
from app.db.base import BaseModel


class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Invoice(BaseModel):
    __tablename__ = "invoices"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.PENDING)
    processed_at = Column(DateTime(timezone=True))
    error_message = Column(String)
    invoice_metadata = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="invoices")
    expenses = relationship("Expense", back_populates="invoice")