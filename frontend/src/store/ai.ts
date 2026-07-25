import { defineStore } from 'pinia'

import {
  downloadAIReport,
  generateAIReport,
  getAIStatus,
  listAIReports,
  sendAIMessage,
  type AIHistoryMessage,
  type AIReport,
  type AIStatus,
} from '../api/ai'

export const useAIStore = defineStore('ai-analyst', {
  state: () => ({
    status: null as AIStatus | null,
    messages: [] as AIHistoryMessage[],
    reports: [] as AIReport[],
    loadingStatus: false,
    sending: false,
    generatingReport: false,
    loadingReports: false,
  }),
  actions: {
    async loadStatus(): Promise<AIStatus> {
      this.loadingStatus = true
      try {
        this.status = await getAIStatus()
        return this.status
      } finally {
        this.loadingStatus = false
      }
    },
    async send(datasetId: number, content: string): Promise<void> {
      const message = content.trim()
      if (!message || this.sending) return
      const history = this.messages.slice(-12)
      this.messages.push({ role: 'user', content: message })
      this.sending = true
      try {
        const result = await sendAIMessage(datasetId, message, history)
        this.messages.push({ role: 'assistant', content: result.answer })
      } catch (error) {
        this.messages.pop()
        throw error
      } finally {
        this.sending = false
      }
    },
    async loadReports(): Promise<void> {
      this.loadingReports = true
      try {
        this.reports = await listAIReports()
      } finally {
        this.loadingReports = false
      }
    },
    async generateReport(datasetId: number): Promise<AIReport> {
      this.generatingReport = true
      try {
        const report = await generateAIReport(datasetId)
        this.reports.unshift(report)
        return report
      } finally {
        this.generatingReport = false
      }
    },
    async downloadReport(report: AIReport): Promise<void> {
      const blob = await downloadAIReport(report.id)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${report.title}.html`
      link.click()
      URL.revokeObjectURL(url)
    },
    clearConversation(): void {
      this.messages = []
    },
  },
})
