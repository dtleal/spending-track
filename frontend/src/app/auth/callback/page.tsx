'use client'

import { useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuthStore } from '@/lib/auth-store'
import { useToast } from '@/components/ui/use-toast'

function AuthCallbackContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login } = useAuthStore()
  const { toast } = useToast()

  useEffect(() => {
    const handleAuth = async () => {
      const token = searchParams.get('token')
      const error = searchParams.get('error')

      if (error) {
        toast({
          title: 'Authentication failed',
          description: error,
          variant: 'destructive',
        })
        router.push('/login')
        return
      }

      if (token) {
        try {
          // Fetch user profile using the token
          const response = await fetch('http://localhost:8000/api/auth/me', {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          })

          if (response.ok) {
            const user = await response.json()
            login(token, user)
            
            toast({
              title: 'Login successful',
              description: `Welcome ${user.full_name || user.username}!`,
            })
            
            router.push('/dashboard')
          } else {
            throw new Error('Failed to fetch user profile')
          }
        } catch (error) {
          toast({
            title: 'Authentication failed',
            description: 'Failed to fetch user profile',
            variant: 'destructive',
          })
          router.push('/login')
        }
      } else {
        toast({
          title: 'Authentication failed',
          description: 'No token received from Google',
          variant: 'destructive',
        })
        router.push('/login')
      }
    }

    handleAuth()
  }, [searchParams, login, router, toast])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900 mx-auto"></div>
        <p className="mt-4 text-gray-600">Completing authentication...</p>
      </div>
    </div>
  )
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    }>
      <AuthCallbackContent />
    </Suspense>
  )
}