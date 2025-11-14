'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import { Users, Calendar, AlertCircle, CheckCircle2, Sparkles } from 'lucide-react'
import { personsApi, dashboardApi, type Person, type PersonDashboard } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { GrowingLogo, OrganicCard, GrowthMetric, LeafBadge, BranchDivider } from '@/components/nature-ui'

const DEFAULT_ORG_ID = '00000000-0000-0000-0000-000000000001'

interface ClientWithAttention extends Person {
  needsAttention: string[]
  dashboard?: PersonDashboard
}

interface Stats {
  totalClients: number
  totalProjects: number
  upcomingDates: number
  needsAttention: number
}

export default function HomePage() {
  const router = useRouter()
  const [showLogo, setShowLogo] = useState(true)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [clients, setClients] = useState<ClientWithAttention[]>([])
  const [stats, setStats] = useState<Stats>({
    totalClients: 0,
    totalProjects: 0,
    upcomingDates: 0,
    needsAttention: 0,
  })

  useEffect(() => {
    // Show logo animation first, then load data
    const timer = setTimeout(() => {
      setShowLogo(false)
      loadDashboardData()
    }, 1300)

    return () => clearTimeout(timer)
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Load all clients
      const response = await personsApi.list(DEFAULT_ORG_ID, 'client')
      const clientsData = response.data

      // Get dashboard data for each client (in parallel)
      const dashboardPromises = clientsData.map(client =>
        dashboardApi.getPersonDashboard(client.person_id)
          .then(res => ({ client, dashboard: res.data }))
          .catch(() => ({ client, dashboard: null }))
      )

      const dashboards = await Promise.all(dashboardPromises)

      // Calculate who needs attention
      const clientsNeedingAttention = dashboards
        .map(({ client, dashboard }) => {
          const needsAttention: string[] = []

          if (dashboard) {
            // No contact in 7 days
            if (dashboard.recent_conversations.length > 0) {
              const lastContact = new Date(dashboard.recent_conversations[0].last_message_at)
              const daysSinceContact = (Date.now() - lastContact.getTime()) / (1000 * 60 * 60 * 24)
              if (daysSinceContact > 7) {
                needsAttention.push(`No contact in ${Math.floor(daysSinceContact)} days`)
              }
            }

            // Upcoming dates this week
            const datesThisWeek = dashboard.upcoming_dates.filter(d => d.days_until <= 7 && d.days_until >= 0)
            if (datesThisWeek.length > 0) {
              needsAttention.push(`${datesThisWeek.length} date(s) this week`)
            }

            // Projects due soon
            const projectsDueSoon = dashboard.active_projects.filter(p => {
              if (!p.due_date) return false
              const daysUntilDue = (new Date(p.due_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
              return daysUntilDue <= 7 && daysUntilDue >= 0
            })
            if (projectsDueSoon.length > 0) {
              needsAttention.push(`${projectsDueSoon.length} project(s) due soon`)
            }
          }

          return {
            ...client,
            needsAttention,
            dashboard: dashboard || undefined,
          }
        })
        .filter(c => c.needsAttention.length > 0)

      setClients(clientsNeedingAttention)

      // Calculate stats
      setStats({
        totalClients: clientsData.length,
        totalProjects: dashboards.reduce((sum, d) => sum + (d.dashboard?.stats.total_active_projects || 0), 0),
        upcomingDates: dashboards.reduce((sum, d) => sum + (d.dashboard?.stats.total_upcoming_dates || 0), 0),
        needsAttention: clientsNeedingAttention.length,
      })
    } catch (error) {
      console.error('Failed to load dashboard:', error)
      setError('Failed to load dashboard data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Logo animation screen
  if (showLogo) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sage-white via-sage-light to-sage-white flex items-center justify-center">
        <div className="w-[400px] h-96">
          <GrowingLogo onComplete={() => {}} size={300} />
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-sage-white">
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="animate-root-pulse">
              <Sparkles className="w-16 h-16 text-sage-dark mx-auto mb-4" />
            </div>
            <p className="font-ui text-sage-dark">Loading dashboard...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-sage-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <OrganicCard className="p-fib5 bg-gold-accent/10 border-gold-accent/30">
            <div className="flex items-center">
              <AlertCircle className="h-6 w-6 text-gold-accent mr-3" />
              <p className="text-earth-dark font-ui">{error}</p>
            </div>
            <Button
              variant="secondary"
              className="mt-fib3 bg-sage-dark text-white hover:bg-sage-dark/90"
              onClick={loadDashboardData}
            >
              Retry
            </Button>
          </OrganicCard>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-sage-white relative overflow-hidden">
      {/* Decorative background roots - subtle */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.02]">
        <svg className="w-full h-full" viewBox="0 0 1000 1000" preserveAspectRatio="xMidYMid slice">
          <path d="M 500 1000 Q 500 800 500 600" stroke="#736E58" strokeWidth="4" fill="none" />
          <path d="M 500 1000 Q 300 850 200 700" stroke="#736E58" strokeWidth="3" fill="none" />
          <path d="M 500 1000 Q 700 850 800 700" stroke="#736E58" strokeWidth="3" fill="none" />
          <path d="M 500 1000 Q 150 900 100 800" stroke="#736E58" strokeWidth="2" fill="none" />
          <path d="M 500 1000 Q 850 900 900 800" stroke="#736E58" strokeWidth="2" fill="none" />
        </svg>
      </div>

      {/* Header */}
      <header className="relative bg-gradient-to-r from-white via-sage-light/30 to-white border-b-2 border-sage-medium/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-fib4 sm:px-fib5">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center gap-fib3">
              {/* Actual Athena logo */}
              <Image
                src="/images/athena-logo.png"
                alt="Athena"
                width={180}
                height={48}
                className="h-12 w-auto"
                priority
              />
              <span className="text-root font-ui text-earth-dark/60 ml-2">Staff Portal</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-fib4 sm:px-fib5 py-fib5">
        {/* Page Header */}
        <div className="mb-fib5 animate-grow-in">
          <h2 className="text-trunk font-display font-semibold text-sage-dark mb-fib2">
            Dashboard
          </h2>
          <p className="text-sprout font-ui text-earth-dark/70 max-w-2xl">
            Manage client relationships and track your projects
          </p>
        </div>

        <BranchDivider className="mb-fib5" />

        {/* Metrics */}
        <div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-fib3 mb-fib5"
          style={{
            animation: 'growIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.1s backwards',
          }}
        >
          <GrowthMetric
            label="Active Clients"
            value={stats.totalClients}
            color="sage"
            icon={<Users className="w-full h-full" />}
          />
          <GrowthMetric
            label="Active Projects"
            value={stats.totalProjects}
            color="sage"
            icon={<CheckCircle2 className="w-full h-full" />}
          />
          <GrowthMetric
            label="Upcoming Dates"
            value={stats.upcomingDates}
            color="earth"
            icon={<Calendar className="w-full h-full" />}
          />
          <GrowthMetric
            label="Need Attention"
            value={stats.needsAttention}
            color="gold"
            icon={<AlertCircle className="w-full h-full" />}
          />
        </div>

        {/* Clients Needing Attention */}
        <OrganicCard
          className="p-fib5 mb-fib5"
          variant="glass"
          withBranch
          style={{
            animation: 'growIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s backwards',
          }}
        >
          <div className="flex items-center justify-between mb-fib4">
            <div>
              <h3 className="text-branch font-display font-semibold text-sage-dark mb-fib1">
                Clients Needing Attention
              </h3>
              <p className="text-root font-ui text-earth-dark/60">
                Clients who require follow-up
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => router.push('/clients')}
              className="rounded-organic-sm border-sage-dark text-sage-dark hover:bg-sage-dark hover:text-white transition-colors"
            >
              View All
            </Button>
          </div>

          <BranchDivider className="mb-fib4" />

          {clients.length === 0 ? (
            <div className="text-center py-fib5">
              <Sparkles className="w-12 h-12 text-gold-accent mx-auto mb-fib3 animate-leaf-rustle" />
              <p className="text-sprout font-ui text-sage-dark">
                All clients are up to date
              </p>
            </div>
          ) : (
            <div className="space-y-fib3">
              {clients.map((client, idx) => (
                <OrganicCard
                  key={client.person_id}
                  className="p-fib3 bg-white hover:bg-sage-light/50 cursor-pointer transition-all"
                  hover
                  onClick={() => router.push(`/clients/${client.person_id}`)}
                  style={{
                    animation: `growIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) ${0.3 + idx * 0.1}s backwards`,
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="font-display font-semibold text-stem text-earth-dark mb-fib2">
                        {client.full_name}
                      </p>
                      <div className="flex flex-wrap gap-fib1">
                        {client.needsAttention.map((reason, idx) => (
                          <LeafBadge key={idx} variant="warning">
                            {reason}
                          </LeafBadge>
                        ))}
                      </div>
                    </div>
                    <div className="ml-fib3 text-sage-dark opacity-50 hover:opacity-100 transition-opacity">
                      <span className="text-sprout font-ui">→</span>
                    </div>
                  </div>
                </OrganicCard>
              ))}
            </div>
          )}
        </OrganicCard>

        {/* Quick Actions - Asymmetric branching layout */}
        <div>
          <h3 className="text-branch font-display font-semibold text-sage-dark mb-fib4">
            Quick Actions
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-fib3">
            <OrganicCard
              className="p-fib4 bg-gradient-to-br from-sage-dark to-sage-medium text-white group"
              hover
              onClick={() => router.push('/clients/new')}
              style={{
                animation: 'growIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.35s backwards',
              }}
            >
              <div className="relative">
                <div className="w-10 h-10 mb-fib3 rounded-organic-sm bg-white/20 flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <h4 className="font-display font-semibold text-stem mb-fib2">
                  Add New Client
                </h4>
                <p className="text-root font-ui text-white/80">
                  Create a new client profile
                </p>
              </div>
            </OrganicCard>

            <OrganicCard
              className="p-fib4 bg-white"
              hover
              withBranch
              onClick={() => router.push('/clients')}
              style={{
                animation: 'growIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.4s backwards',
              }}
            >
              <div className="relative">
                <div className="w-10 h-10 mb-fib3 rounded-organic-sm bg-sage-light flex items-center justify-center">
                  <Users className="w-6 h-6 text-sage-dark" />
                </div>
                <h4 className="font-display font-semibold text-stem text-earth-dark mb-fib2">
                  View All Clients
                </h4>
                <p className="text-root font-ui text-earth-dark/70">
                  Browse and manage all clients
                </p>
              </div>
            </OrganicCard>

            <OrganicCard
              className="p-fib4 bg-white"
              hover
              onClick={() => router.push('/calendar')}
              style={{
                animation: 'growIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.45s backwards',
              }}
            >
              <div className="relative">
                <div className="w-10 h-10 mb-fib3 rounded-organic-sm bg-gold-accent/20 flex items-center justify-center">
                  <Calendar className="w-6 h-6 text-gold-accent" />
                </div>
                <h4 className="font-display font-semibold text-stem text-earth-dark mb-fib2">
                  Calendar
                </h4>
                <p className="text-root font-ui text-earth-dark/70">
                  View all important dates
                </p>
              </div>
            </OrganicCard>
          </div>
        </div>

        {/* Footer decoration */}
        <div className="mt-fib6 pt-fib5 border-t-2 border-dashed border-sage-medium/30">
          <div className="flex justify-center items-center gap-fib2 text-root font-ui text-earth-dark/40">
            <div className="w-2 h-2 rounded-full bg-sage-medium animate-root-pulse" />
            <span>Excellence in service</span>
            <div className="w-2 h-2 rounded-full bg-sage-medium animate-root-pulse" style={{ animationDelay: '0.5s' }} />
          </div>
        </div>
      </main>
    </div>
  )
}
