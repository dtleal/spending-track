'use client'

import { useQuery } from '@tanstack/react-query'
import { analyticsApi, expensesApi } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { SpendingChart } from '@/components/charts/spending-chart'
import { CategoryChart } from '@/components/charts/category-chart'
import { RecentTransactions } from '@/components/recent-transactions'
import { QuickStats } from '@/components/quick-stats'
import { useResolvedFilters } from '@/lib/filter-store'

export default function DashboardPage() {
  const { startDate, endDate, cardholder, label } = useResolvedFilters()

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics', 'summary', startDate, endDate, cardholder],
    queryFn: () => analyticsApi.getSummary(startDate, endDate, cardholder),
  })

  const { data: monthlyTrends, isLoading: trendsLoading } = useQuery({
    queryKey: ['analytics', 'monthly-trends', cardholder],
    queryFn: () => analyticsApi.getMonthlyTrends(6, cardholder),
  })

  const { data: recentExpenses, isLoading: expensesLoading } = useQuery({
    queryKey: ['expenses', 'recent', startDate, endDate, cardholder],
    queryFn: () =>
      expensesApi.list({
        limit: 10,
        start_date: startDate,
        end_date: endDate,
        cardholder,
      }),
  })

  if (summaryLoading || trendsLoading || expensesLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome back! Here's your spending overview · {label}
          {cardholder ? ` · ${cardholder}` : ''}
        </p>
      </div>

      {/* Quick Stats */}
      {summary && <QuickStats summary={summary} periodLabel={label} />}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Spending Trends Chart */}
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Spending Trends</CardTitle>
            <CardDescription>
              Your spending over the last 6 months
            </CardDescription>
          </CardHeader>
          <CardContent>
            {monthlyTrends && <SpendingChart data={monthlyTrends} />}
          </CardContent>
        </Card>

        {/* Category Breakdown Chart */}
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Category Breakdown</CardTitle>
            <CardDescription>
              How you're spending by category this month
            </CardDescription>
          </CardHeader>
          <CardContent>
            {summary && <CategoryChart data={summary.category_breakdown} />}
          </CardContent>
        </Card>
      </div>

      {/* Recent Transactions */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Transactions</CardTitle>
          <CardDescription>
            Your latest expenses and transactions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {recentExpenses && <RecentTransactions expenses={recentExpenses} />}
        </CardContent>
      </Card>
    </div>
  )
}