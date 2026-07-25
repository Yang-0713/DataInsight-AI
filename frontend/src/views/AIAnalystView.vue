<script setup lang="ts">
import {
  ChatDotRound,
  Download,
  MagicStick,
  Promotion,
  Refresh,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { AIReport } from '../api/ai'
import { useAIStore } from '../store/ai'
import { useDatasetStore } from '../store/datasets'
import { getApiErrorMessage } from '../utils/errors'

const route = useRoute()
const router = useRouter()
const aiStore = useAIStore()
const datasetStore = useDatasetStore()
const selectedDatasetId = ref<number>()
const input = ref('')
const conversationRef = ref<HTMLElement>()

const quickQuestions = [
  '这个数据集最值得关注的三个发现是什么？',
  '数据质量有哪些问题，应该如何处理？',
  '请解释数值字段的分布与潜在异常。',
  '结合机器学习结果，哪些样本值得优先调查？',
]

const currentDataset = computed(() =>
  datasetStore.items.find((item) => item.id === selectedDatasetId.value),
)
const currentReports = computed(() =>
  aiStore.reports.filter(
    (report) => report.dataset_id === selectedDatasetId.value,
  ),
)
const canUseAI = computed(
  () =>
    Boolean(aiStore.status?.configured) &&
    Boolean(selectedDatasetId.value),
)

onMounted(async () => {
  try {
    await Promise.all([
      datasetStore.load(),
      aiStore.loadStatus(),
      aiStore.loadReports(),
    ])
    const routeDatasetId = Number(route.params.datasetId)
    selectedDatasetId.value = datasetStore.items.some(
      (item) => item.id === routeDatasetId,
    )
      ? routeDatasetId
      : datasetStore.items[0]?.id
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, 'AI 分析师工作区加载失败'))
  }
})

watch(selectedDatasetId, async (datasetId, previousId) => {
  if (!datasetId || datasetId === previousId) return
  aiStore.clearConversation()
  await router.replace({
    name: 'ai-analyst',
    params: { datasetId: String(datasetId) },
  })
})

watch(
  () => aiStore.messages.length,
  async () => {
    await nextTick()
    conversationRef.value?.scrollTo({
      top: conversationRef.value.scrollHeight,
      behavior: 'smooth',
    })
  },
)

async function sendMessage(content = input.value): Promise<void> {
  if (!selectedDatasetId.value || !content.trim()) return
  try {
    input.value = ''
    await aiStore.send(selectedDatasetId.value, content)
  } catch (error) {
    input.value = content
    ElMessage.error(getApiErrorMessage(error, 'AI 分析失败，请稍后重试'))
  }
}

async function generateReport(): Promise<void> {
  if (!selectedDatasetId.value) return
  try {
    const report = await aiStore.generateReport(selectedDatasetId.value)
    ElMessage.success('综合报告已生成')
    await downloadReport(report)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '报告生成失败，请稍后重试'))
  }
}

async function downloadReport(report: AIReport): Promise<void> {
  try {
    await aiStore.downloadReport(report)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '报告下载失败'))
  }
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}
</script>

