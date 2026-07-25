import { apiClient } from './client'

export interface Dataset {
  id: number
  filename: string
  rows: number
  columns: number
  created_at: string
}

export async function listDatasets(): Promise<Dataset[]> {
  const response = await apiClient.get<Dataset[]>('/datasets')
  return response.data
}

export async function getDataset(datasetId: number): Promise<Dataset> {
  const response = await apiClient.get<Dataset>(`/datasets/${datasetId}`)
  return response.data
}

export async function uploadDataset(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<Dataset> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post<Dataset>('/datasets/upload', formData, {
    timeout: 120_000,
    onUploadProgress: (event) => {
      if (event.total && onProgress) {
        onProgress(Math.round((event.loaded * 100) / event.total))
      }
    },
  })
  return response.data
}

export async function deleteDataset(datasetId: number): Promise<void> {
  await apiClient.delete(`/datasets/${datasetId}`)
}
