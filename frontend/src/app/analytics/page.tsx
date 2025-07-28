'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { TrendingUp, TrendingDown, DollarSign, ShoppingCart, Calendar } from 'lucide-react'
import { format } from 'date-fns'
import { usePrivacyStore } from '@/lib/privacy-store'
import { formatCurrency } from '@/lib/utils'

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState('30')
  const { isPrivacyMode } = usePrivacyStore()

  const { data: summary } = useQuery({
    queryKey: ['analytics-summary', timeRange],
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

  const { data: monthlyTrends } = useQuery({
    queryKey: ['analytics-monthly'],
    queryFn: () => analyticsApi.getMonthlyTrends(6),
  })

  const { data: categoryTrends } = useQuery({
    queryKey: ['analytics-category'],
    queryFn: () => analyticsApi.getCategoryTrends(3),
  })

  const { data: unusualSpending } = useQuery({
    queryKey: ['analytics-unusual'],
    queryFn: () => analyticsApi.getUnusualSpending(),
  })

  const { data: budgetRecommendations } = useQuery({
    queryKey: ['analytics-budget'],
    queryFn: () => analyticsApi.getBudgetRecommendations(),
  })

  const COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#DDA0DD', '#98D8C8', '#F7DC6F']

  const formatAnalyticsCurrency = (value: number | undefined | null) => {
    if (value === undefined || value === null || isNaN(value)) {
      return formatCurrency(0, isPrivacyMode)
    }
    return formatCurrency(value, isPrivacyMode)
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-gray-600 dark:text-gray-400">Insights and trends from your spending data</p>
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

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Spent</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold flex items-center gap-2">
              <DollarSign className="h-5 w-5" />
              {summary ? formatAnalyticsCurrency(summary.total_spent) : '-'}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {summary?.transaction_count || 0} transactions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">Daily Average</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              {summary ? formatAnalyticsCurrency(summary.daily_average) : '-'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">Top Category</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {summary?.category_breakdown && Object.keys(summary.category_breakdown).length > 0
                ? Object.entries(summary.category_breakdown)
                    .sort(([, a], [, b]) => (b as number) - (a as number))[0][0]
                : '-'}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {summary?.category_breakdown && Object.keys(summary.category_breakdown).length > 0 &&
                formatAnalyticsCurrency(
                  Object.entries(summary.category_breakdown)
                    .sort(([, a], [, b]) => (b as number) - (a as number))[0][1] as number
                )}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">Top Merchant</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-bold truncate">
              {summary?.top_merchants?.[0]?.merchant || '-'}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {summary?.top_merchants?.[0]?.amount !== undefined && 
                formatAnalyticsCurrency(summary.top_merchants[0].amount)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Trends */}
        <Card>
          <CardHeader>
            <CardTitle>Monthly Spending Trends</CardTitle>
            <CardDescription>Your spending over the last 6 months</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={monthlyTrends}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis 
                  dataKey="month" 
                  tickFormatter={(value) => format(new Date(value + '-01'), 'MMM')}
                  tick={{ fill: 'hsl(var(--foreground))' }}
                />
                <YAxis tickFormatter={(value) => formatAnalyticsCurrency(value)} tick={{ fill: 'hsl(var(--foreground))' }} />
                <Tooltip 
                  formatter={(value) => [formatAnalyticsCurrency(Number(value)), 'Amount']}
                  labelFormatter={(label) => `Month: ${format(new Date(label + '-01'), 'MMM yyyy')}`}
                  contentStyle={{
                    backgroundColor: 'hsl(var(--background))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    color: 'hsl(var(--foreground))',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                  itemStyle={{
                    color: 'hsl(var(--foreground))',
                  }}
                  labelStyle={{
                    color: 'hsl(var(--foreground))',
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="total_spent" 
                  stroke="#4ECDC4" 
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Category Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Spending by Category</CardTitle>
            <CardDescription>Where your money goes</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={summary?.category_breakdown ? 
                    Object.entries(summary.category_breakdown).map(([category, amount]) => ({
                      name: category,
                      value: amount as number,
                    })) : []
                  }
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {summary?.category_breakdown && 
                    Object.entries(summary.category_breakdown).map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))
                  }
                </Pie>
                <Tooltip 
                  formatter={(value) => [formatAnalyticsCurrency(Number(value)), 'Amount']}
                  labelFormatter={(label) => `Category: ${label}`}
                  contentStyle={{
                    backgroundColor: 'hsl(var(--background))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    color: 'hsl(var(--foreground))',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                  itemStyle={{
                    color: 'hsl(var(--foreground))',
                  }}
                  labelStyle={{
                    color: 'hsl(var(--foreground))',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Category Trends Over Time */}
        {categoryTrends && Object.keys(categoryTrends).length > 0 && (
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Category Trends</CardTitle>
              <CardDescription>How your spending in each category changes over time</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart 
                  data={(() => {
                    // Transform the data structure for the bar chart
                    const months = new Set<string>()
                    Object.values(categoryTrends).forEach((categoryData: any) => {
                      categoryData.forEach((item: any) => months.add(item.month))
                    })
                    
                    return Array.from(months).sort().map(month => {
                      const monthData: any = { month }
                      Object.entries(categoryTrends).forEach(([category, data]: [string, any]) => {
                        const monthItem = data.find((item: any) => item.month === month)
                        monthData[category] = monthItem ? monthItem.amount : 0
                      })
                      return monthData
                    })
                  })()}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis 
                    dataKey="month" 
                    tickFormatter={(value) => format(new Date(value + '-01'), 'MMM')}
                    tick={{ fill: 'hsl(var(--foreground))' }}
                  />
                  <YAxis tickFormatter={(value) => formatAnalyticsCurrency(value)} tick={{ fill: 'hsl(var(--foreground))' }} />
                  <Tooltip 
                    formatter={(value) => [formatAnalyticsCurrency(Number(value)), 'Amount']}
                    labelFormatter={(label) => `Month: ${format(new Date(label + '-01'), 'MMM yyyy')}`}
                    contentStyle={{
                      backgroundColor: 'hsl(var(--background))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      color: 'hsl(var(--foreground))',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    }}
                    itemStyle={{
                      color: 'hsl(var(--foreground))',
                    }}
                    labelStyle={{
                      color: 'hsl(var(--foreground))',
                    }}
                  />
                  <Legend />
                  {Object.keys(categoryTrends).map((category, index) => (
                    <Bar 
                      key={category} 
                      dataKey={category} 
                      fill={COLORS[index % COLORS.length]} 
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Unusual Spending */}
        {unusualSpending && unusualSpending.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Unusual Spending Detected</CardTitle>
              <CardDescription>Transactions that stand out from your patterns</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {unusualSpending.slice(0, 5).map((item: any, index: number) => (
                  <div key={index} className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">{item.merchant}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {format(new Date(item.date), 'MMM dd')} • {item.reason}
                      </p>
                    </div>
                    <p className="font-semibold text-red-600">
                      {formatAnalyticsCurrency(item.amount)}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Budget Recommendations */}
        {budgetRecommendations && (
          <Card>
            <CardHeader>
              <CardTitle>Budget Recommendations</CardTitle>
              <CardDescription>AI-powered suggestions for your budget</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(budgetRecommendations).map(([category, data]: [string, any]) => (
                  <div key={category} className="space-y-1">
                    <div className="flex justify-between items-center">
                      <p className="font-medium capitalize">{category}</p>
                      <p className="text-sm">
                        Current: {formatAnalyticsCurrency(data?.current_avg)} → 
                        Suggested: {formatAnalyticsCurrency(data?.suggested)}
                      </p>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          (data?.current_avg || 0) > (data?.suggested || 0) ? 'bg-red-500' : 'bg-green-500'
                        }`}
                        style={{ 
                          width: data?.current_avg && data.current_avg > 0 
                            ? `${Math.min((data.suggested / data.current_avg) * 100, 100)}%` 
                            : '0%'
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}