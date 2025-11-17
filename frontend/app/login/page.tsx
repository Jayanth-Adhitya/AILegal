"use client"

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Scale, Loader2 } from 'lucide-react'
import { glassCardEntrance } from '@/lib/animations'

export default function LoginPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login, error, user } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const redirect = searchParams.get('redirect') || '/dashboard'

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      router.push(redirect)
    }
  }, [user, router, redirect])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    const success = await login(email, password)

    if (success) {
      router.push(redirect)
    }

    setIsLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-yellow-50 via-yellow-100 to-yellow-200 p-4">
      <motion.div
        initial="hidden"
        animate="visible"
        variants={glassCardEntrance}
        className="w-full max-w-md"
      >
        <Card className="glass-card">
          <CardHeader className="space-y-1">
            <div className="flex items-center justify-center mb-4">
              <motion.div
                className="p-3 bg-gradient-to-br from-yellow-200 to-yellow-300 rounded-full shadow-dual-md"
                whileHover={{ scale: 1.05 }}
                transition={{ duration: 0.2 }}
              >
                <Scale className="h-8 w-8 text-yellow-700" />
              </motion.div>
            </div>
            <CardTitle className="text-2xl font-bold text-center text-gray-900">Welcome back</CardTitle>
            <CardDescription className="text-center">
              Sign in to your Legal AI account
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={isLoading}
                  className="focus:ring-yellow-400"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                  className="focus:ring-yellow-400"
                />
              </div>
            </CardContent>

            <CardFooter className="flex flex-col space-y-4">
              <Button
                type="submit"
                className="w-full"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  'Sign in'
                )}
              </Button>

              <div className="text-center text-sm text-gray-600">
                Don't have an account?{' '}
                <Link
                  href="/register"
                  className="text-yellow-700 hover:text-yellow-800 font-medium transition-colors"
                >
                  Sign up
                </Link>
              </div>

              <div className="text-center text-sm text-gray-500">
                or{' '}
                <Link
                  href="/"
                  className="text-yellow-600 hover:text-yellow-700 transition-colors"
                >
                  Back to home
                </Link>
              </div>
            </CardFooter>
          </form>
        </Card>
      </motion.div>
    </div>
  )
}