import { defineStore } from 'pinia'

import {
  deleteDataset,
  getDataset,
  listDatasets,
  uploadDataset,
  type Dataset,
} from '../api/datasets'

export const useDatasetStore = defineStore('datasets', {
  state: () => ({
    items: [] as Dataset[],
    loading: false,
    uploading: false,
    uploadProgress: 0,
  }),
  getters: {
    count: (state) => state.items.length,
  },
  actions: {
    async load(): Promise<void> {
      this.loading = true
      try {
        this.items = await listDatasets()
      } finally {
        this.loading = false
      }
    },
    async upload(file: File): Promise<Dataset> {
      this.uploading = true
      this.uploadProgress = 0
      try {
        const dataset = await uploadDataset(file, (percent) => {
          this.uploadProgress = percent
        })
        this.items.unshift(dataset)
        return dataset
      } finally {
        this.uploading = false
        this.uploadProgress = 0
      }
    },
    async fetchOne(datasetId: number): Promise<Dataset> {
      return getDataset(datasetId)
    },
    async remove(datasetId: number): Promise<void> {
      await deleteDataset(datasetId)
      this.items = this.items.filter((item) => item.id !== datasetId)
    },
  },
})
