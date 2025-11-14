'use client'

import React, { ReactNode } from 'react'

interface OrganicCardProps {
  children: ReactNode
  className?: string
  variant?: 'default' | 'accent' | 'glass'
  withBranch?: boolean
  hover?: boolean
  onClick?: () => void
  style?: React.CSSProperties
}

export function OrganicCard({
  children,
  className = '',
  variant = 'default',
  withBranch = false,
  hover = false,
  onClick,
  style,
}: OrganicCardProps) {
  const variantStyles = {
    default: 'bg-white border-sage-light',
    accent: 'bg-gradient-to-br from-sage-light to-white border-sage-medium',
    glass: 'bg-white/60 backdrop-blur-sm border-sage-medium/50',
  }

  return (
    <div
      className={`
        relative overflow-hidden
        rounded-organic shadow-organic border
        ${variantStyles[variant]}
        ${hover ? 'organic-hover cursor-pointer' : ''}
        ${className}
      `}
      onClick={onClick}
      style={style}
    >
      {/* Decorative branch in corner */}
      {withBranch && (
        <svg
          className="absolute -top-2 -right-2 w-24 h-24 text-sage-medium opacity-10 pointer-events-none"
          viewBox="0 0 100 100"
          fill="none"
        >
          <path
            d="M 0 100 Q 30 70 50 50 Q 70 30 100 0"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
          />
          <circle cx="25" cy="85" r="6" fill="currentColor" />
          <circle cx="50" cy="50" r="5" fill="currentColor" />
          <circle cx="75" cy="25" r="6" fill="currentColor" />
        </svg>
      )}

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>

      {/* Subtle root anchor at bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-sage-medium/20 to-transparent" />
    </div>
  )
}

interface GrowthMetricProps {
  label: string
  value: number | string
  icon?: ReactNode
  trend?: 'up' | 'down' | 'neutral'
  color?: 'sage' | 'gold' | 'earth'
}

export function GrowthMetric({ label, value, icon, trend, color = 'sage' }: GrowthMetricProps) {
  const colorStyles = {
    sage: 'text-sage-dark bg-sage-light/50',
    gold: 'text-gold-accent bg-gold-accent/10',
    earth: 'text-earth-dark bg-earth-dark/10',
  }

  const iconBgStyles = {
    sage: 'bg-sage-dark/10',
    gold: 'bg-gold-accent/20',
    earth: 'bg-earth-dark/10',
  }

  return (
    <OrganicCard className="p-fib4" hover>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sprout font-ui text-earth-dark/70 mb-fib1">
            {label}
          </p>
          <p className={`text-limb font-display font-semibold ${colorStyles[color].split(' ')[0]}`}>
            {value}
          </p>
        </div>

        {icon && (
          <div className={`
            w-14 h-14 rounded-organic-sm flex items-center justify-center
            ${iconBgStyles[color]}
          `}>
            <div className={`w-8 h-8 ${colorStyles[color].split(' ')[0]}`}>
              {icon}
            </div>
          </div>
        )}
      </div>

      {/* Tree ring growth indicator */}
      <div className="absolute -bottom-2 -left-2 w-16 h-16 opacity-5 pointer-events-none">
        <svg viewBox="0 0 100 100" fill="none">
          <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="2" className="text-sage-dark" />
          <circle cx="50" cy="50" r="30" stroke="currentColor" strokeWidth="2" className="text-sage-dark" />
          <circle cx="50" cy="50" r="20" stroke="currentColor" strokeWidth="2" className="text-sage-dark" />
        </svg>
      </div>
    </OrganicCard>
  )
}

interface LeafBadgeProps {
  children: ReactNode
  variant?: 'warning' | 'success' | 'info'
}

export function LeafBadge({ children, variant = 'info' }: LeafBadgeProps) {
  const variantStyles = {
    warning: 'bg-gold-accent/20 text-gold-accent border-gold-accent/30',
    success: 'bg-sage-dark/20 text-sage-dark border-sage-dark/30',
    info: 'bg-sage-medium/20 text-sage-dark border-sage-medium/30',
  }

  return (
    <span
      className={`
        inline-flex items-center px-fib2 py-fib1
        text-root font-ui font-medium
        border rounded-organic-sm
        ${variantStyles[variant]}
      `}
      style={{
        borderRadius: '12px 8px 12px 4px', // Asymmetric leaf shape
      }}
    >
      {children}
    </span>
  )
}

interface BranchDividerProps {
  className?: string
}

export function BranchDivider({ className = '' }: BranchDividerProps) {
  return (
    <div className={`w-full h-fib3 flex items-center ${className}`}>
      <svg
        viewBox="0 0 400 40"
        className="w-full h-full text-sage-medium/30"
        preserveAspectRatio="none"
      >
        <path
          d="M 0,20 Q 100,10 200,20 T 400,20"
          stroke="currentColor"
          fill="none"
          strokeWidth="2"
        />
        <circle cx="50" cy="15" r="3" fill="currentColor" opacity="0.6" />
        <circle cx="180" cy="25" r="3" fill="currentColor" opacity="0.6" />
        <circle cx="320" cy="18" r="3" fill="currentColor" opacity="0.6" />
      </svg>
    </div>
  )
}
