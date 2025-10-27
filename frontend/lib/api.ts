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

// ===========================
// Types
// ===========================

export interface Person {
  person_id: string
  org_id: string
  full_name: string
  preferred_name?: string
  person_type: 'client' | 'staff' | 'family_member'
  birthday?: string
  timezone?: string
  metadata_jsonb?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface DateCategory {
  category_id: string
  org_id: string
  category_name: string
  icon?: string
  color?: string
  schema_jsonb?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface ReminderRule {
  reminder_rule_id: string
  org_id: string
  date_item_id?: string
  comm_identity_id: string
  reminder_type: 'lead_time' | 'scheduled'
  lead_time_days?: number
  scheduled_datetime?: string
  sent_at?: string
  metadata_jsonb?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface DateItem {
  date_item_id: string
  org_id: string
  person_id: string
  category_id: string
  title: string
  date_value: string
  recurrence_rule?: string
  next_occurrence?: string
  notes?: string
  metadata_jsonb?: Record<string, any>
  reminder_rules: ReminderRule[]
  created_at: string
  updated_at: string
  deleted_at?: string
}

export interface Project {
  project_id: string
  org_id: string
  person_id: string
  title: string
  description?: string
  status: 'new' | 'in_progress' | 'completed' | 'cancelled'
  priority?: number
  due_date?: string
  assigned_to_account_id?: string
  created_at: string
  updated_at: string
}

export interface Task {
  task_id: string
  project_id: string
  title: string
  description?: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  sort_order: number
  due_date?: string
  assigned_to_account_id?: string
  created_at: string
  updated_at: string
}

export interface Conversation {
  conversation_id: string
  person_id: string
  channel_type: 'slack' | 'email' | 'sms' | 'web'
  channel_id?: string
  subject?: string
  status: 'active' | 'archived'
  created_at: string
  updated_at: string
}

export interface Message {
  message_id: string
  conversation_id: string
  sender_type: 'person' | 'agent' | 'staff'
  sender_id?: string
  content: string
  metadata_jsonb?: Record<string, any>
  created_at: string
}

export interface ConversationSummary {
  conversation_id: string
  channel_type: string
  last_message_preview: string
  last_message_at: string
  message_count: number
}

export interface UpcomingDateItem {
  date_item_id: string
  title: string
  date_value: string
  next_occurrence: string
  category_name: string
  category_icon?: string
  days_until: number
  reminder_count: number
}

export interface ActiveProjectSummary {
  project_id: string
  title: string
  status: string
  priority?: number
  due_date?: string
  total_tasks: number
  completed_tasks: number
  completion_percentage: number
}

export interface RecommendationSummary {
  recommendation_id: string
  venue_name?: string
  category: string
  notes?: string
  created_at: string
}

export interface PersonDashboard {
  person: Person
  recent_conversations: ConversationSummary[]
  upcoming_dates: UpcomingDateItem[]
  active_projects: ActiveProjectSummary[]
  recent_recommendations: RecommendationSummary[]
  stats: {
    total_conversations: number
    total_upcoming_dates: number
    total_active_projects: number
    total_recommendations: number
  }
}

// ===========================
// API Methods
// ===========================

// Person API
export const personsApi = {
  list: (orgId: string, personType?: string) =>
    apiClient.get<Person[]>('/persons/', { params: { org_id: orgId, person_type: personType } }),

  get: (personId: string) =>
    apiClient.get<Person>(`/persons/${personId}`),

  create: (data: Partial<Person>) =>
    apiClient.post<Person>('/persons/', data),

  update: (personId: string, data: Partial<Person>) =>
    apiClient.put<Person>(`/persons/${personId}`, data),

  delete: (personId: string) =>
    apiClient.delete(`/persons/${personId}`),
}

// Date Items API
export const dateItemsApi = {
  listByPerson: (personId: string, params?: {
    category_id?: string
    upcoming_only?: boolean
  }) =>
    apiClient.get<DateItem[]>(`/persons/${personId}/date-items`, { params }),

  get: (dateItemId: string) =>
    apiClient.get<DateItem>(`/date-items/${dateItemId}`),

  create: (data: {
    person_id: string
    org_id: string
    category_id: string
    title: string
    date_value: string
    recurrence_rule?: string
    notes?: string
    reminder_rules?: Array<{
      reminder_type: 'lead_time' | 'scheduled'
      lead_time_days?: number
      scheduled_datetime?: string
      channel_type?: string
    }>
  }) =>
    apiClient.post<DateItem>('/date-items', data),

  update: (dateItemId: string, data: Partial<DateItem>) =>
    apiClient.put<DateItem>(`/date-items/${dateItemId}`, data),

  delete: (dateItemId: string) =>
    apiClient.delete(`/date-items/${dateItemId}`),

  getReminders: (dateItemId: string) =>
    apiClient.get<ReminderRule[]>(`/date-items/${dateItemId}/reminders`),
}

// Reminders API
export const remindersApi = {
  list: (params: {
    org_id: string
    person_id?: string
    status_filter?: 'all' | 'pending' | 'sent'
  }) =>
    apiClient.get<ReminderRule[]>('/reminders', { params }),

  get: (reminderId: string) =>
    apiClient.get<ReminderRule>(`/reminders/${reminderId}`),

  create: (data: Partial<ReminderRule>) =>
    apiClient.post<ReminderRule>('/reminders', data),

  update: (reminderId: string, data: Partial<ReminderRule>) =>
    apiClient.put<ReminderRule>(`/reminders/${reminderId}`, data),

  delete: (reminderId: string) =>
    apiClient.delete(`/reminders/${reminderId}`),

  getHistory: (reminderId: string) =>
    apiClient.get(`/reminders/${reminderId}/history`),

  retry: (reminderId: string) =>
    apiClient.post(`/reminders/${reminderId}/retry`),
}

// Date Categories API
export const categoriesApi = {
  list: (orgId: string) =>
    apiClient.get<DateCategory[]>('/date-categories', {
      params: { org_id: orgId }
    }),

  get: (categoryId: string) =>
    apiClient.get<DateCategory>(`/date-categories/${categoryId}`),

  create: (data: {
    org_id: string
    category_name: string
    icon?: string
    color?: string
  }) =>
    apiClient.post<DateCategory>('/date-categories', data),

  update: (categoryId: string, data: Partial<DateCategory>) =>
    apiClient.put<DateCategory>(`/date-categories/${categoryId}`, data),

  delete: (categoryId: string) =>
    apiClient.delete(`/date-categories/${categoryId}`),
}

// Dashboard API
export const dashboardApi = {
  getPersonDashboard: (personId: string) =>
    apiClient.get<PersonDashboard>(`/persons/${personId}/dashboard`),

  getUpcoming: (personId: string, daysAhead: number = 30) =>
    apiClient.get<UpcomingDateItem[]>(`/persons/${personId}/upcoming`, {
      params: { days_ahead: daysAhead }
    }),

  getActivity: (personId: string, limit: number = 50) =>
    apiClient.get(`/persons/${personId}/activity`, {
      params: { limit }
    }),
}

// Project API
export const projectsApi = {
  list: (orgId: string, personId?: string, status?: string) =>
    apiClient.get<Project[]>('/projects/', { params: { org_id: orgId, person_id: personId, status } }),

  get: (projectId: string) =>
    apiClient.get<Project>(`/projects/${projectId}`),

  create: (data: Partial<Project>) =>
    apiClient.post<Project>('/projects/', data),

  update: (projectId: string, data: Partial<Project>) =>
    apiClient.put<Project>(`/projects/${projectId}`, data),

  getTasks: (projectId: string) =>
    apiClient.get<Task[]>(`/projects/${projectId}/tasks`),

  createTask: (projectId: string, data: Partial<Task>) =>
    apiClient.post<Task>(`/projects/${projectId}/tasks`, data),
}

// Conversation API
export const conversationsApi = {
  list: (orgId: string, personId?: string) =>
    apiClient.get<Conversation[]>('/conversations/', { params: { org_id: orgId, person_id: personId } }),

  get: (conversationId: string) =>
    apiClient.get<Conversation>(`/conversations/${conversationId}`),

  getMessages: (conversationId: string) =>
    apiClient.get<Message[]>(`/conversations/${conversationId}/messages`),
}

// Agent API
export const agentsApi = {
  chat: (data: { person_id: string; message: string; conversation_id?: string }) =>
    apiClient.post('/agents/chat', data),

  health: () =>
    apiClient.get('/agents/health'),
}

export default apiClient
