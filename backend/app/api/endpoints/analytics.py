from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.expense import Expense
from app.services.analytics_engine import AnalyticsEngine
from pydantic import BaseModel

router = APIRouter()


class SpendingSummaryResponse(BaseModel):
    total_spent: float
    transaction_count: int
    daily_average: float
    category_breakdown: dict
    top_merchants: list
    date_range: dict


class MonthlyTrendResponse(BaseModel):
    year: int
    month: int
    total_spent: float
    transaction_count: int
    month_name: str


class BudgetRecommendationResponse(BaseModel):
    monthly_budget: float
    category_budgets: dict
    savings_potential: float
    tips: list


@router.get("/summary", response_model=SpendingSummaryResponse)
def get_spending_summary(
    start_date: Optional[date] = Query(None, description="Start date (defaults to 30 days ago)"),
    end_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    all_time: bool = Query(False, description="Get all time data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get spending summary for date range"""
    # Handle all time data
    if all_time or (not start_date and not end_date):
        # Get the earliest expense date for this user
        earliest_expense = db.query(Expense).filter(
            Expense.user_id == current_user.id
        ).order_by(Expense.date.asc()).first()
        
        if earliest_expense:
            start_datetime = datetime.combine(earliest_expense.date, datetime.min.time())
            end_datetime = datetime.now()
        else:
            # No expenses, use default range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
    else:
        # Default date range
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Convert to datetime
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
    
    analytics = AnalyticsEngine(db)
    summary = analytics.get_spending_summary(current_user.id, start_datetime, end_datetime)
    
    return summary


@router.get("/trends/monthly")
def get_monthly_trends(
    months: int = Query(12, ge=1, le=24, description="Number of months to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get monthly spending trends"""
    analytics = AnalyticsEngine(db)
    trends = analytics.get_monthly_trends(current_user.id, months)
    return trends


@router.get("/trends/category")
def get_category_trends(
    months: int = Query(6, ge=1, le=12, description="Number of months to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get spending trends by category"""
    analytics = AnalyticsEngine(db)
    trends = analytics.get_category_trends(current_user.id, months)
    return trends


@router.get("/unusual")
def detect_unusual_spending(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Detect unusual spending patterns"""
    analytics = AnalyticsEngine(db)
    unusual = analytics.detect_unusual_spending(current_user.id)
    return unusual


@router.get("/budget/recommendations", response_model=BudgetRecommendationResponse)
def get_budget_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get AI-powered budget recommendations"""
    analytics = AnalyticsEngine(db)
    recommendations = analytics.get_budget_recommendations(current_user.id)
    return recommendations


@router.get("/export")
def export_data(
    format: str = Query("csv", regex="^(csv|json|excel)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Export expense data"""
    analytics = AnalyticsEngine(db)
    
    # Convert dates to datetime if provided
    start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
    end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
    
    try:
        data = analytics.export_data(current_user.id, format, start_datetime, end_datetime)
        
        # Set appropriate content type and filename
        if format == "csv":
            media_type = "text/csv"
            filename = f"expenses_{datetime.now().strftime('%Y%m%d')}.csv"
        elif format == "json":
            media_type = "application/json"
            filename = f"expenses_{datetime.now().strftime('%Y%m%d')}.json"
        else:  # excel
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"expenses_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return Response(
            content=data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")