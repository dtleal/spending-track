import { useMemo } from 'react'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type RangePreset =
  | 'last7'
  | 'last30'
  | 'last90'
  | 'last180'
  | 'year'
  | 'all'
  | 'custom'

export const PRESET_LABELS: Record<RangePreset, string> = {
  last7: 'Last 7 days',
  last30: 'Last 30 days',
  last90: 'Last 90 days',
  last180: 'Last 6 months',
  year: 'Last year',
  all: 'All time',
  custom: 'Custom range',
}

const PRESET_DAYS: Record<string, number> = {
  last7: 7,
  last30: 30,
  last90: 90,
  last180: 180,
  year: 365,
}

interface FilterState {
  rangePreset: RangePreset
  customStart: string | null // YYYY-MM-DD
  customEnd: string | null
  cardholder: string // 'all' | person name
  setRangePreset: (p: RangePreset) => void
  setCustomRange: (start: string | null, end: string | null) => void
  setCardholder: (c: string) => void
}

export const useFilterStore = create<FilterState>()(
  persist(
    (set) => ({
      rangePreset: 'last30', // default
      customStart: null,
      customEnd: null,
      cardholder: 'all',
      setRangePreset: (rangePreset) => set({ rangePreset }),
      setCustomRange: (customStart, customEnd) =>
        set({ customStart, customEnd, rangePreset: 'custom' }),
      setCardholder: (cardholder) => set({ cardholder }),
    }),
    { name: 'spendtrack-filters' }
  )
)

const fmt = (d: Date) => d.toISOString().split('T')[0]

export interface ResolvedFilters {
  startDate?: string
  endDate?: string
  cardholder?: string
  label: string
}

/** Resolve the active filter store into concrete API params. */
export function resolveFilters(state: FilterState): ResolvedFilters {
  const cardholder = state.cardholder !== 'all' ? state.cardholder : undefined

  if (state.rangePreset === 'all') {
    return { cardholder, label: PRESET_LABELS.all }
  }
  if (state.rangePreset === 'custom') {
    return {
      startDate: state.customStart || undefined,
      endDate: state.customEnd || undefined,
      cardholder,
      label:
        state.customStart && state.customEnd
          ? `${state.customStart} → ${state.customEnd}`
          : 'Custom range',
    }
  }
  const days = PRESET_DAYS[state.rangePreset] ?? 30
  const end = new Date()
  const start = new Date()
  start.setDate(end.getDate() - days)
  return {
    startDate: fmt(start),
    endDate: fmt(end),
    cardholder,
    label: PRESET_LABELS[state.rangePreset],
  }
}

/** Hook returning the resolved filters; re-renders when the store changes. */
export function useResolvedFilters(): ResolvedFilters {
  const rangePreset = useFilterStore((s) => s.rangePreset)
  const customStart = useFilterStore((s) => s.customStart)
  const customEnd = useFilterStore((s) => s.customEnd)
  const cardholder = useFilterStore((s) => s.cardholder)
  return useMemo(
    () =>
      resolveFilters({
        rangePreset,
        customStart,
        customEnd,
        cardholder,
      } as FilterState),
    [rangePreset, customStart, customEnd, cardholder]
  )
}
