export enum ExpenseCategory {
  FOOD = 'food',
  TRANSPORT = 'transport',
  SHOPPING = 'shopping',
  HEALTH = 'health',
  ENTERTAINMENT = 'entertainment',
  UTILITIES = 'utilities',
  EDUCATION = 'education',
  OTHER = 'other',
}

export interface Expense {
  id: number
  user_id: number
  invoice_id?: number
  date: string
  merchant: string
  amount: number
  category?: ExpenseCategory
  ai_category?: ExpenseCategory
  description?: string
  tags?: string[]
  created_at: string
  updated_at?: string
}

export interface Invoice {
  id: number
  filename: string
  status: 'pending' | 'processing' | 'processed' | 'failed'
  processed_at?: string
  error_message?: string
  expense_count: number
  total_amount: number
}

export interface SpendingSummary {
  total_spent: number
  transaction_count: number
  daily_average: number
  category_breakdown: Record<string, number>
  top_merchants: Array<{ merchant: string; amount: number }>
  date_range: {
    start: string
    end: string
  }
}

export interface MonthlyTrend {
  year: number
  month: number
  total_spent: number
  transaction_count: number
  month_name: string
}

export interface BudgetRecommendation {
  monthly_budget: number
  category_budgets: Record<string, number>
  savings_potential: number
  tips: string[]
}