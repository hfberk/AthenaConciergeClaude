'use client'

import React, { useEffect, useState } from 'react'
import Image from 'next/image'

interface GrowingLogoProps {
  onComplete?: () => void
  skipAnimation?: boolean
  size?: number
}

export function GrowingLogo({ onComplete, skipAnimation = false, size = 200 }: GrowingLogoProps) {
  const [animationStage, setAnimationStage] = useState(0)

  useEffect(() => {
    if (skipAnimation) {
      setAnimationStage(4)
      onComplete?.()
      return
    }

    const timings = [
      { delay: 0, stage: 1 },     // Roots appear
      { delay: 400, stage: 2 },   // Trunk rises
      { delay: 700, stage: 3 },   // Branches extend
      { delay: 1000, stage: 4 },  // Leaves appear
    ]

    const timeouts = timings.map(({ delay, stage }) =>
      setTimeout(() => setAnimationStage(stage), delay)
    )

    // Complete callback
    const completeTimeout = setTimeout(() => {
      onComplete?.()
    }, 1200)

    return () => {
      timeouts.forEach(clearTimeout)
      clearTimeout(completeTimeout)
    }
  }, [skipAnimation, onComplete])

  return (
    <div className="relative flex items-center justify-center w-full h-full overflow-hidden">
      {/* Root network - grows from bottom */}
      <svg
        className="absolute inset-0 w-full h-full"
        viewBox="0 0 400 400"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="rootGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#736E58" stopOpacity="0" />
            <stop offset="100%" stopColor="#736E58" stopOpacity="0.3" />
          </linearGradient>
        </defs>

        {/* Root tendrils */}
        <g
          style={{
            opacity: animationStage >= 1 ? 1 : 0,
            transform: animationStage >= 1 ? 'translateY(0)' : 'translateY(40px)',
            transition: 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
          }}
        >
          {/* Center root */}
          <path
            d="M 200 400 Q 200 350 200 300"
            stroke="url(#rootGradient)"
            strokeWidth="3"
            strokeDasharray="4 4"
          />
          {/* Left roots */}
          <path
            d="M 200 400 Q 150 370 120 340"
            stroke="url(#rootGradient)"
            strokeWidth="2"
            strokeDasharray="4 4"
            style={{ animationDelay: '0.1s' }}
          />
          <path
            d="M 200 400 Q 100 360 60 320"
            stroke="url(#rootGradient)"
            strokeWidth="1.5"
            strokeDasharray="4 4"
            style={{ animationDelay: '0.2s' }}
          />
          {/* Right roots */}
          <path
            d="M 200 400 Q 250 370 280 340"
            stroke="url(#rootGradient)"
            strokeWidth="2"
            strokeDasharray="4 4"
            style={{ animationDelay: '0.15s' }}
          />
          <path
            d="M 200 400 Q 300 360 340 320"
            stroke="url(#rootGradient)"
            strokeWidth="1.5"
            strokeDasharray="4 4"
            style={{ animationDelay: '0.25s' }}
          />
        </g>
      </svg>

      {/* Main logo container - grows from center */}
      <div
        className="relative z-10 transition-all duration-700 flex flex-col items-center"
        style={{
          opacity: animationStage >= 2 ? 1 : 0,
          transform:
            animationStage >= 2
              ? 'scale(1) translateY(0)'
              : 'scale(0.5) translateY(60px)',
          transitionTimingFunction: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        }}
      >
        {/* Actual logo image */}
        <div
          className="relative"
          style={{
            filter: animationStage >= 2 ? 'none' : 'blur(4px)',
            transition: 'filter 0.3s ease-out',
            width: size,
            height: size,
          }}
        >
          <Image
            src="/images/athena-logo.png"
            alt="Athena Logo"
            width={size}
            height={size}
            className={animationStage >= 4 ? 'animate-leaf-rustle' : ''}
            priority
          />
        </div>
      </div>

      {/* Floating leaf particles - ambient animation */}
      {animationStage >= 4 && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="absolute w-2 h-2 bg-sage-medium rounded-full animate-leaf-rustle opacity-20"
              style={{
                left: `${20 + i * 15}%`,
                top: `${30 + (i % 3) * 20}%`,
                animationDelay: `${i * 0.3}s`,
                animationDuration: `${3 + i * 0.5}s`,
              }}
            />
          ))}
        </div>
      )}
    </div>
  )
}
