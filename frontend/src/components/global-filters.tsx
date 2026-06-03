'use client'

import { useQuery } from '@tanstack/react-query'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { expensesApi } from '@/lib/api'
import {
  useFilterStore,
  PRESET_LABELS,
  RangePreset,
} from '@/lib/filter-store'
import { CalendarRange, User } from 'lucide-react'

const PRESETS: RangePreset[] = [
  'last7',
  'last30',
  'last90',
  'last180',
  'year',
  'all',
  'custom',
]

/**
 * Global, reusable filter bar (date range + person) shown top-right on every
 * page. Reads/writes the shared filter store, so all pages stay in sync.
 */
export function GlobalFilters() {
  const rangePreset = useFilterStore((s) => s.rangePreset)
  const customStart = useFilterStore((s) => s.customStart)
  const customEnd = useFilterStore((s) => s.customEnd)
  const cardholder = useFilterStore((s) => s.cardholder)
  const setRangePreset = useFilterStore((s) => s.setRangePreset)
  const setCustomRange = useFilterStore((s) => s.setCustomRange)
  const setCardholder = useFilterStore((s) => s.setCardholder)

  const { data: people } = useQuery({
    queryKey: ['cardholders'],
    queryFn: () => expensesApi.cardholders(),
  })

  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Person filter */}
      <Select value={cardholder} onValueChange={setCardholder}>
        <SelectTrigger className="h-9 w-[140px]">
          <User className="mr-1 h-4 w-4 opacity-60" />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Everyone</SelectItem>
          {(people || []).map((p: string) => (
            <SelectItem key={p} value={p}>
              {p}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Date range filter */}
      <Select
        value={rangePreset}
        onValueChange={(v) => setRangePreset(v as RangePreset)}
      >
        <SelectTrigger className="h-9 w-[160px]">
          <CalendarRange className="mr-1 h-4 w-4 opacity-60" />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {PRESETS.map((p) => (
            <SelectItem key={p} value={p}>
              {PRESET_LABELS[p]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Custom range inputs */}
      {rangePreset === 'custom' && (
        <div className="flex items-center gap-1">
          <Input
            type="date"
            value={customStart || ''}
            max={customEnd || undefined}
            onChange={(e) => setCustomRange(e.target.value || null, customEnd)}
            className="h-9 w-[150px]"
          />
          <span className="text-muted-foreground">→</span>
          <Input
            type="date"
            value={customEnd || ''}
            min={customStart || undefined}
            onChange={(e) => setCustomRange(customStart, e.target.value || null)}
            className="h-9 w-[150px]"
          />
        </div>
      )}
    </div>
  )
}
