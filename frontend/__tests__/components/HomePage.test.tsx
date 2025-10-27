import { render, screen, waitFor } from '@testing-library/react'
import HomePage from '@/app/page'

// Mock fetch
global.fetch = jest.fn()

describe('HomePage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the page title', () => {
    render(<HomePage />)
    expect(screen.getByText('Athena Concierge')).toBeInTheDocument()
    expect(screen.getByText('Staff Dashboard')).toBeInTheDocument()
  })

  it('displays welcome message', () => {
    render(<HomePage />)
    expect(screen.getByText('Welcome Back')).toBeInTheDocument()
    expect(
      screen.getByText('Manage your clients, projects, and conversations from the staff dashboard')
    ).toBeInTheDocument()
  })

  it('displays all navigation cards', () => {
    render(<HomePage />)

    expect(screen.getByText('Clients')).toBeInTheDocument()
    expect(screen.getByText('Projects')).toBeInTheDocument()
    expect(screen.getByText('Conversations')).toBeInTheDocument()
    expect(screen.getByText('Calendar')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('checks API health on mount', async () => {
    const mockFetch = global.fetch as jest.Mock
    mockFetch.mockResolvedValueOnce({
      json: async () => ({ status: 'healthy' }),
    })

    render(<HomePage />)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/health')
      )
    })
  })

  it('displays API status as healthy when health check succeeds', async () => {
    const mockFetch = global.fetch as jest.Mock
    mockFetch.mockResolvedValueOnce({
      json: async () => ({ status: 'healthy' }),
    })

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('API healthy')).toBeInTheDocument()
    })
  })

  it('displays API status as error when health check fails', async () => {
    const mockFetch = global.fetch as jest.Mock
    mockFetch.mockRejectedValueOnce(new Error('API Error'))

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('API error')).toBeInTheDocument()
    })
  })

  it('displays system information', () => {
    render(<HomePage />)

    expect(screen.getByText('System Information')).toBeInTheDocument()
    expect(screen.getByText('Version')).toBeInTheDocument()
    expect(screen.getByText('2.0.0')).toBeInTheDocument()
    expect(screen.getByText('Environment')).toBeInTheDocument()
    expect(screen.getByText('Active Agents')).toBeInTheDocument()
  })

  it('renders navigation links correctly', () => {
    render(<HomePage />)

    const links = [
      { text: 'Clients', href: '/clients' },
      { text: 'Projects', href: '/projects' },
      { text: 'Conversations', href: '/conversations' },
      { text: 'Calendar', href: '/calendar' },
      { text: 'Settings', href: '/settings' },
    ]

    links.forEach(({ text }) => {
      const element = screen.getByText(text)
      expect(element.closest('a')).toBeInTheDocument()
    })
  })
})
