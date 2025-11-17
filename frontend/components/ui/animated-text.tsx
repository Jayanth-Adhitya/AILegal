"use client"

import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface GradientTextProps {
  children: React.ReactNode
  className?: string
  gradient?: string
}

export function GradientText({
  children,
  className,
  gradient = "from-yellow-600 via-yellow-500 to-yellow-400",
}: GradientTextProps) {
  return (
    <span
      className={cn(
        "bg-gradient-to-r bg-clip-text text-transparent",
        gradient,
        className
      )}
    >
      {children}
    </span>
  )
}

interface SplitTextProps {
  text: string
  className?: string
  delay?: number
}

export function SplitText({ text, className, delay = 0 }: SplitTextProps) {
  const words = text.split(" ")

  const container = {
    hidden: { opacity: 0 },
    visible: (i = 1) => ({
      opacity: 1,
      transition: { staggerChildren: 0.12, delayChildren: delay },
    }),
  }

  const child = {
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: "spring" as const,
        damping: 12,
        stiffness: 100,
      },
    },
    hidden: {
      opacity: 0,
      y: 20,
    },
  }

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="visible"
      className={cn("flex flex-wrap", className)}
    >
      {words.map((word, index) => (
        <motion.span
          variants={child}
          key={index}
          className="mr-2 inline-block"
        >
          {word}
        </motion.span>
      ))}
    </motion.div>
  )
}

interface BlurTextProps {
  text: string
  className?: string
  delay?: number
}

export function BlurText({ text, className, delay = 0 }: BlurTextProps) {
  const characters = text.split("")

  const container = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.03,
        delayChildren: delay,
      },
    },
  }

  const child = {
    hidden: {
      opacity: 0,
      filter: "blur(10px)",
    },
    visible: {
      opacity: 1,
      filter: "blur(0px)",
      transition: {
        duration: 0.4,
      },
    },
  }

  return (
    <motion.span
      variants={container}
      initial="hidden"
      animate="visible"
      className={cn("inline-block", className)}
    >
      {characters.map((char, index) => (
        <motion.span
          variants={child}
          key={index}
          className="inline-block"
        >
          {char === " " ? "\u00A0" : char}
        </motion.span>
      ))}
    </motion.span>
  )
}

interface CountUpProps {
  end: number
  duration?: number
  className?: string
  prefix?: string
  suffix?: string
}

export function CountUp({
  end,
  duration = 2,
  className,
  prefix = "",
  suffix = "",
}: CountUpProps) {
  return (
    <motion.span
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={cn("tabular-nums", className)}
    >
      {prefix}
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <CountUpNumber end={end} duration={duration} />
      </motion.span>
      {suffix}
    </motion.span>
  )
}

function CountUpNumber({ end, duration }: { end: number; duration: number }) {
  const [count, setCount] = React.useState(0)

  React.useEffect(() => {
    let startTime: number
    let animationFrame: number

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp
      const progress = Math.min((timestamp - startTime) / (duration * 1000), 1)

      setCount(Math.floor(progress * end))

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate)
      }
    }

    animationFrame = requestAnimationFrame(animate)

    return () => cancelAnimationFrame(animationFrame)
  }, [end, duration])

  return <>{count}</>
}

import * as React from "react"
