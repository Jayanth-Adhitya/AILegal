'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

const PUBLIC_ROUTES = ['/login', '/register', '/']

export function RouteGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    // Skip if loading or on public route
    if (loading || PUBLIC_ROUTES.includes(pathname)) {
      return
    }

    // Redirect to login if not authenticated
    if (!user) {
      const redirectUrl = encodeURIComponent(pathname)
      router.push(`/login?redirect=${redirectUrl}`)
    }
  }, [user, loading, pathname, router])

  // Show loading state
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gradient-to-br from-yellow-50 to-yellow-100">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-yellow-600" />
          <p className="mt-4 text-sm text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  // Show login required message for protected routes
  if (!user && !PUBLIC_ROUTES.includes(pathname)) {
    return (
      <div className="flex h-screen items-center justify-center bg-gradient-to-br from-yellow-50 to-yellow-100">
        <div className="max-w-md rounded-lg glass-card p-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-yellow-200 to-yellow-300 shadow-dual-md">
            <svg
              className="h-8 w-8 text-yellow-700"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <h2 className="mb-2 text-2xl font-bold text-gray-900">Authentication Required</h2>
          <p className="mb-6 text-gray-600">
            Please log in to access this page.
          </p>
          <button
            onClick={() => router.push(`/login?redirect=${encodeURIComponent(pathname)}`)}
            className="w-full rounded-lg btn-gradient px-6 py-3 font-medium text-gray-900 transition-all hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:ring-offset-2"
          >
            Go to Login
          </button>
          <p className="mt-4 text-sm text-gray-500">
            Don't have an account?{' '}
            <button
              onClick={() => router.push('/register')}
              className="font-medium text-yellow-700 hover:text-yellow-800 transition-colors"
            >
              Register here
            </button>
          </p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
