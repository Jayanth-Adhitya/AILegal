"use client"

import { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Mail, ArrowLeft, CheckCircle } from 'lucide-react'
import { glassCardEntrance } from '@/lib/animations'
import { API_BASE_URL } from '@/lib/api'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
      })

      const data = await response.json()

      if (data.success) {
        setIsSubmitted(true)
      } else {
        setError(data.error || 'Failed to send reset email')
      }
    } catch (err) {
      setError('Network error. Please try again.')
    } finally {
      setIsLoading(false)
    }
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
                {isSubmitted ? (
                  <CheckCircle className="w-full h-full text-green-600" />
                ) : (
                  <Mail className="w-full h-full text-yellow-600" />
                )}
              </motion.div>
            </div>
            <CardTitle className="text-2xl font-bold text-center text-gray-900">
              {isSubmitted ? 'Check Your Email' : 'Forgot Password?'}
            </CardTitle>
            <CardDescription className="text-center">
              {isSubmitted
                ? 'We\'ve sent you a password reset link'
                : 'Enter your email to receive a reset link'}
            </CardDescription>
          </CardHeader>

          {isSubmitted ? (
            <>
              <CardContent className="space-y-4">
                <Alert className="border-green-200 bg-green-50/50">
                  <AlertDescription className="text-gray-700">
                    If an account exists with <strong>{email}</strong>, you will receive a password reset link shortly. The link will expire in 15 minutes.
                  </AlertDescription>
                </Alert>

                <Alert className="border-yellow-200 bg-yellow-50/50">
                  <AlertDescription className="text-gray-700 text-sm">
                    <strong>Didn't receive the email?</strong>
                    <ul className="mt-2 space-y-1 list-disc list-inside">
                      <li>Check your spam or junk folder</li>
                      <li>Make sure you entered the correct email</li>
                      <li>Wait a few minutes and try again</li>
                    </ul>
                  </AlertDescription>
                </Alert>
              </CardContent>

              <CardFooter className="flex flex-col space-y-4">
                <Button
                  onClick={() => setIsSubmitted(false)}
                  variant="outline"
                  className="w-full"
                >
                  Send Another Link
                </Button>

                <Link href="/login" className="w-full">
                  <Button variant="ghost" className="w-full text-yellow-700 hover:text-yellow-800 hover:bg-yellow-50">
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Login
                  </Button>
                </Link>
              </CardFooter>
            </>
          ) : (
            <form onSubmit={handleSubmit}>
              <CardContent className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
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
                  <p className="text-sm text-gray-600">
                    We'll send you a link to reset your password
                  </p>
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
                      Sending...
                    </>
                  ) : (
                    <>
                      <Mail className="mr-2 h-4 w-4" />
                      Send Reset Link
                    </>
                  )}
                </Button>

                <Link href="/login" className="w-full">
                  <Button variant="ghost" className="w-full text-yellow-700 hover:text-yellow-800 hover:bg-yellow-50">
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Login
                  </Button>
                </Link>
              </CardFooter>
            </form>
          )}
        </Card>
      </motion.div>
    </div>
  )
}
