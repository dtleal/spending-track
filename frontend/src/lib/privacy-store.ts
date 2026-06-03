import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface PrivacyState {
  isPrivacyMode: boolean
  togglePrivacyMode: () => void
}

export const usePrivacyStore = create<PrivacyState>()(
  persist(
    (set) => ({
      isPrivacyMode: false,
      togglePrivacyMode: () =>
        set((state) => ({ isPrivacyMode: !state.isPrivacyMode })),
    }),
    { name: 'privacy-storage' }
  )
)
