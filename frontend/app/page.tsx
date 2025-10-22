'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Users, FolderKanban, MessageSquare, Calendar, Settings } from 'lucide-react'

export default function HomePage() {
  const [apiHealth, setApiHealth] = useState<string>('checking')

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`)
        const data = await response.json()
        setApiHealth(data.status)
      } catch (error) {
        setApiHealth('error')
      }
    }
    checkHealth()
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-slate-900">Athena Concierge</h1>
              <span className="ml-3 px-2 py-1 text-xs font-medium rounded-full bg-primary-100 text-primary-800">
                Staff Dashboard
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`h-2 w-2 rounded-full ${
                apiHealth === 'healthy' ? 'bg-green-500' :
                apiHealth === 'checking' ? 'bg-yellow-500' :
                'bg-red-500'
              }`} />
              <span className="text-sm text-slate-600">
                API {apiHealth}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Welcome Section */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-slate-900 mb-2">Welcome Back</h2>
          <p className="text-slate-600">
            Manage your clients, projects, and conversations from the staff dashboard
          </p>
        </div>

        {/* Quick Actions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Clients Card */}
          <Link href="/clients">
            <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-6 cursor-pointer border border-slate-200">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Users className="h-6 w-6 text-blue-600" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Clients</h3>
              <p className="text-slate-600 text-sm">
                View and manage client profiles, preferences, and households
              </p>
            </div>
          </Link>

          {/* Projects Card */}
          <Link href="/projects">
            <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-6 cursor-pointer border border-slate-200">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <FolderKanban className="h-6 w-6 text-purple-600" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Projects</h3>
              <p className="text-slate-600 text-sm">
                Track active projects, tasks, and deadlines
              </p>
            </div>
          </Link>

          {/* Conversations Card */}
          <Link href="/conversations">
            <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-6 cursor-pointer border border-slate-200">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <MessageSquare className="h-6 w-6 text-green-600" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Conversations</h3>
              <p className="text-slate-600 text-sm">
                Review AI interactions and message history
              </p>
            </div>
          </Link>

          {/* Calendar Card */}
          <Link href="/calendar">
            <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-6 cursor-pointer border border-slate-200">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-orange-100 rounded-lg">
                  <Calendar className="h-6 w-6 text-orange-600" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Calendar</h3>
              <p className="text-slate-600 text-sm">
                Important dates, reminders, and upcoming events
              </p>
            </div>
          </Link>

          {/* Settings Card */}
          <Link href="/settings">
            <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-6 cursor-pointer border border-slate-200">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-slate-100 rounded-lg">
                  <Settings className="h-6 w-6 text-slate-600" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Settings</h3>
              <p className="text-slate-600 text-sm">
                Configure agents, integrations, and preferences
              </p>
            </div>
          </Link>
        </div>

        {/* System Info */}
        <div className="mt-12 bg-white rounded-lg shadow-sm p-6 border border-slate-200">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">System Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-slate-600 mb-1">Version</p>
              <p className="text-lg font-semibold text-slate-900">2.0.0</p>
            </div>
            <div>
              <p className="text-sm text-slate-600 mb-1">Environment</p>
              <p className="text-lg font-semibold text-slate-900">Development</p>
            </div>
            <div>
              <p className="text-sm text-slate-600 mb-1">Active Agents</p>
              <p className="text-lg font-semibold text-slate-900">6</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
