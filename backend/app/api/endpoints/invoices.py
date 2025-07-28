from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.invoice import Invoice, InvoiceStatus
from app.models.expense import Expense
from app.services.invoice_parser import InvoiceParser
from app.services.expense_categorizer import ExpenseCategorizer
from app.core.ai_client import ai_client
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import shutil
import os
from pathlib import Path

router = APIRouter()


class InvoiceResponse(BaseModel):
    id: int
    filename: str
    status: InvoiceStatus
    processed_at: Optional[datetime]
    error_message: Optional[str]
    expense_count: int = 0
    total_amount: float = 0
    
    class Config:
        from_attributes = True


class InvoiceUploadResponse(BaseModel):
    invoice_id: int
    message: str
    summary: dict


@router.post("/upload", response_model=InvoiceUploadResponse)
async def upload_invoice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Upload and process invoice file"""
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are currently supported")
    
    # Create upload directory if it doesn't exist
    upload_dir = Path("uploads") / str(current_user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create invoice record
    invoice = Invoice(
        user_id=current_user.id,
        filename=file.filename,
        file_path=str(file_path),
        status=InvoiceStatus.PENDING
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    
    # Process invoice in background
    background_tasks.add_task(process_invoice_task, invoice.id, str(file_path), db)
    
    # Parse for immediate summary
    parser = InvoiceParser()
    try:
        expenses = parser.parse_csv_invoice(str(file_path))
        summary = parser.get_summary(expenses)
    except:
        summary = {"error": "Failed to parse invoice"}
    
    return {
        "invoice_id": invoice.id,
        "message": "Invoice uploaded successfully and is being processed",
        "summary": summary
    }


async def process_invoice_task(invoice_id: int, file_path: str, db: Session):
    """Background task to process invoice"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        return
    
    try:
        # Update status
        invoice.status = InvoiceStatus.PROCESSING
        db.commit()
        
        # Parse invoice
        parser = InvoiceParser()
        raw_expenses = parser.parse_csv_invoice(file_path)
        valid_expenses = parser.validate_expenses(raw_expenses)
        
        # Categorize expenses
        categorizer = ExpenseCategorizer()
        
        for expense_data in valid_expenses:
            # Rule-based categorization
            category = categorizer.categorize_by_rules(
                expense_data['merchant'], 
                expense_data['amount']
            )
            
            # AI categorization (async)
            try:
                ai_category = await ai_client.categorize_expense(
                    expense_data['merchant'],
                    expense_data['amount'],
                    expense_data.get('original_description')
                )
            except:
                ai_category = category
            
            # Create expense record
            expense = Expense(
                user_id=invoice.user_id,
                invoice_id=invoice.id,
                date=expense_data['date'],
                merchant=expense_data['merchant'],
                amount=expense_data['amount'],
                category=category,
                ai_category=ai_category,
                description=expense_data.get('original_description'),
                expense_metadata=expense_data.get('metadata')
            )
            db.add(expense)
        
        # Update invoice status
        invoice.status = InvoiceStatus.PROCESSED
        invoice.processed_at = datetime.utcnow()
        invoice.invoice_metadata = parser.get_summary(valid_expenses)
        
        db.commit()
        
    except Exception as e:
        invoice.status = InvoiceStatus.FAILED
        invoice.error_message = str(e)
        db.commit()


@router.get("/", response_model=List[InvoiceResponse])
def list_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """List user's invoices"""
    invoices = db.query(Invoice).filter(
        Invoice.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    # Add expense count and total for each invoice
    result = []
    for invoice in invoices:
        invoice_dict = {
            "id": invoice.id,
            "filename": invoice.filename,
            "status": invoice.status,
            "processed_at": invoice.processed_at,
            "error_message": invoice.error_message,
            "expense_count": len(invoice.expenses),
            "total_amount": sum(e.amount for e in invoice.expenses)
        }
        result.append(invoice_dict)
    
    return result


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get invoice details"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return {
        "id": invoice.id,
        "filename": invoice.filename,
        "status": invoice.status,
        "processed_at": invoice.processed_at,
        "error_message": invoice.error_message,
        "expense_count": len(invoice.expenses),
        "total_amount": sum(e.amount for e in invoice.expenses)
    }


@router.delete("/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Delete invoice and associated expenses"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Delete file if exists
    if invoice.file_path and os.path.exists(invoice.file_path):
        os.remove(invoice.file_path)
    
    # Delete invoice (expenses will be cascade deleted)
    db.delete(invoice)
    db.commit()
    
    return {"message": "Invoice deleted successfully"}