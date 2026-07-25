import { apiClient } from './client'

export interface AIStatus {
  configured: boolean
  provider: string
  model: string
  api_mode: 'responses' | 'chat_completions'
}

export interface AIHistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AIChatResponse {
  result_id: number
  dataset_id: number
  answer: string
  provider: string
  model: string
  created_at: string
}

export interface AIReport {
  id: number
  dataset_id: number
  title: string
  summary: string
  findings: string[]
  possible_problems: string[]
  recommendations: string[]
  download_url: string
  provider: string
  model: string
  created_at: string
}

export async function getAIStatus(): Promise<AIStatus> {
  const response = await apiClient.get<AIStatus>('/ai/status')
  return response.data
}

export async function sendAIMessage(
  datasetId: number,
  message: string,
  history: AIHistoryMessage[],
): Promise<AIChatResponse> {
  const response = await apiClient.post<AIChatResponse>(
    '/ai/chat',
    {
      dataset_id: datasetId,
      message,
      history,
    },
    { timeout: 120_000 },
  )
  return response.data
}

export async function generateAIReport(datasetId: number): Promise<AIReport> {
  const response = await apiClient.post<AIReport>(
    `/reports/${datasetId}`,
    undefined,
    { timeout: 180_000 },
  )
  return response.data
}

export async function listAIReports(): Promise<AIReport[]> {
  const response = await apiClient.get<AIReport[]>('/reports')
  return response.data
}

export async function downloadAIReport(reportId: number): Promise<Blob> {
  const response = await apiClient.get<Blob>(`/reports/${reportId}/download`, {
    responseType: 'blob',
    timeout: 30_000,
  })
  return response.data
}
