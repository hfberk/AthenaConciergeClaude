// MSW (Mock Service Worker) handlers for API mocking
import { http, HttpResponse } from 'msw'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const handlers = [
  // Health check endpoint
  http.get(`${API_URL}/health`, () => {
    return HttpResponse.json({
      status: 'healthy',
      version: '1.0.0-test',
      database: 'connected',
    })
  }),

  // Root endpoint
  http.get(`${API_URL}/`, () => {
    return HttpResponse.json({
      name: 'AI Concierge Test',
      version: '1.0.0-test',
      status: 'running',
    })
  }),

  // Example: Get conversations
  http.get(`${API_URL}/api/v1/conversations`, () => {
    return HttpResponse.json([
      {
        id: 1,
        household_id: 1,
        channel: 'slack',
        channel_id: 'C123456',
        status: 'active',
      },
    ])
  }),

  // Example: Get persons
  http.get(`${API_URL}/api/v1/persons`, () => {
    return HttpResponse.json([
      {
        id: 1,
        first_name: 'John',
        last_name: 'Doe',
        email: 'john.doe@example.com',
      },
    ])
  }),

  // Add more handlers as needed for your API endpoints
]
