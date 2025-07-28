'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency } from '@/lib/utils'
import { usePrivacyStore } from '@/lib/privacy-store'
import { SpendingSummary } from '@/types'
import { TrendingUp, TrendingDown, DollarSign, CreditCard } from 'lucide-react'

interface QuickStatsProps {
  summary: SpendingSummary
}

export function QuickStats({ summary }: QuickStatsProps) {
  const { isPrivacyMode } = usePrivacyStore()
  const totalSpent = summary.total_spent
  const dailyAverage = summary.daily_average
  const transactionCount = summary.transaction_count
  const topCategory = Object.entries(summary.category_breakdown || {})[0]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Spent</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatCurrency(totalSpent, isPrivacyMode)}</div>
          <p className="text-xs text-muted-foreground">
            Last 30 days
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Daily Average</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatCurrency(dailyAverage, isPrivacyMode)}</div>
          <p className="text-xs text-muted-foreground">
            Per day spending
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Transactions</CardTitle>
          <CreditCard className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{transactionCount}</div>
          <p className="text-xs text-muted-foreground">
            Total transactions
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Top Category</CardTitle>
          <TrendingDown className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {topCategory ? topCategory[0].charAt(0).toUpperCase() + topCategory[0].slice(1) : 'N/A'}
          </div>
          <p className="text-xs text-muted-foreground">
            {topCategory ? formatCurrency(topCategory[1], isPrivacyMode) : 'No data'}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}