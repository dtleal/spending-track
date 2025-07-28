from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models.expense import Expense, ExpenseCategory
from app.models.user import User
import pandas as pd
from collections import defaultdict


class AnalyticsEngine:
    def __init__(self, db: Session):
        self.db = db
    
    def get_spending_summary(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get spending summary for a user within date range"""
        expenses = self.db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).all()
        
        total_spent = sum(e.amount for e in expenses)
        
        # Category breakdown
        category_breakdown = defaultdict(float)
        for expense in expenses:
            category = expense.category or ExpenseCategory.OTHER
            category_breakdown[category.value] += expense.amount
        
        # Top merchants
        merchant_spending = defaultdict(float)
        for expense in expenses:
            merchant_spending[expense.merchant] += expense.amount
        
        top_merchants = sorted(
            merchant_spending.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Daily average
        days_in_period = (end_date - start_date).days + 1
        daily_average = total_spent / days_in_period if days_in_period > 0 else 0
        
        return {
            'total_spent': round(total_spent, 2),
            'transaction_count': len(expenses),
            'daily_average': round(daily_average, 2),
            'category_breakdown': {k: round(v, 2) for k, v in category_breakdown.items()},
            'top_merchants': [
                {'merchant': m, 'amount': round(a, 2)} for m, a in top_merchants
            ],
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
    
    def get_monthly_trends(self, user_id: int, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly spending trends"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        monthly_data = self.db.query(
            extract('year', Expense.date).label('year'),
            extract('month', Expense.date).label('month'),
            func.sum(Expense.amount).label('total'),
            func.count(Expense.id).label('count')
        ).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date
        ).group_by('year', 'month').all()
        
        trends = []
        for row in monthly_data:
            trends.append({
                'year': int(row.year),
                'month': f"{int(row.year)}-{int(row.month):02d}",
                'total_spent': round(float(row.total), 2),
                'transaction_count': row.count,
                'month_name': datetime(int(row.year), int(row.month), 1).strftime('%B %Y')
            })
        
        return sorted(trends, key=lambda x: x['month'])
    
    def get_category_trends(self, user_id: int, months: int = 6) -> Dict[str, List[Dict[str, Any]]]:
        """Get spending trends by category over time"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        expenses = self.db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date
        ).all()
        
        # Group by month and category
        category_monthly = defaultdict(lambda: defaultdict(float))
        
        for expense in expenses:
            month_key = expense.date.strftime('%Y-%m')
            category = (expense.category or ExpenseCategory.OTHER).value
            category_monthly[category][month_key] += expense.amount
        
        # Format for frontend
        trends = {}
        for category, monthly_data in category_monthly.items():
            trends[category] = [
                {
                    'month': month,
                    'amount': round(amount, 2),
                    'month_name': datetime.strptime(month, '%Y-%m').strftime('%B %Y')
                }
                for month, amount in sorted(monthly_data.items())
            ]
        
        return trends
    
    def detect_unusual_spending(self, user_id: int) -> List[Dict[str, Any]]:
        """Detect unusual spending patterns"""
        # Get last 3 months of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        expenses = self.db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date
        ).all()
        
        if len(expenses) < 10:
            return []
        
        # Calculate statistics
        amounts = [e.amount for e in expenses]
        df = pd.DataFrame(amounts, columns=['amount'])
        
        mean = df['amount'].mean()
        std = df['amount'].std()
        
        # Find outliers (expenses > 2 standard deviations from mean)
        unusual = []
        threshold = mean + (2 * std)
        
        for expense in expenses:
            if expense.amount > threshold:
                unusual.append({
                    'id': expense.id,
                    'date': expense.date.isoformat(),
                    'merchant': expense.merchant,
                    'amount': expense.amount,
                    'category': expense.category.value if expense.category else 'other',
                    'deviation': round((expense.amount - mean) / std, 2)
                })
        
        return sorted(unusual, key=lambda x: x['amount'], reverse=True)[:10]
    
    def get_budget_recommendations(self, user_id: int) -> Dict[str, Any]:
        """Generate budget recommendations based on spending history"""
        # Get last 3 months of data
        summary = self.get_spending_summary(
            user_id, 
            datetime.now() - timedelta(days=90),
            datetime.now()
        )
        
        recommendations = {
            'monthly_budget': round(summary['total_spent'] / 3, 2),
            'category_budgets': {},
            'savings_potential': 0,
            'tips': []
        }
        
        # Category-specific recommendations
        for category, amount in summary['category_breakdown'].items():
            monthly_avg = amount / 3
            
            # Suggest 10% reduction for non-essential categories
            if category in ['entertainment', 'shopping', 'food']:
                suggested = monthly_avg * 0.9
                recommendations['category_budgets'][category] = {
                    'current_avg': round(monthly_avg, 2),
                    'suggested': round(suggested, 2)
                }
                recommendations['savings_potential'] += monthly_avg * 0.1
            else:
                recommendations['category_budgets'][category] = {
                    'current_avg': round(monthly_avg, 2),
                    'suggested': round(monthly_avg, 2)
                }
        
        recommendations['savings_potential'] = round(recommendations['savings_potential'], 2)
        
        # Generate tips based on spending patterns
        if summary['category_breakdown'].get('food', 0) > summary['total_spent'] * 0.3:
            recommendations['tips'].append("Your food expenses are over 30% of total spending. Consider meal planning to reduce costs.")
        
        if summary['category_breakdown'].get('entertainment', 0) > summary['total_spent'] * 0.15:
            recommendations['tips'].append("Entertainment spending is high. Look for free or low-cost alternatives.")
        
        if summary['daily_average'] > 100:
            recommendations['tips'].append("Your daily average spending is over $100. Review your expenses for potential savings.")
        
        return recommendations
    
    def export_data(self, user_id: int, format: str = 'csv', start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Any:
        """Export expense data in various formats"""
        query = self.db.query(Expense).filter(Expense.user_id == user_id)
        
        if start_date:
            query = query.filter(Expense.date >= start_date)
        if end_date:
            query = query.filter(Expense.date <= end_date)
        
        expenses = query.all()
        
        # Convert to DataFrame
        data = []
        for expense in expenses:
            data.append({
                'date': expense.date,
                'merchant': expense.merchant,
                'amount': expense.amount,
                'category': expense.category.value if expense.category else 'other',
                'description': expense.description or '',
                'tags': ','.join(expense.tags) if expense.tags else ''
            })
        
        df = pd.DataFrame(data)
        
        if format == 'csv':
            return df.to_csv(index=False)
        elif format == 'json':
            return df.to_json(orient='records', date_format='iso')
        elif format == 'excel':
            # Return bytes for Excel file
            import io
            buffer = io.BytesIO()
            df.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            return buffer.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")