import { apiClient } from './client'

export interface MachineLearningFeatures {
  dataset_id: number
  rows: number
  numeric_features: string[]
  recommended_features: string[]
  max_rows: number
}

export interface MachineLearningRequest {
  features: string[]
  contamination: number
  lof_neighbors: number
}

export interface PredictionSample {
  sample_id: string
  anomaly_score: number
  raw_score: number
  prediction: -1 | 1
  label: 'anomaly' | 'normal'
}

export interface AnomalyResult {
  contamination: number
  anomaly_count: number
  samples: PredictionSample[]
}

export interface MachineLearningPayload {
  dataset: {
    id: number
    filename: string
    rows: number
    columns: number
  }
  preprocessing: {
    features: string[]
    sample_count: number
    missing_values_imputed: number
    imputation: string
    scaling: string
  }
  pca: {
    components: Array<{
      component: string
      loadings: Array<{ feature: string; weight: number }>
    }>
    explained_variance_ratio: number[]
    cumulative_explained_variance: number
    visualization: Array<{
      sample_id: string
      x: number
      y: number
    }>
  }
  isolation_forest: AnomalyResult
  lof: AnomalyResult & { n_neighbors: number }
}

export interface MachineLearningResult {
  id: number
  dataset_id: number
  analysis_type: 'ML'
  result_json: MachineLearningPayload
  created_at: string
}

export async function getMachineLearningFeatures(
  datasetId: number,
): Promise<MachineLearningFeatures> {
  const response = await apiClient.get<MachineLearningFeatures>(
    `/ml/${datasetId}/features`,
  )
  return response.data
}

export async function runMachineLearning(
  datasetId: number,
  request: MachineLearningRequest,
): Promise<MachineLearningResult> {
  const response = await apiClient.post<MachineLearningResult>(
    `/ml/${datasetId}`,
    request,
    { timeout: 180_000 },
  )
  return response.data
}
