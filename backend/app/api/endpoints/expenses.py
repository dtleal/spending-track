from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, date
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.expense import Expense, ExpenseCategory
from pydantic import BaseModel

router = APIRouter()


class ExpenseBase(BaseModel):
    date: datetime
    merchant: str
    amount: float
    category: Optional[ExpenseCategory] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = []


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    category: Optional[ExpenseCategory] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class ExpenseResponse(ExpenseBase):
    id: int
    user_id: int
    invoice_id: Optional[int]
    ai_category: Optional[ExpenseCategory]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[ExpenseResponse])
def list_expenses(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[ExpenseCategory] = None,
    merchant: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """List expenses with filters"""
    query = db.query(Expense).filter(Expense.user_id == current_user.id)
    
    # Apply filters
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    if category:
        query = query.filter(Expense.category == category)
    if merchant:
        query = query.filter(Expense.merchant.ilike(f"%{merchant}%"))
    if min_amount is not None:
        query = query.filter(Expense.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Expense.amount <= max_amount)
    
    expenses = query.order_by(Expense.date.desc()).offset(skip).limit(limit).all()
    return expenses


@router.post("/", response_model=ExpenseResponse)
def create_expense(
    expense_in: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Manually create an expense"""
    expense = Expense(
        user_id=current_user.id,
        **expense_in.dict()
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get expense details"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    return expense


@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Update expense details"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    update_data = expense_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)
    
    expense.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(expense)
    
    return expense


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Delete an expense"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(expense)
    db.commit()
    
    return {"message": "Expense deleted successfully"}


@router.post("/{expense_id}/categorize", response_model=ExpenseResponse)
async def recategorize_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Re-run AI categorization for an expense"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Use AI to recategorize
    from app.core.ai_client import ai_client
    
    try:
        ai_category = await ai_client.categorize_expense(
            expense.merchant,
            expense.amount,
            expense.description
        )
        expense.ai_category = ai_category
        expense.category = ai_category  # Also update the main category
        expense.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(expense)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI categorization failed: {str(e)}")
    
    return expense


@router.post("/categorize-batch")
async def categorize_expenses_batch(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Re-run AI categorization for all uncategorized expenses"""
    from app.core.ai_client import ai_client
    
    # Get all uncategorized expenses for the user
    uncategorized_expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.category == ExpenseCategory.OTHER
    ).all()
    
    if not uncategorized_expenses:
        return {"message": "No uncategorized expenses found", "categorized_count": 0}
    
    # Prepare data for AI
    expense_data = []
    for expense in uncategorized_expenses:
        expense_data.append({
            'id': expense.id,
            'merchant': expense.merchant,
            'amount': float(expense.amount),
            'description': expense.description or ''
        })
    
    try:
        # Get AI categorizations
        categorizations = await ai_client.categorize_expenses_batch(expense_data)
        
        if not categorizations:
            raise HTTPException(status_code=500, detail="AI categorization failed")
        
        # Update expenses with AI categories
        updated_count = 0
        for expense in uncategorized_expenses:
            if expense.id in categorizations:
                new_category = categorizations[expense.id]
                expense.category = new_category
                expense.ai_category = new_category
                expense.updated_at = datetime.utcnow()
                updated_count += 1
        
        db.commit()
        
        return {
            "message": f"Successfully categorized {updated_count} expenses",
            "categorized_count": updated_count,
            "total_uncategorized": len(uncategorized_expenses)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI batch categorization failed: {str(e)}")