'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/auth-store'
import dynamic from 'next/dynamic'

interface AuthGuardProps {
  children: React.ReactNode
  requireAuth?: boolean
  redirectTo?: string
}

export function AuthGuard({ 
  children, 
  requireAuth = true, 
  redirectTo 
}: AuthGuardProps) {
  const { isAuthenticated } = useAuthStore()
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Wait for hydration to complete
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, 100)

    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    if (isLoading) return

    if (requireAuth && !isAuthenticated) {
      router.push(redirectTo || '/login')
    } else if (!requireAuth && isAuthenticated) {
      router.push(redirectTo || '/dashboard')
    }
  }, [isAuthenticated, requireAuth, redirectTo, router, isLoading])

  // Show loading during hydration
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  // Show content only if auth requirements are met
  if (requireAuth && !isAuthenticated) {
    return null // Will redirect
  }

  if (!requireAuth && isAuthenticated) {
    return null // Will redirect
  }

  return <>{children}</>
}