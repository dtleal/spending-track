import axios from 'axios'
import { useAuthStore } from '@/lib/auth-store'
import type {
  Expense,
  SpendingSummary,
  MonthlyTrend,
  BudgetRecommendation,
} from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
})

// Attach the bearer token from the auth store to every request.
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Log the user out on a 401 so the auth guard can redirect to /login.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      useAuthStore.getState().logout()
    }
    return Promise.reject(error)
  }
)

export interface ExpenseFilters {
  skip?: number
  limit?: number
  start_date?: string
  end_date?: string
  category?: string
  merchant?: string
  cardholder?: string
  min_amount?: number
  max_amount?: number
}

export interface RegisterData {
  email: string
  username: string
  password: string
  full_name?: string
}

export const authApi = {
  // The backend login endpoint expects OAuth2 form-encoded credentials.
  login: async (username: string, password: string) => {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    const { data } = await api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data as { access_token: string; token_type: string }
  },
  register: async (payload: RegisterData) => {
    const { data } = await api.post('/auth/register', payload)
    return data
  },
  me: async () => {
    const { data } = await api.get('/auth/me')
    return data
  },
}

export const expensesApi = {
  list: async (filters: ExpenseFilters = {}) => {
    const { data } = await api.get('/expenses/', { params: filters })
    return data as Expense[]
  },
  get: async (id: number) => {
    const { data } = await api.get(`/expenses/${id}`)
    return data as Expense
  },
  update: async (id: number, payload: Partial<Expense>) => {
    const { data } = await api.patch(`/expenses/${id}`, payload)
    return data as Expense
  },
  delete: async (id: number) => {
    const { data } = await api.delete(`/expenses/${id}`)
    return data
  },
  recategorize: async (id: number) => {
    const { data } = await api.post(`/expenses/${id}/categorize`)
    return data as Expense
  },
  categorizeBatch: async () => {
    const { data } = await api.post('/expenses/categorize-batch')
    return data
  },
  cardholders: async () => {
    const { data } = await api.get('/expenses/cardholders')
    return data as string[]
  },
}

export const analyticsApi = {
  // start/end are ISO date strings (YYYY-MM-DD). Omit both for all-time data.
  getSummary: async (startDate?: string, endDate?: string, cardholder?: string) => {
    const params: Record<string, string | boolean> = {}
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    if (!startDate && !endDate) params.all_time = true
    if (cardholder) params.cardholder = cardholder
    const { data } = await api.get('/analytics/summary', { params })
    return data as SpendingSummary
  },
  getMonthlyTrends: async (months = 12, cardholder?: string) => {
    const { data } = await api.get('/analytics/trends/monthly', {
      params: { months, ...(cardholder ? { cardholder } : {}) },
    })
    return data as MonthlyTrend[]
  },
  getCategoryTrends: async (months = 6, cardholder?: string) => {
    const { data } = await api.get('/analytics/trends/category', {
      params: { months, ...(cardholder ? { cardholder } : {}) },
    })
    return data
  },
  getUnusualSpending: async (cardholder?: string) => {
    const { data } = await api.get('/analytics/unusual', {
      params: { ...(cardholder ? { cardholder } : {}) },
    })
    return data
  },
  getBudgetRecommendations: async (cardholder?: string) => {
    const { data } = await api.get('/analytics/budget/recommendations', {
      params: { ...(cardholder ? { cardholder } : {}) },
    })
    return data as BudgetRecommendation
  },
}
