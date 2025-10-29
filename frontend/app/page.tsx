'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Users, FolderKanban, Calendar, AlertCircle, CheckSquare } from 'lucide-react'
import { personsApi, dashboardApi, type Person, type PersonDashboard } from '@/lib/api'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'

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
    loadDashboardData()
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <header className="bg-white border-b border-slate-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <h1 className="text-2xl font-bold text-slate-900">AI Concierge - Staff Portal</h1>
            </div>
          </div>
        </header>
        <div className="flex items-center justify-center h-96">
          <Spinner size="lg" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <header className="bg-white border-b border-slate-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <h1 className="text-2xl font-bold text-slate-900">AI Concierge - Staff Portal</h1>
            </div>
          </div>
        </header>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <Card className="p-6 bg-red-50 border-red-200">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
              <p className="text-red-800">{error}</p>
            </div>
            <Button variant="secondary" className="mt-4" onClick={loadDashboardData}>
              Retry
            </Button>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-slate-900">AI Concierge</h1>
              <span className="ml-3 px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                Staff Portal
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-slate-900">Dashboard</h2>
          <p className="text-slate-600 mt-2">Manage client relationships and track important dates</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Active Clients</p>
                <p className="text-3xl font-bold text-slate-900">{stats.totalClients}</p>
              </div>
              <Users className="w-10 h-10 text-blue-500" />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Active Projects</p>
                <p className="text-3xl font-bold text-slate-900">{stats.totalProjects}</p>
              </div>
              <CheckSquare className="w-10 h-10 text-green-500" />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Upcoming Dates</p>
                <p className="text-3xl font-bold text-slate-900">{stats.upcomingDates}</p>
              </div>
              <Calendar className="w-10 h-10 text-purple-500" />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Need Attention</p>
                <p className="text-3xl font-bold text-red-600">{stats.needsAttention}</p>
              </div>
              <AlertCircle className="w-10 h-10 text-red-500" />
            </div>
          </Card>
        </div>

        {/* Clients Needing Attention */}
        <Card className="p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-slate-900">Clients Needing Attention</h3>
            <Button
              variant="outline"
              onClick={() => router.push('/clients')}
            >
              View All Clients
            </Button>
          </div>

          {clients.length === 0 ? (
            <p className="text-slate-500">All clients are up to date! 🎉</p>
          ) : (
            <div className="space-y-4">
              {clients.map(client => (
                <div
                  key={client.person_id}
                  className="flex items-center justify-between p-4 bg-slate-50 rounded-lg hover:bg-slate-100 cursor-pointer transition"
                  onClick={() => router.push(`/clients/${client.person_id}`)}
                >
                  <div>
                    <p className="font-semibold text-slate-900">{client.full_name}</p>
                    <div className="flex gap-2 mt-2">
                      {client.needsAttention.map((reason, idx) => (
                        <Badge key={idx} variant="warning">
                          {reason}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <Button variant="ghost" size="sm">
                    View Profile →
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card
            className="p-6 hover:shadow-lg transition cursor-pointer"
            onClick={() => router.push('/clients/new')}
          >
            <h4 className="font-semibold text-slate-900 mb-2">+ New Client</h4>
            <p className="text-sm text-slate-600">Add a new client to the system</p>
          </Card>

          <Card
            className="p-6 hover:shadow-lg transition cursor-pointer"
            onClick={() => router.push('/clients')}
          >
            <h4 className="font-semibold text-slate-900 mb-2">View All Clients</h4>
            <p className="text-sm text-slate-600">Browse and search all clients</p>
          </Card>

          <Card
            className="p-6 hover:shadow-lg transition cursor-pointer"
            onClick={() => router.push('/calendar')}
          >
            <h4 className="font-semibold text-slate-900 mb-2">Calendar View</h4>
            <p className="text-sm text-slate-600">See all important dates</p>
          </Card>
        </div>
      </main>
    </div>
  )
}
