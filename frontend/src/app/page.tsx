'use client'

import { AuthGuard } from '@/components/auth-guard'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import Link from 'next/link'

export default function HomePage() {

  return (
    <AuthGuard requireAuth={false}>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
        <div className="max-w-4xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            Welcome to SpendTrack
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
            AI-Powered Personal Finance Manager
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="text-2xl">🤖 AI-Powered Insights</CardTitle>
              <CardDescription>
                Get intelligent spending analysis and personalized recommendations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                <li>• Automatic expense categorization</li>
                <li>• Smart spending pattern detection</li>
                <li>• Personalized budget recommendations</li>
                <li>• Predictive expense forecasting</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-2xl">📊 Beautiful Analytics</CardTitle>
              <CardDescription>
                Visualize your finances with interactive charts and reports
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                <li>• Interactive spending charts</li>
                <li>• Category breakdown analysis</li>
                <li>• Monthly trend tracking</li>
                <li>• Custom date range filtering</li>
              </ul>
            </CardContent>
          </Card>
        </div>

        <div className="text-center space-y-4">
          <div className="space-x-4">
            <Button asChild size="lg">
              <Link href="/login">Sign In</Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/register">Get Started</Link>
            </Button>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Start tracking your expenses with AI-powered insights today
          </p>
        </div>
        </div>
      </div>
    </AuthGuard>
  )
}