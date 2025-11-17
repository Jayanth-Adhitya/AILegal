"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface ShuffleTextProps {
  text: string
  className?: string
  duration?: number
  charset?: string
  triggerOnHover?: boolean
}

export function ShuffleText({
  text,
  className,
  duration = 1000,
  charset = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`",
  triggerOnHover = false,
}: ShuffleTextProps) {
  const [displayText, setDisplayText] = React.useState(text)
  const [isAnimating, setIsAnimating] = React.useState(false)
  const intervalRef = React.useRef<NodeJS.Timeout | null>(null)
  const hasAnimated = React.useRef(false)

  const shuffle = React.useCallback(() => {
    if (isAnimating) return

    setIsAnimating(true)
    let iteration = 0
    const maxIterations = text.length

    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }

    intervalRef.current = setInterval(() => {
      setDisplayText(
        text
          .split("")
          .map((char, index) => {
            if (char === " ") return " "
            if (index < iteration) {
              return text[index]
            }
            return charset[Math.floor(Math.random() * charset.length)]
          })
          .join("")
      )

      if (iteration >= maxIterations) {
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
        }
        setDisplayText(text)
        setIsAnimating(false)
      }

      iteration += 1 / 3
    }, duration / (maxIterations * 3))
  }, [text, charset, duration, isAnimating])

  React.useEffect(() => {
    if (!hasAnimated.current && !triggerOnHover) {
      const timer = setTimeout(() => {
        shuffle()
        hasAnimated.current = true
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [shuffle, triggerOnHover])

  React.useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  const handleMouseEnter = () => {
    if (triggerOnHover) {
      shuffle()
    }
  }

  return (
    <span
      className={cn("inline-block", className)}
      onMouseEnter={handleMouseEnter}
    >
      {displayText}
    </span>
  )
}
