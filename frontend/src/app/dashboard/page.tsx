'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi, expensesApi } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { formatCurrency } from '@/lib/utils'
import { SpendingChart } from '@/components/charts/spending-chart'
import { CategoryChart } from '@/components/charts/category-chart'
import { RecentTransactions } from '@/components/recent-transactions'
import { QuickStats } from '@/components/quick-stats'

export default function DashboardPage() {
  const [timeRange, setTimeRange] = useState('30')
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics', 'summary', timeRange],
    queryFn: () => {
      if (timeRange === 'all') {
        // Don't pass dates to get all data
        return analyticsApi.getSummary()
      }
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - parseInt(timeRange))
      return analyticsApi.getSummary(
        startDate.toISOString().split('T')[0],
        endDate.toISOString().split('T')[0]
      )
    },
  })

  const { data: monthlyTrends, isLoading: trendsLoading } = useQuery({
    queryKey: ['analytics', 'monthly-trends'],
    queryFn: () => analyticsApi.getMonthlyTrends(6),
  })

  const { data: recentExpenses, isLoading: expensesLoading } = useQuery({
    queryKey: ['expenses', 'recent'],
    queryFn: () => expensesApi.list({ limit: 10 }),
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
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here's your spending overview.
          </p>
        </div>
        <Select value={timeRange} onValueChange={setTimeRange}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
            <SelectItem value="90">Last 90 days</SelectItem>
            <SelectItem value="180">Last 6 months</SelectItem>
            <SelectItem value="365">Last year</SelectItem>
            <SelectItem value="all">All time</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Quick Stats */}
      {summary && <QuickStats summary={summary} />}

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