import { defineStore } from 'pinia'

import {
  getMachineLearningFeatures,
  runMachineLearning,
  type MachineLearningFeatures,
  type MachineLearningRequest,
  type MachineLearningResult,
} from '../api/machineLearning'

export const useMachineLearningStore = defineStore('machine-learning', {
  state: () => ({
    features: null as MachineLearningFeatures | null,
    current: null as MachineLearningResult | null,
    loadingFeatures: false,
    running: false,
  }),
  actions: {
    async loadFeatures(datasetId: number): Promise<MachineLearningFeatures> {
      this.loadingFeatures = true
      try {
        const features = await getMachineLearningFeatures(datasetId)
        this.features = features
        return features
      } finally {
        this.loadingFeatures = false
      }
    },
    async run(
      datasetId: number,
      request: MachineLearningRequest,
    ): Promise<MachineLearningResult> {
      this.running = true
      try {
        const result = await runMachineLearning(datasetId, request)
        this.current = result
        return result
      } finally {
        this.running = false
      }
    },
    clear(): void {
      this.features = null
      this.current = null
    },
  },
})
