"use client"

import { useRef, useEffect, useCallback, useMemo } from "react"
import { cn } from "@/lib/utils"

interface DotGridProps {
  dotSize?: number
  gap?: number
  baseColor?: string
  activeColor?: string
  proximity?: number
  className?: string
  style?: React.CSSProperties
}

function hexToRgb(hex: string) {
  const m = hex.match(/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i)
  if (!m) return { r: 0, g: 0, b: 0 }
  return {
    r: parseInt(m[1], 16),
    g: parseInt(m[2], 16),
    b: parseInt(m[3], 16),
  }
}

export function DotGrid({
  dotSize = 3,
  gap = 24,
  baseColor = "#d4a60a",
  activeColor = "#fbbf24",
  proximity = 120,
  className = "",
  style,
}: DotGridProps) {
  const wrapperRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const dotsRef = useRef<Array<{ cx: number; cy: number }>>([])
  const pointerRef = useRef({ x: -1000, y: -1000 })
  const rafRef = useRef<number>(0)

  const baseRgb = useMemo(() => hexToRgb(baseColor), [baseColor])
  const activeRgb = useMemo(() => hexToRgb(activeColor), [activeColor])

  const circlePath = useMemo(() => {
    if (typeof window === "undefined" || !window.Path2D) return null
    const p = new window.Path2D()
    p.arc(0, 0, dotSize / 2, 0, Math.PI * 2)
    return p
  }, [dotSize])

  const buildGrid = useCallback(() => {
    const wrap = wrapperRef.current
    const canvas = canvasRef.current
    if (!wrap || !canvas) return

    const { width, height } = wrap.getBoundingClientRect()
    const dpr = window.devicePixelRatio || 1

    canvas.width = width * dpr
    canvas.height = height * dpr
    canvas.style.width = `${width}px`
    canvas.style.height = `${height}px`
    const ctx = canvas.getContext("2d")
    if (ctx) ctx.scale(dpr, dpr)

    const cols = Math.floor((width + gap) / (dotSize + gap))
    const rows = Math.floor((height + gap) / (dotSize + gap))
    const cell = dotSize + gap

    const gridW = cell * cols - gap
    const gridH = cell * rows - gap

    const extraX = width - gridW
    const extraY = height - gridH

    const startX = extraX / 2 + dotSize / 2
    const startY = extraY / 2 + dotSize / 2

    const dots: Array<{ cx: number; cy: number }> = []
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const cx = startX + x * cell
        const cy = startY + y * cell
        dots.push({ cx, cy })
      }
    }
    dotsRef.current = dots
  }, [dotSize, gap])

  useEffect(() => {
    if (!circlePath) return

    const proxSq = proximity * proximity

    const draw = () => {
      const canvas = canvasRef.current
      if (!canvas) return
      const ctx = canvas.getContext("2d")
      if (!ctx) return
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const { x: px, y: py } = pointerRef.current

      for (const dot of dotsRef.current) {
        const dx = dot.cx - px
        const dy = dot.cy - py
        const dsq = dx * dx + dy * dy

        let style = baseColor
        if (dsq <= proxSq) {
          const dist = Math.sqrt(dsq)
          const t = 1 - dist / proximity
          const r = Math.round(baseRgb.r + (activeRgb.r - baseRgb.r) * t)
          const g = Math.round(baseRgb.g + (activeRgb.g - baseRgb.g) * t)
          const b = Math.round(baseRgb.b + (activeRgb.b - baseRgb.b) * t)
          style = `rgb(${r},${g},${b})`
        }

        ctx.save()
        ctx.translate(dot.cx, dot.cy)
        ctx.fillStyle = style
        ctx.fill(circlePath)
        ctx.restore()
      }

      rafRef.current = requestAnimationFrame(draw)
    }

    draw()
    return () => cancelAnimationFrame(rafRef.current)
  }, [proximity, baseColor, activeRgb, baseRgb, circlePath])

  useEffect(() => {
    buildGrid()
    const ro = new ResizeObserver(buildGrid)
    if (wrapperRef.current) {
      ro.observe(wrapperRef.current)
    }
    return () => {
      ro.disconnect()
    }
  }, [buildGrid])

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      const canvas = canvasRef.current
      if (!canvas) return
      const rect = canvas.getBoundingClientRect()
      pointerRef.current.x = e.clientX - rect.left
      pointerRef.current.y = e.clientY - rect.top
    }

    const onLeave = () => {
      pointerRef.current.x = -1000
      pointerRef.current.y = -1000
    }

    window.addEventListener("mousemove", onMove, { passive: true })
    window.addEventListener("mouseleave", onLeave)

    return () => {
      window.removeEventListener("mousemove", onMove)
      window.removeEventListener("mouseleave", onLeave)
    }
  }, [])

  return (
    <section
      className={cn("absolute inset-0 overflow-hidden", className)}
      style={style}
    >
      <div ref={wrapperRef} className="h-full w-full">
        <canvas ref={canvasRef} className="block h-full w-full" />
      </div>
    </section>
  )
}
