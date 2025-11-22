"use client"

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Lock, CheckCircle, AlertTriangle } from 'lucide-react'
import { glassCardEntrance } from '@/lib/animations'
import { API_BASE_URL } from '@/lib/api'

export default function ResetPasswordPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isValidating, setIsValidating] = useState(true)
  const [isTokenValid, setIsTokenValid] = useState(false)
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [passwordError, setPasswordError] = useState<string | null>(null)

  // Validate token on page load
  useEffect(() => {
    if (!token) {
      setError('No reset token provided')
      setIsValidating(false)
      return
    }

    const validateToken = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/auth/validate-reset-token/${token}`)
        const data = await response.json()

        if (data.valid) {
          setIsTokenValid(true)
          setEmail(data.email)
        } else {
          setError(data.error || 'Invalid or expired reset token')
        }
      } catch (err) {
        setError('Network error. Please try again.')
      } finally {
        setIsValidating(false)
      }
    }

    validateToken()
  }, [token])

  // Password validation
  useEffect(() => {
    if (newPassword.length > 0 && newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters long')
    } else if (newPassword !== confirmPassword && confirmPassword.length > 0) {
      setPasswordError('Passwords do not match')
    } else {
      setPasswordError(null)
    }
  }, [newPassword, confirmPassword])

  const getPasswordStrength = () => {
    if (newPassword.length === 0) return { strength: 0, label: '', color: '' }
    if (newPassword.length < 8) return { strength: 25, label: 'Too Short', color: 'bg-red-500' }
    if (newPassword.length < 12) return { strength: 50, label: 'Weak', color: 'bg-yellow-500' }
    if (newPassword.length < 16) return { strength: 75, label: 'Good', color: 'bg-blue-500' }
    return { strength: 100, label: 'Strong', color: 'bg-green-500' }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (passwordError) {
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          token,
          new_password: newPassword,
          confirm_password: confirmPassword
        })
      })

      const data = await response.json()

      if (data.success) {
        // Redirect to login with success message
        router.push('/login?reset=success')
      } else {
        setError(data.error || 'Password reset failed')
      }
    } catch (err) {
      setError('Network error. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const passwordStrength = getPasswordStrength()

  if (isValidating) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-yellow-50 via-yellow-100 to-yellow-200 p-4">
        <motion.div
          initial="hidden"
          animate="visible"
          variants={glassCardEntrance}
          className="w-full max-w-md"
        >
          <Card className="glass-card">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-12 w-12 animate-spin text-yellow-600 mb-4" />
              <p className="text-gray-600">Validating reset token...</p>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  if (!isTokenValid) {
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
                <div className="w-24 h-24 p-4 rounded-3xl backdrop-blur-xl bg-white/40 border border-white/30 flex items-center justify-center"
                  style={{
                    background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.5), rgba(254, 240, 138, 0.3))',
                    boxShadow: '0 12px 48px 0 rgba(251, 191, 36, 0.25), inset 0 1px 0 0 rgba(255, 255, 255, 0.6)'
                  }}
                >
                  <AlertTriangle className="w-full h-full text-red-600" />
                </div>
              </div>
              <CardTitle className="text-2xl font-bold text-center text-gray-900">Reset Link Invalid</CardTitle>
              <CardDescription className="text-center">This password reset link is invalid or has expired</CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <Alert variant="destructive">
                <AlertDescription>{error || 'The reset link is invalid or has expired'}</AlertDescription>
              </Alert>

              <div className="text-sm text-gray-600 space-y-2">
                <p><strong>Common reasons:</strong></p>
                <ul className="list-disc list-inside space-y-1">
                  <li>The link has expired (links are valid for 15 minutes)</li>
                  <li>The link has already been used</li>
                  <li>The link was copied incorrectly</li>
                </ul>
              </div>
            </CardContent>

            <CardFooter className="flex flex-col space-y-4">
              <Link href="/forgot-password" className="w-full">
                <Button className="w-full">
                  Request New Reset Link
                </Button>
              </Link>

              <Link href="/login" className="w-full">
                <Button variant="outline" className="w-full">
                  Back to Login
                </Button>
              </Link>
            </CardFooter>
          </Card>
        </motion.div>
      </div>
    )
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
                className="w-24 h-24 p-4 rounded-3xl backdrop-blur-xl bg-white/40 border border-white/30"
                whileHover={{ scale: 1.1, rotate: 5 }}
                transition={{ duration: 0.3, type: "spring" }}
                style={{
                  background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.5), rgba(254, 240, 138, 0.3))',
                  boxShadow: '0 12px 48px 0 rgba(251, 191, 36, 0.25), inset 0 1px 0 0 rgba(255, 255, 255, 0.6)'
                }}
              >
                <Lock className="w-full h-full text-yellow-600" />
              </motion.div>
            </div>
            <CardTitle className="text-2xl font-bold text-center text-gray-900">Reset Your Password</CardTitle>
            <CardDescription className="text-center">
              Enter a new password for {email}
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
                <Label htmlFor="newPassword">New Password</Label>
                <Input
                  id="newPassword"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  disabled={isLoading}
                  className="focus:ring-yellow-400"
                  placeholder="Enter new password"
                />
                {newPassword.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Password strength:</span>
                      <span className={`font-medium ${
                        passwordStrength.strength >= 75 ? 'text-green-600' :
                        passwordStrength.strength >= 50 ? 'text-blue-600' :
                        passwordStrength.strength >= 25 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {passwordStrength.label}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${passwordStrength.color}`}
                        style={{ width: `${passwordStrength.strength}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm New Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={isLoading}
                  className="focus:ring-yellow-400"
                  placeholder="Confirm new password"
                />
                {passwordError && (
                  <p className="text-sm text-red-600">{passwordError}</p>
                )}
              </div>

              <Alert className="border-yellow-200 bg-yellow-50/50">
                <AlertDescription className="text-sm text-gray-700">
                  <strong>Security note:</strong> Your password must be at least 8 characters long. After resetting, all active sessions will be logged out for security.
                </AlertDescription>
              </Alert>
            </CardContent>

            <CardFooter className="flex flex-col space-y-4">
              <Button
                type="submit"
                className="w-full"
                disabled={isLoading || !!passwordError}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Resetting Password...
                  </>
                ) : (
                  <>
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Reset Password
                  </>
                )}
              </Button>

              <Link href="/login" className="w-full">
                <Button variant="outline" className="w-full">
                  Cancel
                </Button>
              </Link>
            </CardFooter>
          </form>
        </Card>
      </motion.div>
    </div>
  )
}