<template>
  <section class="ai-page">
    <div class="ai-heading">
      <div>
        <p class="eyebrow">AI DATA ANALYST</p>
        <h1>与你的数据对话</h1>
        <p>AI 仅接收聚合统计和分析摘要，不会上传原始 CSV 文件。</p>
      </div>
      <el-select
        v-model="selectedDatasetId"
        class="dataset-select"
        placeholder="选择数据集"
        filterable
        :disabled="datasetStore.loading || !datasetStore.count"
      >
        <el-option
          v-for="dataset in datasetStore.items"
          :key="dataset.id"
          :label="dataset.filename"
          :value="dataset.id"
        />
      </el-select>
    </div>

    <el-alert
      v-if="aiStore.status && !aiStore.status.configured"
      class="configuration-alert"
      title="AI 服务尚未配置"
      type="warning"
      :closable="false"
      show-icon
    >
      <template #default>
        在 backend/.env 中设置 DATAINSIGHT_OPENAI_API_KEY 后重启后端。
      </template>
    </el-alert>

    <el-empty
      v-if="!datasetStore.loading && !datasetStore.count"
      description="请先上传一个 CSV 数据集"
    >
      <RouterLink to="/datasets">
        <el-button type="primary">前往数据集管理</el-button>
      </RouterLink>
    </el-empty>

    <div v-else class="analyst-layout">
      <aside class="context-panel">
        <div class="panel-title">
          <span><el-icon><MagicStick /></el-icon></span>
          <div>
            <small>当前上下文</small>
            <strong>{{ currentDataset?.filename || '请选择数据集' }}</strong>
          </div>
        </div>

        <div v-if="currentDataset" class="dataset-metrics">
          <div><span>记录</span><strong>{{ currentDataset.rows }}</strong></div>
          <div><span>字段</span><strong>{{ currentDataset.columns }}</strong></div>
        </div>

        <div class="service-status">
          <span :class="{ online: aiStore.status?.configured }"></span>
          <div>
            <strong>
              {{ aiStore.status?.configured ? 'AI 已连接' : '等待配置' }}
            </strong>
            <small>{{ aiStore.status?.model || '—' }}</small>
          </div>
        </div>

        <el-button
          class="report-button"
          type="primary"
          plain
          :icon="MagicStick"
          :loading="aiStore.generatingReport"
          :disabled="!canUseAI"
          @click="generateReport"
        >
          生成综合 HTML 报告
        </el-button>

        <div class="report-list">
          <div class="report-heading">
            <span>历史报告</span>
            <el-icon
              :class="{ spinning: aiStore.loadingReports }"
              @click="aiStore.loadReports"
            >
              <Refresh />
            </el-icon>
          </div>
          <p v-if="!currentReports.length">还没有生成报告</p>
          <button
            v-for="report in currentReports"
            :key="report.id"
            type="button"
            @click="downloadReport(report)"
          >
            <span>
              <strong>{{ report.title }}</strong>
              <small>{{ formatDate(report.created_at) }}</small>
            </span>
            <el-icon><Download /></el-icon>
          </button>
        </div>
      </aside>

      <div class="chat-panel">
        <div class="chat-toolbar">
          <div>
            <span><el-icon><ChatDotRound /></el-icon></span>
            <div>
              <strong>DataInsight 分析师</strong>
              <small>基于最新 EDA 与机器学习结果</small>
            </div>
          </div>
          <el-button
            text
            :icon="Refresh"
            :disabled="!aiStore.messages.length"
            @click="aiStore.clearConversation"
          >
            新对话
          </el-button>
        </div>

        <div ref="conversationRef" class="conversation">
          <div v-if="!aiStore.messages.length" class="welcome-message">
            <span><el-icon :size="28"><MagicStick /></el-icon></span>
            <h2>想从数据中了解什么？</h2>
            <p>选择一个问题开始，系统会先生成或复用 EDA 摘要，再交给 AI 分析。</p>
            <div class="quick-grid">
              <button
                v-for="question in quickQuestions"
                :key="question"
                type="button"
                :disabled="!canUseAI"
                @click="sendMessage(question)"
              >
                {{ question }}
              </button>
            </div>
          </div>

          <div
            v-for="(message, index) in aiStore.messages"
            :key="`${message.role}-${index}`"
            class="message-row"
            :class="message.role"
          >
            <div class="message-avatar">
              {{ message.role === 'assistant' ? 'AI' : '我' }}
            </div>
            <div class="message-content">{{ message.content }}</div>
          </div>

          <div v-if="aiStore.sending" class="message-row assistant">
            <div class="message-avatar">AI</div>
            <div class="message-content typing">
              <span></span><span></span><span></span>
              正在分析统计摘要
            </div>
          </div>
        </div>

        <form class="composer" @submit.prevent="sendMessage()">
          <el-input
            v-model="input"
            type="textarea"
            :rows="2"
            resize="none"
            maxlength="4000"
            placeholder="例如：缺失值会怎样影响当前结论？"
            :disabled="!canUseAI || aiStore.sending"
            @keydown.ctrl.enter.prevent="sendMessage()"
          />
          <el-button
            type="primary"
            :icon="Promotion"
            native-type="submit"
            :loading="aiStore.sending"
            :disabled="!canUseAI || !input.trim()"
          >
            发送
          </el-button>
        </form>
        <p class="composer-hint">Ctrl + Enter 发送 · AI 结论可能有误，重要决策请复核原始数据</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ai-page {
  width: min(1180px, calc(100% - 40px));
  padding: 52px 0 80px;
  margin: 0 auto;
}

.ai-heading {
  display: flex;
  gap: 30px;
  align-items: end;
  justify-content: space-between;
}

.eyebrow {
  margin: 0 0 10px;
  color: #5b5cf0;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.15em;
}

.ai-heading h1 {
  margin: 0;
  font-size: clamp(2.3rem, 5vw, 4rem);
  letter-spacing: -0.055em;
}

.ai-heading p:last-child {
  margin: 13px 0 0;
  color: #727b91;
}

.dataset-select {
  width: 280px;
}

.configuration-alert {
  margin-top: 24px;
}

.analyst-layout {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 20px;
  align-items: stretch;
  margin-top: 34px;
}

.context-panel,
.chat-panel {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(30, 42, 76, 0.08);
  border-radius: 21px;
  box-shadow: 0 16px 40px rgba(31, 42, 76, 0.07);
}

.context-panel {
  padding: 22px;
}

.panel-title,
.chat-toolbar > div,
.service-status {
  display: flex;
  gap: 12px;
  align-items: center;
}

.panel-title > span,
.chat-toolbar > div > span {
  display: grid;
  flex: 0 0 auto;
  width: 40px;
  height: 40px;
  color: #5758d8;
  background: #eeeeff;
  border-radius: 12px;
  place-items: center;
}

