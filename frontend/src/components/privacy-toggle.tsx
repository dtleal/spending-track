'use client'

import { Eye, EyeOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { usePrivacyStore } from '@/lib/privacy-store'

export function PrivacyToggle() {
  const { isPrivacyMode, togglePrivacyMode } = usePrivacyStore()

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={togglePrivacyMode}
      className="h-8 w-8 p-0"
      title={isPrivacyMode ? 'Show values' : 'Hide values'}
    >
      {isPrivacyMode ? (
        <EyeOff className="h-4 w-4" />
      ) : (
        <Eye className="h-4 w-4" />
      )}
    </Button>
  )
}