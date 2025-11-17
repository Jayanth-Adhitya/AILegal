"use client"

import * as React from "react"
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion"
import { cn } from "@/lib/utils"

interface TiltCardProps {
  children: React.ReactNode
  className?: string
  tiltAmount?: number
}

export function TiltCard({
  children,
  className,
  tiltAmount = 10,
}: TiltCardProps) {
  const x = useMotionValue(0)
  const y = useMotionValue(0)

  const mouseXSpring = useSpring(x)
  const mouseYSpring = useSpring(y)

  const rotateX = useTransform(
    mouseYSpring,
    [-0.5, 0.5],
    [`${tiltAmount}deg`, `-${tiltAmount}deg`]
  )
  const rotateY = useTransform(
    mouseXSpring,
    [-0.5, 0.5],
    [`-${tiltAmount}deg`, `${tiltAmount}deg`]
  )

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const width = rect.width
    const height = rect.height
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top
    const xPct = mouseX / width - 0.5
    const yPct = mouseY / height - 0.5
    x.set(xPct)
    y.set(yPct)
  }

  const handleMouseLeave = () => {
    x.set(0)
    y.set(0)
  }

  return (
    <motion.div
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        rotateX,
        rotateY,
        transformStyle: "preserve-3d",
      }}
      className={cn(
        "relative rounded-lg bg-card text-card-foreground shadow-dual-md transition-shadow duration-200 hover:shadow-dual-lg",
        className
      )}
    >
      <div style={{ transform: "translateZ(50px)" }}>{children}</div>
    </motion.div>
  )
}

interface SpotlightCardProps {
  children: React.ReactNode
  className?: string
}

export function SpotlightCard({ children, className }: SpotlightCardProps) {
  const divRef = React.useRef<HTMLDivElement>(null)
  const [position, setPosition] = React.useState({ x: 0, y: 0 })
  const [opacity, setOpacity] = React.useState(0)

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!divRef.current) return
    const rect = divRef.current.getBoundingClientRect()
    setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top })
  }

  const handleMouseEnter = () => setOpacity(1)
  const handleMouseLeave = () => setOpacity(0)

  return (
    <div
      ref={divRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={cn(
        "relative overflow-hidden rounded-lg bg-card text-card-foreground shadow-dual-md transition-shadow duration-200 hover:shadow-dual-lg",
        className
      )}
    >
      <div
        className="pointer-events-none absolute -inset-px opacity-0 transition duration-300"
        style={{
          opacity,
          background: `radial-gradient(600px circle at ${position.x}px ${position.y}px, hsl(45 93% 77% / 0.15), transparent 40%)`,
        }}
      />
      {children}
    </div>
  )
}

interface MagneticButtonProps {
  children: React.ReactNode
  className?: string
  strength?: number
}

export function MagneticButton({
  children,
  className,
  strength = 0.3,
}: MagneticButtonProps) {
  const ref = React.useRef<HTMLDivElement>(null)
  const x = useMotionValue(0)
  const y = useMotionValue(0)

  const mouseXSpring = useSpring(x, { stiffness: 150, damping: 15 })
  const mouseYSpring = useSpring(y, { stiffness: 150, damping: 15 })

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return
    const rect = ref.current.getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2
    const distanceX = e.clientX - centerX
    const distanceY = e.clientY - centerY
    x.set(distanceX * strength)
    y.set(distanceY * strength)
  }

  const handleMouseLeave = () => {
    x.set(0)
    y.set(0)
  }

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ x: mouseXSpring, y: mouseYSpring }}
      className={cn("inline-block", className)}
    >
      {children}
    </motion.div>
  )
}

interface ShimmerButtonProps {
  children: React.ReactNode
  className?: string
  shimmerColor?: string
}

export function ShimmerButton({
  children,
  className,
  shimmerColor = "hsl(45 93% 77% / 0.3)",
}: ShimmerButtonProps) {
  return (
    <button
      className={cn(
        "group relative overflow-hidden rounded-md btn-gradient px-4 py-2 text-sm font-medium text-primary-foreground transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]",
        className
      )}
    >
      <div
        className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/20 to-transparent"
        style={{
          backgroundImage: `linear-gradient(90deg, transparent, ${shimmerColor}, transparent)`,
        }}
      />
      {children}
    </button>
  )
}
