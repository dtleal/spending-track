'use client'

import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { expensesApi } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import {
  DollarSign, Calendar, Receipt, AlertTriangle, TrendingUp, TrendingDown,
  Repeat, Users, Trophy, Flame,
} from 'lucide-react'
import { format } from 'date-fns'
import { usePrivacyStore } from '@/lib/privacy-store'
import { formatCurrency } from '@/lib/utils'
import { useResolvedFilters } from '@/lib/filter-store'

const CATEGORY_LABELS: Record<string, string> = {
  food: 'Food & Dining', transport: 'Transportation', shopping: 'Shopping',
  health: 'Health & Medical', entertainment: 'Entertainment',
  utilities: 'Utilities & Bills', education: 'Education', fees: 'Card Fees',
  mercado_livre: 'Mercado Livre', amazon: 'Amazon', other: 'Other',
}
const CATEGORY_COLORS: Record<string, string> = {
  food: '#f97316', transport: '#3b82f6', shopping: '#ec4899', health: '#ef4444',
  entertainment: '#a855f7', utilities: '#64748b', education: '#22c55e',
  fees: '#e11d48', mercado_livre: '#eab308', amazon: '#6366f1', other: '#f59e0b',
}
const monthKey = (iso: string) => iso.slice(0, 7)

export default function AnalyticsPage() {
  const { isPrivacyMode } = usePrivacyStore()
  const { startDate, endDate, cardholder, label } = useResolvedFilters()
  const fc = (v: number) => formatCurrency(v, isPrivacyMode)

  const { data: expenses = [], isLoading } = useQuery({
    queryKey: ['analytics-expenses', startDate, endDate, cardholder],
    queryFn: () =>
      expensesApi.list({ start_date: startDate, end_date: endDate, cardholder, limit: 5000 }),
  })

  const insights = useMemo(() => {
    const rows = expenses as any[]
    const total = rows.reduce((s, e) => s + e.amount, 0)
    const count = rows.length

    // date span (for per-day average)
    const times = rows.map((e) => new Date(e.date).getTime())
    const minT = times.length ? Math.min(...times) : 0
    const maxT = times.length ? Math.max(...times) : 0
    const days = times.length ? Math.max(1, Math.round((maxT - minT) / 86400000) + 1) : 1

    const sumBy = (key: (e: any) => string) =>
      rows.reduce((acc: Record<string, number>, e) => {
        const k = key(e)
        acc[k] = (acc[k] || 0) + e.amount
        return acc
      }, {})

    const byCategory = Object.entries(sumBy((e) => e.category || 'other'))
      .sort((a, b) => b[1] - a[1])

    // per-person
    const byPerson = Object.entries(
      rows.reduce((acc: Record<string, { total: number; count: number }>, e) => {
        const p = e.cardholder || 'Sem titular'
        acc[p] = acc[p] || { total: 0, count: 0 }
        acc[p].total += e.amount
        acc[p].count += 1
        return acc
      }, {})
    ).sort((a, b) => b[1].total - a[1].total)

    // per month (sorted) for the trend area chart
    const byMonthMap = sumBy((e) => monthKey(e.date))
    const months = Object.keys(byMonthMap).sort()
    const monthly = months.map((m) => ({
      month: m,
      total: Math.round(byMonthMap[m] * 100) / 100,
      label: format(new Date(m + '-01'), 'MMM yy'),
    }))

    // category month-over-month (latest vs previous month present)
    const catMonth: Record<string, Record<string, number>> = {}
    rows.forEach((e) => {
      const c = e.category || 'other'
      const m = monthKey(e.date)
      catMonth[c] = catMonth[c] || {}
      catMonth[c][m] = (catMonth[c][m] || 0) + e.amount
    })
    const lastM = months[months.length - 1]
    const prevM = months[months.length - 2]
    const catDelta: Record<string, number | null> = {}
    byCategory.forEach(([c]) => {
      if (!prevM) { catDelta[c] = null; return }
      const cur = catMonth[c]?.[lastM] || 0
      const prev = catMonth[c]?.[prevM] || 0
      catDelta[c] = prev > 0 ? ((cur - prev) / prev) * 100 : (cur > 0 ? 100 : null)
    })

    // top merchants (exclude internal aggregate lines)
    const isAggregate = (m: string) => /\(Itaú\)/.test(m)
    const merchants = Object.entries(
      rows.filter((e) => !isAggregate(e.merchant)).reduce(
        (acc: Record<string, { total: number; count: number }>, e) => {
          acc[e.merchant] = acc[e.merchant] || { total: 0, count: 0 }
          acc[e.merchant].total += e.amount
          acc[e.merchant].count += 1
          return acc
        }, {})
    ).sort((a, b) => b[1].total - a[1].total)

    // recurring: merchant present in many distinct months
    const merchMonths: Record<string, Set<string>> = {}
    const merchTotal: Record<string, number> = {}
    rows.filter((e) => !isAggregate(e.merchant)).forEach((e) => {
      merchMonths[e.merchant] = merchMonths[e.merchant] || new Set()
      merchMonths[e.merchant].add(monthKey(e.date))
      merchTotal[e.merchant] = (merchTotal[e.merchant] || 0) + e.amount
    })
    const minMonths = Math.min(3, Math.max(2, months.length))
    const recurring = Object.entries(merchMonths)
      .filter(([, set]) => set.size >= minMonths)
      .map(([m, set]) => ({ merchant: m, months: set.size, total: merchTotal[m], perMonth: merchTotal[m] / set.size }))
      .sort((a, b) => b.total - a.total)

    // biggest single expenses
    const biggest = [...rows].filter((e) => !isAggregate(e.merchant))
      .sort((a, b) => b.amount - a.amount).slice(0, 6)

    // fees
    const feeRows = rows.filter((e) => e.category === 'fees')
    const feesTotal = feeRows.reduce((s, e) => s + e.amount, 0)
    const avoidable = feeRows
      .filter((e) => /Multa|Juros/i.test(e.merchant))
      .reduce((s, e) => s + e.amount, 0)
    const feeByType = Object.entries(sumBy((e) => e.merchant))
      .filter(([m]) => /\(Itaú\)/.test(m) && feeRows.some((f) => f.merchant === m))
      .map(([m, v]) => ({ name: m.replace(' (Itaú)', ''), amount: v }))
      .sort((a, b) => b.amount - a.amount)

    return {
      total, count, days, avgPerDay: total / days, avgTicket: count ? total / count : 0,
      byCategory, byPerson, monthly, catDelta, merchants, recurring, biggest,
      feesTotal, avoidable, feeByType,
    }
  }, [expenses])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  const sub = `${label}${cardholder ? ` · ${cardholder}` : ''}`
  const maxCat = insights.byCategory[0]?.[1] || 1
  const maxPerson = insights.byPerson[0]?.[1].total || 1

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Analytics</h1>
        <p className="text-muted-foreground">Insights from your spending · {sub}</p>
      </div>

      {insights.count === 0 ? (
        <Card><CardContent className="py-12 text-center text-muted-foreground">
          No expenses in this period. Adjust the filters above.
        </CardContent></Card>
      ) : (
        <>
          {/* KPI cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Kpi icon={<DollarSign className="h-5 w-5" />} label="Total spent" value={fc(insights.total)} hint={`${insights.count} transactions`} />
            <Kpi icon={<Calendar className="h-5 w-5" />} label="Avg / day" value={fc(insights.avgPerDay)} hint={`over ${insights.days} days`} />
            <Kpi icon={<Receipt className="h-5 w-5" />} label="Avg ticket" value={fc(insights.avgTicket)} hint="per transaction" />
            <Kpi
              icon={<AlertTriangle className="h-5 w-5" />}
              label="Card fees"
              value={fc(insights.feesTotal)}
              hint={insights.avoidable > 0 ? `${fc(insights.avoidable)} avoidable` : 'annuity & taxes'}
              danger={insights.avoidable > 0}
            />
          </div>

          {/* Avoidable-fees callout */}
          {insights.avoidable > 0 && (
            <Card className="border-rose-300 bg-rose-50 dark:border-rose-900/60 dark:bg-rose-950/30">
              <CardContent className="py-4 flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-rose-600 dark:text-rose-400 mt-0.5" />
                <div className="text-sm">
                  <span className="font-semibold text-rose-700 dark:text-rose-300">
                    {fc(insights.avoidable)} em juros e multa por atraso.
                  </span>{' '}
                  <span className="text-rose-700/80 dark:text-rose-300/80">
                    Pagar cada fatura integral e em dia evitaria essas cobranças
                    (a multa por atraso é de 2% sobre o saldo total).
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Monthly trend (area) */}
          <Card>
            <CardHeader>
              <CardTitle>Spending over time</CardTitle>
              <CardDescription>Total per month in the selected range</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={insights.monthly}>
                  <defs>
                    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4ECDC4" stopOpacity={0.7} />
                      <stop offset="95%" stopColor="#4ECDC4" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="label" tick={{ fill: 'hsl(var(--foreground))' }} />
                  <YAxis tickFormatter={fc} tick={{ fill: 'hsl(var(--foreground))' }} width={80} />
                  <Tooltip
                    formatter={(v: number) => [fc(v), 'Total']}
                    contentStyle={{ backgroundColor: 'hsl(var(--background))', border: '1px solid hsl(var(--border))', borderRadius: 8, color: 'hsl(var(--foreground))' }}
                  />
                  <Area type="monotone" dataKey="total" stroke="#4ECDC4" strokeWidth={2} fill="url(#g)" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Who spent */}
            {insights.byPerson.length > 1 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><Users className="h-5 w-5" /> Who spent</CardTitle>
                  <CardDescription>Split between cardholders</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {insights.byPerson.map(([person, d]) => (
                    <div key={person}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium">{person}</span>
                        <span className="text-muted-foreground">
                          {fc(d.total)} · {((d.total / insights.total) * 100).toFixed(0)}% · {d.count} txns
                        </span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2.5">
                        <div className="h-2.5 rounded-full bg-primary" style={{ width: `${(d.total / maxPerson) * 100}%` }} />
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Category breakdown w/ MoM */}
            <Card className={insights.byPerson.length > 1 ? '' : 'lg:col-span-2'}>
              <CardHeader>
                <CardTitle>By category</CardTitle>
                <CardDescription>Share of spending and month-over-month change</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {insights.byCategory.map(([cat, amount]) => {
                  const delta = insights.catDelta[cat]
                  return (
                    <div key={cat}>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="flex items-center gap-2">
                          <span className="h-3 w-3 rounded-sm" style={{ background: CATEGORY_COLORS[cat] || '#999' }} />
                          {CATEGORY_LABELS[cat] || cat}
                        </span>
                        <span className="flex items-center gap-2">
                          {delta != null && (
                            <span className={`text-xs flex items-center ${delta > 0 ? 'text-rose-600' : 'text-green-600'}`}>
                              {delta > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                              {Math.abs(delta).toFixed(0)}%
                            </span>
                          )}
                          <span className="font-semibold tabular-nums">{fc(amount)}</span>
                        </span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-1.5">
                        <div className="h-1.5 rounded-full" style={{ width: `${(amount / maxCat) * 100}%`, background: CATEGORY_COLORS[cat] || '#999' }} />
                      </div>
                    </div>
                  )
                })}
              </CardContent>
            </Card>

            {/* Top merchants */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Trophy className="h-5 w-5" /> Top merchants</CardTitle>
                <CardDescription>Where most of your money goes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {insights.merchants.slice(0, 8).map(([m, d], i) => (
                    <div key={m} className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2 truncate">
                        <span className="text-muted-foreground w-4 text-right">{i + 1}</span>
                        <span className="truncate">{m}</span>
                        <span className="text-xs text-muted-foreground">×{d.count}</span>
                      </span>
                      <span className="font-semibold tabular-nums">{fc(d.total)}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Recurring / subscriptions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Repeat className="h-5 w-5" /> Recurring spending</CardTitle>
                <CardDescription>Merchants charged across multiple months</CardDescription>
              </CardHeader>
              <CardContent>
                {insights.recurring.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No recurring merchants detected in this range.</p>
                ) : (
                  <div className="space-y-2">
                    {insights.recurring.slice(0, 8).map((r) => (
                      <div key={r.merchant} className="flex items-center justify-between text-sm">
                        <span className="truncate">
                          {r.merchant}
                          <span className="text-xs text-muted-foreground"> · {r.months} months</span>
                        </span>
                        <span className="text-right">
                          <span className="font-semibold tabular-nums">{fc(r.total)}</span>
                          <span className="block text-xs text-muted-foreground">~{fc(r.perMonth)}/mo</span>
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Biggest expenses */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Flame className="h-5 w-5" /> Biggest purchases</CardTitle>
                <CardDescription>Largest single transactions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {insights.biggest.map((e) => (
                    <div key={e.id} className="flex items-center justify-between text-sm">
                      <span className="truncate">
                        {e.merchant}
                        <span className="block text-xs text-muted-foreground">
                          {format(new Date(e.date), 'dd MMM yyyy')} · {CATEGORY_LABELS[e.category] || e.category}
                        </span>
                      </span>
                      <span className="font-semibold tabular-nums">{fc(e.amount)}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Card fees detail */}
          {insights.feeByType.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5" /> Card fees breakdown</CardTitle>
                <CardDescription>What the bank charged in the selected range</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {insights.feeByType.map((f) => (
                    <div key={f.name} className="flex items-center justify-between text-sm border rounded-md px-3 py-2">
                      <span>{f.name}</span>
                      <span className="font-semibold tabular-nums">{fc(f.amount)}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}

function Kpi({ icon, label, value, hint, danger }: {
  icon: React.ReactNode; label: string; value: string; hint?: string; danger?: boolean
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          {icon} {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${danger ? 'text-rose-600 dark:text-rose-400' : ''}`}>{value}</div>
        {hint && <p className="text-xs text-muted-foreground mt-1">{hint}</p>}
      </CardContent>
    </Card>
  )
}
