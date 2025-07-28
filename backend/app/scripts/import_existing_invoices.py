#!/usr/bin/env python3
"""
Script to import existing invoice CSV files into the database
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.models.invoice import Invoice, InvoiceStatus
from app.models.expense import Expense
from app.services.invoice_parser import InvoiceParser
from app.services.expense_categorizer import ExpenseCategorizer


def import_csv_for_user(file_path: str, user_email: str, db: Session):
    """Import a CSV file for a specific user"""
    
    # Find user
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        print(f"User with email {user_email} not found!")
        return
    
    print(f"Importing {file_path} for user {user.email}...")
    
    # Check if invoice already exists
    filename = os.path.basename(file_path)
    existing_invoice = db.query(Invoice).filter(
        Invoice.user_id == user.id,
        Invoice.filename == filename
    ).first()
    
    if existing_invoice:
        print(f"Invoice {filename} already exists for this user. Skipping...")
        return
    
    # Create invoice record
    invoice = Invoice(
        user_id=user.id,
        filename=filename,
        file_path=file_path,
        status=InvoiceStatus.PROCESSING
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    
    try:
        # Parse invoice
        parser = InvoiceParser()
        raw_expenses = parser.parse_csv_invoice(file_path)
        valid_expenses = parser.validate_expenses(raw_expenses)
        
        print(f"Found {len(valid_expenses)} valid expenses")
        
        # Categorize expenses
        categorizer = ExpenseCategorizer()
        
        for expense_data in valid_expenses:
            # Rule-based categorization
            category = categorizer.categorize_by_rules(
                expense_data['merchant'], 
                expense_data['amount']
            )
            
            # Create expense record
            expense = Expense(
                user_id=user.id,
                invoice_id=invoice.id,
                date=expense_data['date'],
                merchant=expense_data['merchant'],
                amount=expense_data['amount'],
                category=category,
                ai_category=category,  # Use rule-based for now
                description=expense_data.get('original_description'),
                expense_metadata=expense_data.get('metadata', {})
            )
            db.add(expense)
        
        # Update invoice status
        invoice.status = InvoiceStatus.PROCESSED
        invoice.processed_at = datetime.utcnow()
        invoice.invoice_metadata = parser.get_summary(valid_expenses)
        
        db.commit()
        print(f"Successfully imported {len(valid_expenses)} expenses from {filename}")
        
    except Exception as e:
        print(f"Error processing invoice: {e}")
        invoice.status = InvoiceStatus.FAILED
        invoice.error_message = str(e)
        db.commit()


def main():
    """Main function to import all CSV files from the invoices folder"""
    # Get database session
    db = SessionLocal()
    
    try:
        # Path to invoices folder
        invoices_folder = Path("/app/invoices")
        
        if not invoices_folder.exists():
            print(f"Invoices folder not found at {invoices_folder}")
            return
        
        # Find all CSV files
        csv_files = list(invoices_folder.glob("*.csv"))
        print(f"Found {len(csv_files)} CSV files in {invoices_folder}")
        
        if not csv_files:
            print("No CSV files found to import")
            return
        
        # Get user email from command line or use default
        user_email = sys.argv[1] if len(sys.argv) > 1 else None
        
        if not user_email:
            # Try to find the first active user
            first_user = db.query(User).filter(User.is_active == True).first()
            if first_user:
                user_email = first_user.email
                print(f"Using first active user: {user_email}")
            else:
                print("No active users found. Please provide user email as argument.")
                return
        
        # Import each CSV file
        for csv_file in csv_files:
            import_csv_for_user(str(csv_file), user_email, db)
        
        print("Import completed!")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()