import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from pathlib import Path


class InvoiceParser:
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls']
        
    def parse_csv_invoice(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse CSV invoice file and extract expenses"""
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Standardize column names
            df.columns = df.columns.str.lower().str.strip()
            
            # Expected columns: data, lançamento (merchant), valor (amount)
            if not all(col in df.columns for col in ['data', 'lançamento', 'valor']):
                raise ValueError("CSV must contain columns: data, lançamento, valor")
            
            expenses = []
            
            for _, row in df.iterrows():
                # Skip empty rows
                if pd.isna(row['valor']) or pd.isna(row['lançamento']):
                    continue
                
                # Parse date
                try:
                    date = pd.to_datetime(row['data']).to_pydatetime()
                except:
                    continue
                
                # Parse amount (handle negative values for refunds)
                amount = float(row['valor'])
                
                # Clean merchant name
                merchant = self._clean_merchant_name(str(row['lançamento']))
                
                expense = {
                    'date': date,
                    'merchant': merchant,
                    'amount': amount,  # Keep negative amounts as negative
                    'is_refund': amount < 0,
                    'original_description': str(row['lançamento']),
                    'metadata': {
                        'source': 'csv_import',
                        'row_index': _
                    }
                }
                
                expenses.append(expense)
            
            return expenses
            
        except Exception as e:
            raise Exception(f"Failed to parse CSV invoice: {str(e)}")
    
    def _clean_merchant_name(self, merchant: str) -> str:
        """Clean and standardize merchant names"""
        # Remove common prefixes
        prefixes_to_remove = ['IFD*', 'MP*', 'EC *', 'DL *']
        for prefix in prefixes_to_remove:
            if merchant.startswith(prefix):
                merchant = merchant[len(prefix):]
        
        # Remove trailing numbers and special characters
        merchant = re.sub(r'\s+\d+/\d+$', '', merchant)
        merchant = re.sub(r'\s+\d+$', '', merchant)
        
        # Standardize known merchants
        merchant_mapping = {
            'AMAZONMKTPLC': 'Amazon Marketplace',
            'AMAZON BR': 'Amazon Brasil',
            'MERCADOPAGO': 'Mercado Pago',
            'MERCADOLIVRE': 'Mercado Livre',
            'UBER* TRIP': 'Uber',
            'MC DONALDS': 'McDonald\'s',
            'CLAUDE.AI SUBSCRIPTION': 'Claude AI',
            'APPLE.COM/BILL': 'Apple',
            'Paramount+': 'Paramount Plus',
            'AmazonPrimeBR': 'Amazon Prime',
            'Google One': 'Google One',
        }
        
        for pattern, replacement in merchant_mapping.items():
            if pattern in merchant.upper():
                return replacement
        
        # Title case and trim
        return merchant.strip().title()
    
    def validate_expenses(self, expenses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean parsed expenses"""
        valid_expenses = []
        
        for expense in expenses:
            # Skip zero amounts
            if expense['amount'] == 0:
                continue
            
            # Skip future dates
            if expense['date'] > datetime.now():
                continue
            
            # Add to valid expenses
            valid_expenses.append(expense)
        
        return valid_expenses
    
    def get_summary(self, expenses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics from parsed expenses"""
        if not expenses:
            return {
                'total_expenses': 0,
                'total_amount': 0,
                'refund_count': 0,
                'refund_amount': 0,
                'date_range': None
            }
        
        total_amount = sum(e['amount'] for e in expenses if not e.get('is_refund'))
        refund_amount = sum(e['amount'] for e in expenses if e.get('is_refund'))
        
        dates = [e['date'] for e in expenses]
        
        return {
            'total_expenses': len([e for e in expenses if not e.get('is_refund')]),
            'total_amount': round(total_amount, 2),
            'refund_count': len([e for e in expenses if e.get('is_refund')]),
            'refund_amount': round(refund_amount, 2),
            'date_range': {
                'start': min(dates).isoformat(),
                'end': max(dates).isoformat()
            },
            'unique_merchants': len(set(e['merchant'] for e in expenses))
        }