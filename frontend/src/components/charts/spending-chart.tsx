'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { formatCurrency } from '@/lib/utils'
import { usePrivacyStore } from '@/lib/privacy-store'
import { MonthlyTrend } from '@/types'

interface SpendingChartProps {
  data: MonthlyTrend[]
}

export function SpendingChart({ data }: SpendingChartProps) {
  const { isPrivacyMode } = usePrivacyStore()
  
  return (
    <div className="h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis 
            dataKey="month_name" 
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'hsl(var(--foreground))' }}
          />
          <YAxis 
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => formatCurrency(value, isPrivacyMode)}
            tick={{ fill: 'hsl(var(--foreground))' }}
          />
          <Tooltip 
            formatter={(value: number) => [formatCurrency(value, isPrivacyMode), 'Amount']}
            labelFormatter={(label) => `Month: ${label}`}
            contentStyle={{
              backgroundColor: 'hsl(var(--background))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px',
              color: 'hsl(var(--foreground))',
            }}
          />
          <Line 
            type="monotone" 
            dataKey="total_spent" 
            stroke="hsl(var(--primary))" 
            strokeWidth={2}
            dot={{ fill: 'hsl(var(--primary))', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}