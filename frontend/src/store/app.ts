import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    projectName: 'DataInsight AI',
    phase: 2,
  }),
})
