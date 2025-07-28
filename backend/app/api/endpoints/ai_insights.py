from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.expense import Expense
from app.core.ai_client import ai_client
from pydantic import BaseModel

router = APIRouter()


class InsightRequest(BaseModel):
    timeframe_days: int = 30
    focus_areas: Optional[List[str]] = None


class InsightResponse(BaseModel):
    insights: dict
    generated_at: datetime
    timeframe: dict


class ChatRequest(BaseModel):
    message: str
    include_context: bool = True


class ChatResponse(BaseModel):
    response: str
    context_used: bool


class PredictionResponse(BaseModel):
    predictions: dict
    confidence: float
    generated_at: datetime


@router.post("/analyze", response_model=InsightResponse)
async def analyze_spending(
    request: InsightRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get AI-powered spending insights"""
    # Get expenses for the timeframe
    end_date = datetime.now()
    start_date = end_date - timedelta(days=request.timeframe_days)
    
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).all()
    
    if not expenses:
        raise HTTPException(status_code=404, detail="No expenses found for the specified timeframe")
    
    # Prepare data for AI analysis
    expense_data = []
    for expense in expenses:
        expense_data.append({
            "date": expense.date.isoformat(),
            "merchant": expense.merchant,
            "amount": expense.amount,
            "category": expense.category.value if expense.category else "other",
            "ai_category": expense.ai_category.value if expense.ai_category else None
        })
    
    # Get AI insights
    try:
        insights = await ai_client.analyze_spending_patterns(expense_data)
        
        return {
            "insights": insights,
            "generated_at": datetime.now(),
            "timeframe": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": request.timeframe_days
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")


@router.post("/predict", response_model=PredictionResponse)
async def predict_expenses(
    months_ahead: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Predict future expenses using AI"""
    # Get historical data (last 6 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).order_by(Expense.date).all()
    
    if len(expenses) < 30:
        raise HTTPException(
            status_code=400, 
            detail="Insufficient historical data. Need at least 30 transactions for predictions."
        )
    
    # Prepare historical data
    historical_data = []
    monthly_totals = {}
    
    for expense in expenses:
        month_key = expense.date.strftime('%Y-%m')
        if month_key not in monthly_totals:
            monthly_totals[month_key] = {
                "total": 0,
                "count": 0,
                "categories": {}
            }
        
        monthly_totals[month_key]["total"] += expense.amount
        monthly_totals[month_key]["count"] += 1
        
        category = expense.category.value if expense.category else "other"
        if category not in monthly_totals[month_key]["categories"]:
            monthly_totals[month_key]["categories"][category] = 0
        monthly_totals[month_key]["categories"][category] += expense.amount
    
    # Convert to list for AI
    for month, data in sorted(monthly_totals.items()):
        historical_data.append({
            "month": month,
            "total_spent": data["total"],
            "transaction_count": data["count"],
            "category_breakdown": data["categories"]
        })
    
    # Get AI predictions
    try:
        predictions = await ai_client.predict_future_expenses(historical_data)
        
        # Calculate confidence based on data quality
        confidence = min(0.95, 0.5 + (len(expenses) / 1000))  # Max 95% confidence
        
        return {
            "predictions": predictions,
            "confidence": round(confidence, 2),
            "generated_at": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI prediction failed: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Chat with AI financial assistant"""
    context = None
    
    if request.include_context:
        # Get recent spending summary as context
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        expenses = db.query(Expense).filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).all()
        
        if expenses:
            total_spent = sum(e.amount for e in expenses)
            category_totals = {}
            
            for expense in expenses:
                category = expense.category.value if expense.category else "other"
                if category not in category_totals:
                    category_totals[category] = 0
                category_totals[category] += expense.amount
            
            context = {
                "total_spent_30d": total_spent,
                "transaction_count": len(expenses),
                "daily_average": total_spent / 30,
                "top_categories": sorted(
                    category_totals.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:3]
            }
    
    try:
        response = await ai_client.chat_with_financial_assistant(
            request.message,
            context
        )
        
        return {
            "response": response,
            "context_used": request.include_context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/suggestions/merchants/{merchant}")
async def get_merchant_suggestions(
    merchant: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get AI suggestions for categorizing a specific merchant"""
    # Get all expenses from this merchant
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.merchant.ilike(f"%{merchant}%")
    ).all()
    
    if not expenses:
        # Try AI categorization without history
        try:
            category = await ai_client.categorize_expense(merchant, 0)
            return {
                "merchant": merchant,
                "suggested_category": category.value,
                "confidence": "low",
                "based_on": "ai_analysis"
            }
        except:
            raise HTTPException(status_code=404, detail="Could not determine category")
    
    # Analyze historical categorization
    categories = {}
    total_amount = 0
    
    for expense in expenses:
        cat = expense.category.value if expense.category else "other"
        if cat not in categories:
            categories[cat] = {"count": 0, "amount": 0}
        categories[cat]["count"] += 1
        categories[cat]["amount"] += expense.amount
        total_amount += expense.amount
    
    # Sort by frequency
    most_common = sorted(
        categories.items(), 
        key=lambda x: x[1]["count"], 
        reverse=True
    )[0]
    
    return {
        "merchant": merchant,
        "suggested_category": most_common[0],
        "confidence": "high" if most_common[1]["count"] > 5 else "medium",
        "based_on": "historical_data",
        "history": {
            "total_transactions": len(expenses),
            "total_amount": total_amount,
            "category_breakdown": categories
        }
    }