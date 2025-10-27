/**
 * Integration tests for API communication
 * These tests use MSW (Mock Service Worker) to mock API responses
 */

import { server } from '@/__mocks__/server'

// Establish API mocking before all tests
beforeAll(() => server.listen())

// Reset any request handlers that we may add during the tests
afterEach(() => server.resetHandlers())

// Clean up after tests are finished
afterAll(() => server.close())

describe('API Integration', () => {
  it('fetches health status from API', async () => {
    const response = await fetch('http://localhost:8000/health')
    const data = await response.json()

    expect(response.ok).toBe(true)
    expect(data).toEqual({
      status: 'healthy',
      version: '1.0.0-test',
      database: 'connected',
    })
  })

  it('fetches conversations from API', async () => {
    const response = await fetch('http://localhost:8000/api/v1/conversations')
    const data = await response.json()

    expect(response.ok).toBe(true)
    expect(Array.isArray(data)).toBe(true)
    expect(data.length).toBeGreaterThan(0)
    expect(data[0]).toHaveProperty('id')
    expect(data[0]).toHaveProperty('household_id')
  })

  it('fetches persons from API', async () => {
    const response = await fetch('http://localhost:8000/api/v1/persons')
    const data = await response.json()

    expect(response.ok).toBe(true)
    expect(Array.isArray(data)).toBe(true)
    expect(data.length).toBeGreaterThan(0)
    expect(data[0]).toHaveProperty('first_name')
    expect(data[0]).toHaveProperty('email')
  })

  it('handles API errors gracefully', async () => {
    // This will use the default MSW handler
    const response = await fetch('http://localhost:8000/nonexistent')

    // MSW returns 404 for unmocked endpoints by default
    expect(response.ok).toBe(false)
  })
})
