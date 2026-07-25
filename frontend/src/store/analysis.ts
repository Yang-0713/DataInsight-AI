import { defineStore } from 'pinia'

import {
  getAnalysisResult,
  runDatasetAnalysis,
  type AnalysisResult,
} from '../api/analysis'

export const useAnalysisStore = defineStore('analysis', {
  state: () => ({
    current: null as AnalysisResult | null,
    running: false,
    loading: false,
  }),
  actions: {
    async run(datasetId: number): Promise<AnalysisResult> {
      this.running = true
      try {
        const result = await runDatasetAnalysis(datasetId)
        this.current = result
        return result
      } finally {
        this.running = false
      }
    },
    async fetch(resultId: number): Promise<AnalysisResult> {
      this.loading = true
      try {
        const result = await getAnalysisResult(resultId)
        this.current = result
        return result
      } finally {
        this.loading = false
      }
    },
    clear(): void {
      this.current = null
    },
  },
})