.panel-title div,
.chat-toolbar > div > div,
.service-status div {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.panel-title small,
.chat-toolbar small,
.service-status small {
  color: #9197a9;
  font-size: 0.69rem;
}

.panel-title strong {
  overflow: hidden;
  font-size: 0.82rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dataset-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 22px;
}

.dataset-metrics div {
  display: grid;
  gap: 6px;
  padding: 14px;
  background: #f7f8fc;
  border-radius: 11px;
}

.dataset-metrics span {
  color: #9298a9;
  font-size: 0.68rem;
}

.dataset-metrics strong {
  font-size: 1.15rem;
}

.service-status {
  padding: 17px 0;
  margin-top: 14px;
  border-top: 1px solid #eceef5;
  border-bottom: 1px solid #eceef5;
}

.service-status > span {
  width: 9px;
  height: 9px;
  background: #e6a23c;
  border-radius: 99px;
  box-shadow: 0 0 0 4px rgba(230, 162, 60, 0.12);
}

.service-status > span.online {
  background: #2fc49a;
  box-shadow: 0 0 0 4px rgba(47, 196, 154, 0.12);
}

.report-button {
  width: 100%;
  margin-top: 18px;
}

.report-list {
  margin-top: 25px;
}

.report-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  color: #80879a;
  font-size: 0.72rem;
  font-weight: 750;
}

.report-heading .el-icon {
  cursor: pointer;
}

.spinning {
  animation: spin 0.8s linear infinite;
}

.report-list > p {
  color: #a0a5b4;
  font-size: 0.72rem;
}

.report-list button {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 11px 0;
  color: #535c73;
  text-align: left;
  cursor: pointer;
  background: transparent;
  border: 0;
  border-bottom: 1px solid #f0f1f6;
}

.report-list button > span {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.report-list button strong {
  overflow: hidden;
  font-size: 0.72rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.report-list button small {
  color: #a1a6b5;
  font-size: 0.65rem;
}

.chat-panel {
  display: grid;
  grid-template-rows: auto minmax(430px, 1fr) auto auto;
  min-height: 650px;
  overflow: hidden;
}

.chat-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid #eceef5;
}

.chat-toolbar strong {
  font-size: 0.84rem;
}

.conversation {
  max-height: 570px;
  padding: 28px;
  overflow-y: auto;
}

.welcome-message {
  max-width: 620px;
  margin: 45px auto 0;
  text-align: center;
}

.welcome-message > span {
  display: grid;
  width: 58px;
  height: 58px;
  margin: auto;
  color: white;
  background: linear-gradient(145deg, #7779ff, #4b4cd3);
  border-radius: 18px;
  place-items: center;
}

.welcome-message h2 {
  margin: 19px 0 8px;
}

.welcome-message p {
  margin: 0;
  color: #81889c;
  font-size: 0.82rem;
}

.quick-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 25px;
}

.quick-grid button {
  padding: 14px;
  color: #606980;
  font: inherit;
  font-size: 0.75rem;
  line-height: 1.45;
  text-align: left;
  cursor: pointer;
  background: #f8f9fd;
  border: 1px solid #e5e7f1;
  border-radius: 12px;
}

.quick-grid button:hover:not(:disabled) {
  color: #5051ce;
  border-color: #c8c9f2;
}

.quick-grid button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.message-row {
  display: flex;
  gap: 11px;
  align-items: flex-start;
  margin-bottom: 20px;
}

.message-row.user {
  flex-direction: row-reverse;
}

.message-avatar {
  display: grid;
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  color: #5556d9;
  font-size: 0.7rem;
  font-weight: 800;
  background: #eeeeff;
  border-radius: 10px;
  place-items: center;
}

.user .message-avatar {
  color: white;
  background: #5b5cf0;
}

.message-content {
  max-width: 78%;
  padding: 13px 15px;
  color: #4f5870;
  font-size: 0.84rem;
  line-height: 1.72;
  white-space: pre-wrap;
  background: #f6f7fb;
  border-radius: 4px 14px 14px;
}

.user .message-content {
  color: white;
  background: #5b5cf0;
  border-radius: 14px 4px 14px 14px;
}

.typing {
  display: flex;
  gap: 5px;
  align-items: center;
  color: #8990a4;
}

.typing span {
  width: 5px;
  height: 5px;
  background: #7779dd;
  border-radius: 99px;
  animation: pulse 1.2s infinite;
}

.typing span:nth-child(2) {
  animation-delay: 0.15s;
}

.typing span:nth-child(3) {
  margin-right: 5px;
  animation-delay: 0.3s;
}

.composer {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: end;
  padding: 16px 20px 8px;
  border-top: 1px solid #eceef5;
}

.composer .el-button {
  height: 54px;
}

.composer-hint {
  margin: 0;
  padding: 0 20px 15px;
  color: #a0a5b4;
  font-size: 0.66rem;
  text-align: center;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  50% { opacity: 0.25; transform: translateY(-2px); }
}

@media (max-width: 880px) {
  .analyst-layout {
    grid-template-columns: 1fr;
  }

  .chat-panel {
    min-height: 620px;
  }
}

@media (max-width: 640px) {
  .ai-page {
    width: min(100% - 28px, 1180px);
    padding-top: 34px;
  }

  .ai-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .dataset-select {
    width: 100%;
  }

  .quick-grid {
    grid-template-columns: 1fr;
  }

  .conversation {
    padding: 20px 14px;
  }

  .message-content {
    max-width: 85%;
  }
}
</style>
