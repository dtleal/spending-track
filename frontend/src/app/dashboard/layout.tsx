'use client'

import { AuthGuard } from '@/components/auth-guard'
import { DashboardNav } from '@/components/dashboard-nav'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <AuthGuard requireAuth={true}>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <DashboardNav />
        <main className="container mx-auto max-w-7xl">
          {children}
        </main>
      </div>
    </AuthGuard>
  )
}