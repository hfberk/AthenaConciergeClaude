/**
 * API client for backend communication
 */

import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Person API
export const personsApi = {
  list: (orgId: string, personType?: string) =>
    apiClient.get('/persons/', { params: { org_id: orgId, person_type: personType } }),

  get: (personId: string) =>
    apiClient.get(`/persons/${personId}`),

  create: (data: any) =>
    apiClient.post('/persons/', data),

  update: (personId: string, data: any) =>
    apiClient.put(`/persons/${personId}`, data),

  delete: (personId: string) =>
    apiClient.delete(`/persons/${personId}`),
}

// Project API
export const projectsApi = {
  list: (orgId: string, personId?: string, status?: string) =>
    apiClient.get('/projects/', { params: { org_id: orgId, person_id: personId, status } }),

  get: (projectId: string) =>
    apiClient.get(`/projects/${projectId}`),

  create: (data: any) =>
    apiClient.post('/projects/', data),

  update: (projectId: string, data: any) =>
    apiClient.put(`/projects/${projectId}`, data),

  getTasks: (projectId: string) =>
    apiClient.get(`/projects/${projectId}/tasks`),

  createTask: (projectId: string, data: any) =>
    apiClient.post(`/projects/${projectId}/tasks`, data),
}

// Conversation API
export const conversationsApi = {
  list: (orgId: string, personId?: string) =>
    apiClient.get('/conversations/', { params: { org_id: orgId, person_id: personId } }),

  get: (conversationId: string) =>
    apiClient.get(`/conversations/${conversationId}`),

  getMessages: (conversationId: string) =>
    apiClient.get(`/conversations/${conversationId}/messages`),
}

// Agent API
export const agentsApi = {
  chat: (data: { person_id: string; message: string; conversation_id?: string }) =>
    apiClient.post('/agents/chat', data),

  health: () =>
    apiClient.get('/agents/health'),
}

export default apiClient
