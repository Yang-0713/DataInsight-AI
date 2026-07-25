import { apiClient } from './client'

export interface DatasetSummary {
  id: number
  filename: string
  rows: number
  columns: number
}

export interface ColumnProfile {
  name: string
  data_type: 'numeric' | 'categorical' | 'datetime' | 'boolean'
  pandas_type: string
  missing_count: number
  missing_percentage: number
  unique_count: number
}

export interface DataProfile {
  rows: number
  columns: number
  duplicate_rows: number
  missing_cells: number
  missing_percentage: number
  column_profiles: ColumnProfile[]
}

export interface NumericalStatistic {
  column: string
  count: number
  mean: number | null
  median: number | null
  std: number | null
  min: number | null
  q1: number | null
  q3: number | null
  max: number | null
}

export interface CategoryDistribution {
  value: string
  count: number
  percentage: number
}

export interface CategoricalStatistic {
  column: string
  count: number
  unique: number
  top: string | null
  frequency: number
  distribution: CategoryDistribution[]
}

export interface AnalysisChart {
  id: string
  type: 'histogram' | 'boxplot' | 'bar' | 'heatmap' | 'line'
  title: string
  columns: string[]
  option: Record<string, unknown>
}

export interface EdaPayload {
  dataset: DatasetSummary
  profile: DataProfile
  statistics: {
    numerical: NumericalStatistic[]
    categorical: CategoricalStatistic[]
  }
  visualizations: AnalysisChart[]
}

export interface AnalysisResult {
  id: number
  dataset_id: number
  analysis_type: string
  result_json: EdaPayload
  created_at: string
}

export async function runDatasetAnalysis(datasetId: number): Promise<AnalysisResult> {
  const response = await apiClient.post<AnalysisResult>(
    `/analysis/${datasetId}`,
    undefined,
    { timeout: 120_000 },
  )
  return response.data
}

export async function getAnalysisResult(resultId: number): Promise<AnalysisResult> {
  const response = await apiClient.get<AnalysisResult>(`/results/${resultId}`)
  return response.data
}
