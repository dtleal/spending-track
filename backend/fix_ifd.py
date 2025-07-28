#!/usr/bin/env python3
"""
Script to fix IFD* categorization
"""
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.models.expense import Expense, ExpenseCategory
from app.services.expense_categorizer import ExpenseCategorizer

def main():
    db = SessionLocal()
    try:
        # Find expenses with IFD* in merchant name or description
        ifd_expenses = db.query(Expense).filter(
            (Expense.merchant.ilike('%ifd%')) | 
            (Expense.description.ilike('%ifd%'))
        ).all()
        
        print(f'Found {len(ifd_expenses)} expenses with IFD* pattern:')
        
        categorizer = ExpenseCategorizer()
        updated_count = 0
        
        for expense in ifd_expenses:
            old_category = expense.category
            new_category = categorizer.categorize_by_rules(expense.merchant, float(expense.amount))
            
            print(f'- {expense.merchant}: R$ {expense.amount} | {old_category.value} -> {new_category.value}')
            
            if old_category != new_category:
                expense.category = new_category
                expense.ai_category = new_category
                updated_count += 1
        
        if updated_count > 0:
            db.commit()
            print(f'\nUpdated {updated_count} IFD* expenses to FOOD category')
        else:
            print(f'\nAll IFD* expenses already correctly categorized')
            
        # Final categorization stats
        total_expenses = db.query(Expense).count()
        uncategorized = db.query(Expense).filter(Expense.category == ExpenseCategory.OTHER).count()
        categorization_rate = ((total_expenses - uncategorized) / total_expenses * 100) if total_expenses > 0 else 0
        
        print(f'\nFinal Statistics:')
        print(f'   Total expenses: {total_expenses}')
        print(f'   Categorized: {total_expenses - uncategorized}')
        print(f'   Uncategorized: {uncategorized}')
        print(f'   Categorization rate: {categorization_rate:.1f}%')
        
    finally:
        db.close()

if __name__ == "__main__":
    main()