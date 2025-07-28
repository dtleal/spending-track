'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { expensesApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import { Calendar, DollarSign, Filter, Search, Tag, Trash2, AlertCircle, TrendingUp, BarChart3 } from 'lucide-react'
import { format } from 'date-fns'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { usePrivacyStore } from '@/lib/privacy-store'
import { formatCurrency } from '@/lib/utils'

export default function ExpensesPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [updatingExpenseId, setUpdatingExpenseId] = useState<number | null>(null)
  const { isPrivacyMode } = usePrivacyStore()
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: expenses, isLoading } = useQuery({
    queryKey: ['expenses', searchTerm, selectedCategory],
    queryFn: () => expensesApi.list({
      merchant: searchTerm || undefined,
      category: selectedCategory === 'all' ? undefined : selectedCategory,
      limit: 100,
    }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => expensesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      toast({
        title: 'Expense deleted',
        description: 'The expense has been removed successfully.',
      })
    },
  })

  const recategorizeMutation = useMutation({
    mutationFn: (id: number) => expensesApi.recategorize(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      toast({
        title: 'Expense recategorized',
        description: 'AI has updated the category for this expense.',
      })
    },
  })

  const updateCategoryMutation = useMutation({
    mutationFn: ({ id, category }: { id: number; category: string }) => 
      expensesApi.update(id, { category }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      toast({
        title: 'Category updated',
        description: 'The expense category has been updated successfully.',
      })
    },
  })

  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'food', label: 'Food & Dining' },
    { value: 'transport', label: 'Transportation' },
    { value: 'shopping', label: 'Shopping' },
    { value: 'health', label: 'Health & Medical' },
    { value: 'entertainment', label: 'Entertainment' },
    { value: 'utilities', label: 'Utilities & Bills' },
    { value: 'education', label: 'Education' },
    { value: 'other', label: 'Other' },
  ]

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      food: 'bg-orange-100 text-orange-800',
      transport: 'bg-blue-100 text-blue-800',
      shopping: 'bg-pink-100 text-pink-800',
      health: 'bg-red-100 text-red-800',
      entertainment: 'bg-purple-100 text-purple-800',
      utilities: 'bg-gray-100 text-gray-800',
      education: 'bg-green-100 text-green-800',
      other: 'bg-yellow-100 text-yellow-800',
    }
    return colors[category] || 'bg-gray-100 text-gray-800'
  }

  const getCategoryLabel = (value: string) => {
    const category = categories.find(cat => cat.value === value)
    return category?.label || value
  }

  // Count uncategorized expenses
  const uncategorizedExpenses = expenses?.filter(
    (expense: any) => !expense.category || expense.category === 'other'
  ) || []

  const categorizeBatchMutation = useMutation({
    mutationFn: () => expensesApi.categorizeBatch(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      toast({
        title: 'Batch categorization completed',
        description: `${data.categorized_count} expenses categorized successfully with AI.`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Batch categorization failed',
        description: error.response?.data?.detail || 'An error occurred during AI categorization.',
        variant: 'destructive',
      })
    },
  })

  const categorizeAllWithAI = async () => {
    categorizeBatchMutation.mutate()
  }

  // Calculate filtered results statistics
  const filteredStats = expenses ? {
    totalAmount: expenses.reduce((sum: number, expense: any) => sum + expense.amount, 0),
    count: expenses.length,
    averageAmount: expenses.length > 0 ? expenses.reduce((sum: number, expense: any) => sum + expense.amount, 0) / expenses.length : 0,
    dateRange: expenses.length > 0 ? {
      earliest: new Date(Math.min(...expenses.map((e: any) => new Date(e.date).getTime()))),
      latest: new Date(Math.max(...expenses.map((e: any) => new Date(e.date).getTime())))
    } : null,
    topMerchants: expenses.reduce((acc: any, expense: any) => {
      if (!acc[expense.merchant]) {
        acc[expense.merchant] = { amount: 0, count: 0 }
      }
      acc[expense.merchant].amount += expense.amount
      acc[expense.merchant].count += 1
      return acc
    }, {})
  } : null


  const isFiltered = searchTerm || selectedCategory !== 'all'

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Expenses</h1>
        <p className="text-gray-600">View and manage your expenses</p>
      </div>

      {/* Uncategorized Alert */}
      {!isLoading && uncategorizedExpenses.length > 0 && (
        <Alert className="mb-6 border-orange-200 bg-orange-50">
          <AlertCircle className="h-4 w-4 text-orange-600" />
          <AlertTitle className="text-orange-800">
            {uncategorizedExpenses.length} Uncategorized Expense{uncategorizedExpenses.length > 1 ? 's' : ''}
          </AlertTitle>
          <AlertDescription className="text-orange-700">
            <p className="mb-3">
              You have {uncategorizedExpenses.length} expense{uncategorizedExpenses.length > 1 ? 's' : ''} without proper categorization. 
              Categorizing your expenses helps you better understand your spending patterns.
            </p>
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={categorizeAllWithAI}
                disabled={categorizeBatchMutation.isPending}
                className="bg-orange-600 hover:bg-orange-700 text-white"
              >
                <Tag className="h-4 w-4 mr-1" />
                Categorize All with AI
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setSelectedCategory('other')}
                className="border-orange-600 text-orange-600 hover:bg-orange-50"
              >
                Show Only Uncategorized
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
              <Input
                placeholder="Search merchants..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((cat) => (
                  <SelectItem key={cat.value} value={cat.value}>
                    {cat.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {/* Quick Search Buttons */}
          <div className="mt-4">
            <p className="text-sm font-medium text-gray-700 mb-2">Quick Search:</p>
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setSearchTerm('SUPERMERCADO CONFIANCA')}
                className="text-xs"
              >
                🛒 Confiança
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setSearchTerm('IFD*')}
                className="text-xs"
              >
                🍔 iFood
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setSearchTerm('DROGASIL')}
                className="text-xs"
              >
                💊 Drogasil
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setSearchTerm('COMBUSTIVEIS')}
                className="text-xs"
              >
                ⛽ Gas Stations
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setSearchTerm('Paramount')}
                className="text-xs"
              >
                📺 Paramount+
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setSearchTerm('CLAUDE.AI')}
                className="text-xs"
              >
                🤖 Claude AI
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setSearchTerm('')
                  setSelectedCategory('all')
                }}
                className="text-xs border-red-200 text-red-600 hover:bg-red-50"
              >
                ❌ Clear All
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filter Results Summary */}
      {!isLoading && filteredStats && isFiltered && (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Amount</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency(filteredStats.totalAmount, isPrivacyMode)}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Transactions</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {filteredStats.count}
                  </p>
                </div>
                <BarChart3 className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Average</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {formatCurrency(filteredStats.averageAmount, isPrivacyMode)}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Date Range</p>
                  <p className="text-sm font-bold text-gray-800">
                    {filteredStats.dateRange ? (
                      <>
                        {format(filteredStats.dateRange.earliest, 'MMM dd')} - {format(filteredStats.dateRange.latest, 'MMM dd')}
                      </>
                    ) : '-'}
                  </p>
                </div>
                <Calendar className="h-8 w-8 text-gray-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Top Merchants for Filtered Results */}
      {!isLoading && filteredStats && isFiltered && Object.keys(filteredStats.topMerchants).length > 1 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Top Merchants in Filter</CardTitle>
            <CardDescription>
              Merchants with highest spending in current filter
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(filteredStats.topMerchants)
                .sort(([,a]: [string, any], [,b]: [string, any]) => b.amount - a.amount)
                .slice(0, 5)
                .map(([merchant, data]: [string, any]) => (
                  <div key={merchant} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">{merchant}</p>
                      <p className="text-sm text-gray-500">{data.count} transaction{data.count > 1 ? 's' : ''}</p>
                    </div>
                    <p className="font-semibold text-green-600">
                      {formatCurrency(data.amount, isPrivacyMode)}
                    </p>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Expenses List */}
      <Card>
        <CardHeader>
          <CardTitle>All Expenses</CardTitle>
          <CardDescription>
            {expenses?.length || 0} expenses found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-center py-8 text-gray-500">Loading expenses...</p>
          ) : expenses && expenses.length > 0 ? (
            <div className="space-y-2">
              {expenses.map((expense: any) => (
                <div
                  key={expense.id}
                  className={`flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 ${
                    (!expense.category || expense.category === 'other') ? 'border-orange-300 bg-orange-50/50' : ''
                  }`}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <div>
                        <p className="font-medium">{expense.merchant}</p>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <Calendar className="h-3 w-3" />
                          {format(new Date(expense.date), 'MMM dd, yyyy')}
                          {expense.description && (
                            <>
                              <span>•</span>
                              <span>{expense.description}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="flex flex-col items-end gap-2">
                      <p className="font-semibold flex items-center gap-1">
                        <DollarSign className="h-4 w-4" />
                        {formatCurrency(expense.amount, isPrivacyMode)}
                      </p>
                      <Select 
                        value={expense.category || 'other'} 
                        onValueChange={(value) => 
                          updateCategoryMutation.mutate({ id: expense.id, category: value })
                        }
                        disabled={updateCategoryMutation.isPending}
                      >
                        <SelectTrigger className="w-40 h-8 text-xs border-0 focus:ring-0">
                          <span className={`px-2 py-1 rounded ${getCategoryColor(expense.category || 'other')}`}>
                            {getCategoryLabel(expense.category || 'other')}
                          </span>
                        </SelectTrigger>
                        <SelectContent>
                          {categories.slice(1).map((cat) => (
                            <SelectItem key={cat.value} value={cat.value}>
                              <span className={`px-2 py-1 rounded text-xs ${getCategoryColor(cat.value)}`}>
                                {cat.label}
                              </span>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {expense.ai_category && expense.ai_category !== expense.category && (
                        <span className="text-xs text-purple-600">
                          AI suggests: {getCategoryLabel(expense.ai_category)}
                        </span>
                      )}
                    </div>
                    
                    <div className="flex gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => recategorizeMutation.mutate(expense.id)}
                        disabled={recategorizeMutation.isPending}
                        title="Recategorize with AI"
                      >
                        <Tag className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => deleteMutation.mutate(expense.id)}
                        disabled={deleteMutation.isPending}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center py-8 text-gray-500">
              No expenses found. Upload an invoice to get started!
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}