"use client"

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Scale, Loader2, Info } from 'lucide-react'
import { glassCardEntrance } from '@/lib/animations'

export default function RegisterPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { register, error, user } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [companyId, setCompanyId] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [validationError, setValidationError] = useState('')

  const redirect = searchParams.get('redirect') || '/dashboard'

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      router.push(redirect)
    }
  }, [user, router, redirect])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setValidationError('')

    // Validation
    if (password !== confirmPassword) {
      setValidationError('Passwords do not match')
      return
    }

    if (password.length < 6) {
      setValidationError('Password must be at least 6 characters')
      return
    }

    setIsLoading(true)

    const success = await register(email, password, companyName, companyId || undefined)

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
            <CardTitle className="text-2xl font-bold text-center text-gray-900">Create an account</CardTitle>
            <CardDescription className="text-center">
              Register your company for Legal AI services
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {(error || validationError) && (
                <Alert variant="destructive">
                  <AlertDescription>{error || validationError}</AlertDescription>
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
                <Label htmlFor="companyName">Company Name</Label>
                <Input
                  id="companyName"
                  type="text"
                  placeholder="Acme Corporation"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  required
                  disabled={isLoading}
                  className="focus:ring-yellow-400"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="companyId">
                  Company ID <span className="text-gray-400">(Optional)</span>
                </Label>
                <Input
                  id="companyId"
                  type="text"
                  placeholder="ACME-001 (leave empty for auto-generated)"
                  value={companyId}
                  onChange={(e) => setCompanyId(e.target.value)}
                  disabled={isLoading}
                  className="focus:ring-yellow-400"
                />
                <p className="text-xs text-gray-500">
                  This ID will be used for contract negotiations. If left empty, one will be generated for you.
                </p>
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
                  minLength={6}
                  className="focus:ring-yellow-400"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={isLoading}
                  minLength={6}
                  className="focus:ring-yellow-400"
                />
              </div>

              <Alert className="bg-yellow-100/50">
                <Info className="h-4 w-4 text-yellow-700" />
                <AlertTitle>Note</AlertTitle>
                <AlertDescription>
                  Your company ID will be used to identify your organization in future contract negotiations.
                </AlertDescription>
              </Alert>
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
                    Creating account...
                  </>
                ) : (
                  'Create account'
                )}
              </Button>

              <div className="text-center text-sm text-gray-600">
                Already have an account?{' '}
                <Link
                  href="/login"
                  className="text-yellow-700 hover:text-yellow-800 font-medium transition-colors"
                >
                  Sign in
                </Link>
              </div>

              <div className="text-center text-sm text-gray-500">
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