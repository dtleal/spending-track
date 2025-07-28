from fastapi import APIRouter
from app.api.endpoints import auth, invoices, expenses, analytics, ai_insights

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(ai_insights.router, prefix="/ai", tags=["ai"])