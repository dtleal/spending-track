#!/usr/bin/env python3
"""
Debug script to check what's in the database
"""
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.models.expense import Expense

def main():
    db = SessionLocal()
    try:
        # Check all expenses
        all_expenses = db.query(Expense).all()
        print(f'Total expenses: {len(all_expenses)}')
        
        # Find IFD expenses
        ifd_expenses = db.query(Expense).filter(
            Expense.merchant.ilike('%IFD%')
        ).all()
        print(f'IFD expenses found: {len(ifd_expenses)}')
        
        for expense in ifd_expenses:
            print(f'- {expense.merchant}: R$ {expense.amount}')
        
        # Check all unique merchants that contain 'ifd' (case insensitive)
        print("\nAll merchants containing 'ifd':")
        for expense in all_expenses:
            if 'ifd' in expense.merchant.lower():
                print(f'- {expense.merchant}')
        
        # Check some sample merchants
        print(f"\nFirst 20 merchants:")
        for expense in all_expenses[:20]:
            print(f'- {expense.merchant}')
        
        # Get unique merchants
        print(f"\nAll unique merchants:")
        unique_merchants = set()
        for expense in all_expenses:
            unique_merchants.add(expense.merchant)
        
        for merchant in sorted(unique_merchants):
            print(f'- {merchant}')
            
    finally:
        db.close()

if __name__ == "__main__":
    main()