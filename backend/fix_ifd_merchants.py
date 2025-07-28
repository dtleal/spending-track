#!/usr/bin/env python3
"""
Script to fix IFD merchant names in the database
"""
import sys
from pathlib import Path
import pandas as pd

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.models.expense import Expense

def main():
    db = SessionLocal()
    try:
        # Read the original CSV to get the mapping
        csv_path = "/app/invoices/fatura-99999999.csv"
        df = pd.read_csv(csv_path)
        
        # Create mapping of cleaned names to original names
        merchant_mapping = {}
        for _, row in df.iterrows():
            original = str(row['lançamento'])
            if original.startswith('IFD*'):
                # Apply the same cleaning logic as the parser
                cleaned = original[4:]  # Remove IFD* prefix
                cleaned = cleaned.strip().title()
                merchant_mapping[cleaned] = original
        
        print(f"Found {len(merchant_mapping)} IFD merchants to fix:")
        for cleaned, original in merchant_mapping.items():
            print(f"  {cleaned} -> {original}")
        
        # Update expenses in database
        updated_count = 0
        for cleaned_name, original_name in merchant_mapping.items():
            expenses = db.query(Expense).filter(Expense.merchant == cleaned_name).all()
            for expense in expenses:
                expense.merchant = original_name
                updated_count += 1
        
        if updated_count > 0:
            db.commit()
            print(f"\nUpdated {updated_count} expenses with original IFD* merchant names")
        else:
            print("\nNo expenses found to update")
        
        # Verify the fix worked
        ifd_expenses = db.query(Expense).filter(
            Expense.merchant.like('IFD*%')
        ).all()
        print(f"\nVerification: Found {len(ifd_expenses)} expenses with IFD* merchants:")
        for expense in ifd_expenses[:5]:  # Show first 5
            print(f"  - {expense.merchant}: R$ {expense.amount}")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()