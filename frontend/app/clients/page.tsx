'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Search, UserPlus, Calendar, FolderKanban, MessageSquare } from 'lucide-react'
import { personsApi, dashboardApi, type Person, type PersonDashboard } from '@/lib/api'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Spinner } from '@/components/ui/Spinner'
import { Badge } from '@/components/ui/Badge'

const DEFAULT_ORG_ID = '00000000-0000-0000-0000-000000000001'

interface ClientWithStats extends Person {
  dashboard?: PersonDashboard
  upcomingDatesCount: number
  activeProjectsCount: number
  conversationsCount: number
  lastContact?: Date
}

export default function ClientsPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [clients, setClients] = useState<ClientWithStats[]>([])
  const [filteredClients, setFilteredClients] = useState<ClientWithStats[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'name' | 'last_contact' | 'join_date'>('name')

  useEffect(() => {
    loadClients()
  }, [])

  useEffect(() => {
    filterAndSortClients()
  }, [clients, searchQuery, sortBy])

  const loadClients = async () => {
    try {
      setLoading(true)

      // Load all clients
      const response = await personsApi.list(DEFAULT_ORG_ID, 'client')
      const clientsData = response.data

      // Get dashboard data for each client (in parallel)
      const clientsWithStats: ClientWithStats[] = await Promise.all(
        clientsData.map(async client => {
          try {
            const dashboard = await dashboardApi.getPersonDashboard(client.person_id)
            const lastContact = dashboard.data.recent_conversations.length > 0
              ? new Date(dashboard.data.recent_conversations[0].last_message_at)
              : undefined

            return {
              ...client,
              dashboard: dashboard.data,
              upcomingDatesCount: dashboard.data.stats.total_upcoming_dates,
              activeProjectsCount: dashboard.data.stats.total_active_projects,
              conversationsCount: dashboard.data.stats.total_conversations,
              lastContact,
            }
          } catch {
            // If dashboard fails, return client with zero stats
            return {
              ...client,
              upcomingDatesCount: 0,
              activeProjectsCount: 0,
              conversationsCount: 0,
            }
          }
        })
      )

      setClients(clientsWithStats)
    } catch (error) {
      console.error('Failed to load clients:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterAndSortClients = () => {
    let filtered = clients

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(
        client =>
          client.full_name.toLowerCase().includes(query) ||
          client.preferred_name?.toLowerCase().includes(query)
      )
    }

    // Apply sort
    filtered = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.full_name.localeCompare(b.full_name)
        case 'last_contact':
          if (!a.lastContact) return 1
          if (!b.lastContact) return -1
          return b.lastContact.getTime() - a.lastContact.getTime()
        case 'join_date':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        default:
          return 0
      }
    })

    setFilteredClients(filtered)
  }

  const formatLastContact = (date?: Date) => {
    if (!date) return 'Never'
    const days = Math.floor((Date.now() - date.getTime()) / (1000 * 60 * 60 * 24))
    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    if (days < 7) return `${days} days ago`
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`
    return `${Math.floor(days / 30)} months ago`
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-center justify-center h-96">
            <Spinner size="lg" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Clients</h1>
            <p className="text-slate-600 mt-2">
              Manage your client relationships and profiles
            </p>
          </div>
          <Button
            onClick={() => router.push('/clients/new')}
            className="flex items-center gap-2"
          >
            <UserPlus className="h-4 w-4" />
            New Client
          </Button>
        </div>

        {/* Search and Filter Bar */}
        <Card className="p-4 mb-6">
          <div className="flex gap-4 items-center">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                type="text"
                placeholder="Search by name..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="w-48">
              <Select value={sortBy} onChange={e => setSortBy(e.target.value as any)}>
                <option value="name">Sort by Name</option>
                <option value="last_contact">Sort by Last Contact</option>
                <option value="join_date">Sort by Join Date</option>
              </Select>
            </div>
          </div>
        </Card>

        {/* Results Count */}
        <div className="mb-4">
          <p className="text-sm text-slate-600">
            Showing {filteredClients.length} of {clients.length} clients
          </p>
        </div>

        {/* Clients Grid */}
        {filteredClients.length === 0 ? (
          <Card className="p-12 text-center">
            <p className="text-slate-500">
              {searchQuery ? 'No clients found matching your search.' : 'No clients yet.'}
            </p>
            {!searchQuery && (
              <Button
                variant="secondary"
                className="mt-4"
                onClick={() => router.push('/clients/new')}
              >
                Add Your First Client
              </Button>
            )}
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredClients.map(client => (
              <Card
                key={client.person_id}
                className="p-6 hover:shadow-lg transition cursor-pointer"
                onClick={() => router.push(`/clients/${client.person_id}`)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">
                      {client.full_name}
                    </h3>
                    {client.preferred_name && (
                      <p className="text-sm text-slate-500">"{client.preferred_name}"</p>
                    )}
                  </div>
                  {client.person_type && (
                    <Badge variant="secondary" className="text-xs">
                      {client.person_type}
                    </Badge>
                  )}
                </div>

                {/* Quick Stats */}
                <div className="space-y-2 mb-4">
                  <div className="flex items-center text-sm text-slate-600">
                    <Calendar className="h-4 w-4 mr-2 text-purple-500" />
                    {client.upcomingDatesCount} upcoming dates
                  </div>
                  <div className="flex items-center text-sm text-slate-600">
                    <FolderKanban className="h-4 w-4 mr-2 text-green-500" />
                    {client.activeProjectsCount} active projects
                  </div>
                  <div className="flex items-center text-sm text-slate-600">
                    <MessageSquare className="h-4 w-4 mr-2 text-blue-500" />
                    {client.conversationsCount} conversations
                  </div>
                </div>

                {/* Last Contact */}
                <div className="pt-4 border-t border-slate-200">
                  <p className="text-xs text-slate-500">
                    Last contact: {formatLastContact(client.lastContact)}
                  </p>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
