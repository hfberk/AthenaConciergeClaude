/**
 * Example component tests demonstrating best practices
 *
 * This file shows how to:
 * - Test component rendering
 * - Test user interactions
 * - Test async behavior
 * - Test accessibility
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Example Button Component (inline for demonstration)
function Button({ onClick, children, disabled = false }: {
  onClick: () => void;
  children: React.ReactNode;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="px-4 py-2 bg-blue-600 text-white rounded"
    >
      {children}
    </button>
  )
}

describe('Button Component (Example)', () => {
  it('renders button with text', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)

    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)

    fireEvent.click(screen.getByText('Click me'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('does not call onClick when disabled', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick} disabled>Click me</Button>)

    const button = screen.getByText('Click me')
    fireEvent.click(button)
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('is accessible via keyboard', async () => {
    const user = userEvent.setup()
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)

    const button = screen.getByText('Click me')
    button.focus()
    await user.keyboard('{Enter}')

    expect(handleClick).toHaveBeenCalled()
  })
})

// Example AsyncComponent (inline for demonstration)
function AsyncComponent({ fetchData }: { fetchData: () => Promise<string> }) {
  const [data, setData] = React.useState<string>('Loading...')
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    fetchData()
      .then(setData)
      .catch(() => setError('Error loading data'))
  }, [fetchData])

  if (error) return <div>{error}</div>
  return <div>{data}</div>
}

import React from 'react'

describe('AsyncComponent (Example)', () => {
  it('shows loading state initially', () => {
    const mockFetch = jest.fn(() => new Promise(() => {}))
    render(<AsyncComponent fetchData={mockFetch} />)

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('displays data after successful fetch', async () => {
    const mockFetch = jest.fn(() => Promise.resolve('Loaded data'))
    render(<AsyncComponent fetchData={mockFetch} />)

    await waitFor(() => {
      expect(screen.getByText('Loaded data')).toBeInTheDocument()
    })
  })

  it('displays error message on fetch failure', async () => {
    const mockFetch = jest.fn(() => Promise.reject(new Error('Fetch failed')))
    render(<AsyncComponent fetchData={mockFetch} />)

    await waitFor(() => {
      expect(screen.getByText('Error loading data')).toBeInTheDocument()
    })
  })
})
