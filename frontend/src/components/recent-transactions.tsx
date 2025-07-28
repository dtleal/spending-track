'use client'

import { formatCurrency, formatDate } from '@/lib/utils'
import { Expense } from '@/types'
import { Badge } from '@/components/ui/badge'

interface RecentTransactionsProps {
  expenses: Expense[]
}

export function RecentTransactions({ expenses }: RecentTransactionsProps) {
  if (!expenses || expenses.length === 0) {
    return (
      <div className="text-center py-6 text-muted-foreground">
        No recent transactions found.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {expenses.map((expense) => (
        <div
          key={expense.id}
          className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
        >
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h4 className="font-medium">{expense.merchant}</h4>
              {expense.category && (
                <Badge variant="secondary">
                  {expense.category.charAt(0).toUpperCase() + expense.category.slice(1)}
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              {formatDate(expense.date)}
            </p>
            {expense.description && (
              <p className="text-xs text-muted-foreground mt-1">
                {expense.description}
              </p>
            )}
          </div>
          <div className="text-right">
            <div className="font-semibold">
              {formatCurrency(expense.amount)}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}