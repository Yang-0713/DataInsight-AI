<script setup lang="ts">
import {
  DataAnalysis,
  DataLine,
  Refresh,
  Select,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { ColumnProfile } from '../api/analysis'
import EChart from '../components/EChart.vue'
import { useAnalysisStore } from '../store/analysis'
import { useDatasetStore } from '../store/datasets'
import { getApiErrorMessage } from '../utils/errors'

const route = useRoute()
const router = useRouter()
const datasetStore = useDatasetStore()
const analysisStore = useAnalysisStore()
const selectedDatasetId = ref<number>()

const result = computed(() => analysisStore.current?.result_json ?? null)
const hasDataset = computed(() => datasetStore.items.length > 0)
const numericalStatistics = computed(
  () => result.value?.statistics.numerical ?? [],
)
const categoricalStatistics = computed(
  () => result.value?.statistics.categorical ?? [],
)

onMounted(async () => {
  try {
    await datasetStore.load()
    const routeDatasetId = Number(route.params.datasetId)
    selectedDatasetId.value = datasetStore.items.some(
      (item) => item.id === routeDatasetId,
    )
      ? routeDatasetId
      : datasetStore.items[0]?.id
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '数据集加载失败'))
  }
})

watch(selectedDatasetId, async (datasetId, previousId) => {
  if (!datasetId || datasetId === previousId) return
  analysisStore.clear()
  await router.replace({
    name: 'analysis',
    params: { datasetId: String(datasetId) },
  })
})

async function startAnalysis(): Promise<void> {
  if (!selectedDatasetId.value) {
    ElMessage.warning('请先选择一个数据集')
    return
  }
  try {
    await analysisStore.run(selectedDatasetId.value)
    ElMessage.success('自动 EDA 已完成')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '分析失败，请稍后重试'))
  }
}

function formatNumber(value: number | null, digits = 2): string {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('zh-CN', {
    maximumFractionDigits: digits,
  }).format(value)
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function typeLabel(type: ColumnProfile['data_type']): string {
  return {
    numeric: '数值',
    categorical: '分类',
    datetime: '日期',
    boolean: '布尔',
  }[type]
}
</script>

<template>
  <section class="analysis-page">
    <div class="analysis-heading">
      <div>
        <p class="eyebrow">AUTOMATIC EDA</p>
        <h1>自动探索数据</h1>
        <p>一次生成数据画像、统计摘要和可交互图表。</p>
      </div>
      <div class="analysis-controls">
        <el-select
          v-model="selectedDatasetId"
          placeholder="选择数据集"
          filterable
          :disabled="datasetStore.loading || !hasDataset"
        >
          <el-option
            v-for="dataset in datasetStore.items"
            :key="dataset.id"
            :label="dataset.filename"
            :value="dataset.id"
          />
        </el-select>
        <el-button
          type="primary"
          size="large"
          :icon="analysisStore.current ? Refresh : DataAnalysis"
          :loading="analysisStore.running"
          :disabled="!selectedDatasetId"
          @click="startAnalysis"
        >
          {{ analysisStore.current ? '重新分析' : '开始分析' }}
        </el-button>
      </div>
    </div>

    <el-empty
      v-if="!datasetStore.loading && !hasDataset"
      class="empty-state"
      description="请先上传 CSV 数据集"
    >
      <RouterLink to="/datasets">
        <el-button type="primary">前往数据集管理</el-button>
      </RouterLink>
    </el-empty>

    <div
      v-else-if="!result"
      v-loading="analysisStore.running || datasetStore.loading"
      class="start-panel"
    >
      <span class="start-icon"><el-icon :size="30"><DataLine /></el-icon></span>
      <h2>让数据先介绍自己</h2>
      <p>
        系统会识别字段类型、缺失值、重复记录和分布特征，并根据数据结构自动选择合适图表。
      </p>
      <div class="capability-list">
        <span><el-icon><Select /></el-icon>字段画像</span>
        <span><el-icon><Select /></el-icon>描述性统计</span>
        <span><el-icon><Select /></el-icon>ECharts 图表</span>
      </div>
    </div>

    <template v-else>
      <div class="result-meta">
        <div>
          <span>分析结果 #{{ analysisStore.current?.id }}</span>
          <strong>{{ result.dataset.filename }}</strong>
        </div>
        <small>生成于 {{ formatDate(analysisStore.current!.created_at) }}</small>
      </div>

      <div class="metric-grid">
        <article>
          <span>记录数</span>
          <strong>{{ formatNumber(result.profile.rows, 0) }}</strong>
          <small>共 {{ result.profile.columns }} 个字段</small>
        </article>
        <article>
          <span>缺失单元格</span>
          <strong>{{ formatNumber(result.profile.missing_cells, 0) }}</strong>
          <small>占全部数据 {{ result.profile.missing_percentage }}%</small>
        </article>
        <article>
          <span>重复记录</span>
          <strong>{{ formatNumber(result.profile.duplicate_rows, 0) }}</strong>
          <small>建议在建模前检查</small>
        </article>
        <article>
          <span>自动图表</span>
          <strong>{{ result.visualizations.length }}</strong>
          <small>根据字段类型生成</small>
        </article>
      </div>

      <section class="result-section">
        <div class="section-heading">
          <div>
            <span>DATA PROFILE</span>
            <h2>字段画像</h2>
          </div>
          <p>查看类型、完整性与唯一值规模。</p>
        </div>
        <div class="table-card">
          <el-table :data="result.profile.column_profiles">
            <el-table-column min-width="180" prop="name" label="字段" />
            <el-table-column width="110" label="识别类型">
              <template #default="{ row }">
                <el-tag effect="plain">{{ typeLabel(row.data_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column width="130" prop="pandas_type" label="存储类型" />
            <el-table-column width="130" label="缺失值">
              <template #default="{ row }">
                {{ row.missing_count }}（{{ row.missing_percentage }}%）
              </template>
            </el-table-column>
            <el-table-column width="120" prop="unique_count" label="唯一值" />
          </el-table>
        </div>
      </section>

      <section class="result-section">
        <div class="section-heading">
          <div>
            <span>STATISTICS</span>
            <h2>描述性统计</h2>
          </div>
          <p>数值字段与分类字段分别计算。</p>
        </div>
        <div class="table-card statistic-card">
          <el-tabs>
            <el-tab-pane :label="`数值字段 ${numericalStatistics.length}`">
              <el-empty
                v-if="numericalStatistics.length === 0"
                description="没有可统计的数值字段"
              />
              <el-table v-else :data="numericalStatistics">
                <el-table-column min-width="150" prop="column" label="字段" fixed />
                <el-table-column width="100" label="有效数">
                  <template #default="{ row }">{{ formatNumber(row.count, 0) }}</template>
                </el-table-column>
                <el-table-column width="110" label="平均值">
                  <template #default="{ row }">{{ formatNumber(row.mean) }}</template>
                </el-table-column>
                <el-table-column width="110" label="中位数">
                  <template #default="{ row }">{{ formatNumber(row.median) }}</template>
                </el-table-column>
                <el-table-column width="110" label="标准差">
                  <template #default="{ row }">{{ formatNumber(row.std) }}</template>
                </el-table-column>
                <el-table-column width="100" label="最小值">
                  <template #default="{ row }">{{ formatNumber(row.min) }}</template>
                </el-table-column>
                <el-table-column width="100" label="Q1">
                  <template #default="{ row }">{{ formatNumber(row.q1) }}</template>
                </el-table-column>
                <el-table-column width="100" label="Q3">
                  <template #default="{ row }">{{ formatNumber(row.q3) }}</template>
                </el-table-column>
                <el-table-column width="100" label="最大值">
                  <template #default="{ row }">{{ formatNumber(row.max) }}</template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane :label="`分类字段 ${categoricalStatistics.length}`">
              <el-empty
                v-if="categoricalStatistics.length === 0"
                description="没有可统计的分类字段"
              />
              <el-table v-else :data="categoricalStatistics">
                <el-table-column min-width="170" prop="column" label="字段" />
                <el-table-column width="120" prop="count" label="有效数" />
                <el-table-column width="120" prop="unique" label="类别数" />
                <el-table-column min-width="170" prop="top" label="最高频类别" />
                <el-table-column width="120" prop="frequency" label="出现次数" />
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </div>
      </section>

      <section class="result-section">
        <div class="section-heading">
          <div>
            <span>VISUALIZATIONS</span>
            <h2>自动可视化</h2>
          </div>
          <p>{{ result.visualizations.length }} 张图表，可缩放和查看数据点。</p>
        </div>
        <el-empty
          v-if="result.visualizations.length === 0"
          class="table-card"
          description="当前数据没有适合自动生成的图表"
        />
        <div v-else class="chart-grid">
          <article
            v-for="chart in result.visualizations"
            :key="chart.id"
            class="chart-card"
          >
            <div>
              <span>{{ chart.type.toUpperCase() }}</span>
              <h3>{{ chart.title }}</h3>
            </div>
            <EChart :option="chart.option" :title="chart.title" />
          </article>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.analysis-page {
  width: min(1180px, calc(100% - 40px));
  padding: 54px 0 90px;
  margin: 0 auto;
}

.analysis-heading {
  display: flex;
  gap: 40px;
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

.analysis-heading h1 {
  margin: 0;
  color: #17213a;
  font-size: clamp(2.4rem, 5vw, 4rem);
  letter-spacing: -0.055em;
}

.analysis-heading > div:first-child > p:last-child {
  margin: 14px 0 0;
  color: #727b91;
}

.analysis-controls {
  display: flex;
  gap: 10px;
  align-items: center;
  min-width: min(100%, 430px);
}

.analysis-controls .el-select {
  flex: 1;
}

.empty-state,
.start-panel,
.table-card,
.chart-card {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(30, 42, 76, 0.08);
  border-radius: 20px;
  box-shadow: 0 16px 40px rgba(31, 42, 76, 0.06);
}

.empty-state,
.start-panel {
  min-height: 360px;
  margin-top: 46px;
}

.start-panel {
  display: flex;
  align-items: center;
  flex-direction: column;
  justify-content: center;
  padding: 50px 24px;
  text-align: center;
}

.start-icon {
  display: grid;
  width: 64px;
  height: 64px;
  color: #5556d9;
  background: #eeeeff;
  border-radius: 19px;
  place-items: center;
}

.start-panel h2 {
  margin: 22px 0 10px;
  font-size: 1.5rem;
}

.start-panel p {
  max-width: 570px;
  margin: 0;
  color: #737c91;
  line-height: 1.7;
}

.capability-list {
  display: flex;
  gap: 10px;
  margin-top: 25px;
}

.capability-list span {
  display: inline-flex;
  gap: 5px;
  align-items: center;
  padding: 8px 11px;
  color: #586178;
  font-size: 0.76rem;
  background: #f5f6fb;
  border-radius: 9px;
}

.result-meta {
  display: flex;
  align-items: end;
  justify-content: space-between;
  padding: 28px 30px;
  margin-top: 44px;
  color: white;
  background: linear-gradient(120deg, #292d64, #5557cb);
  border-radius: 20px;
}

.result-meta div {
  display: grid;
  gap: 7px;
}

.result-meta span,
.result-meta small {
  color: #cecfff;
  font-size: 0.74rem;
}

.result-meta strong {
  font-size: 1.2rem;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-top: 16px;
}

.metric-grid article {
  display: grid;
  gap: 7px;
  padding: 22px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(30, 42, 76, 0.08);
  border-radius: 17px;
}

.metric-grid span,
.metric-grid small {
  color: #8a91a5;
  font-size: 0.72rem;
}

.metric-grid strong {
  color: #242d49;
  font-size: 1.75rem;
}

.result-section {
  margin-top: 56px;
}

.section-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  margin-bottom: 18px;
}

.section-heading span,
.chart-card > div span {
  color: #5b5cf0;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.section-heading h2 {
  margin: 6px 0 0;
  font-size: 1.55rem;
}

.section-heading p {
  margin: 0;
  color: #858da2;
  font-size: 0.8rem;
}

.table-card {
  overflow: hidden;
  padding: 8px;
}

.statistic-card {
  padding: 12px 20px 20px;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.chart-card {
  min-width: 0;
  padding: 22px 20px 14px;
}

.chart-card > div h3 {
  margin: 5px 0 3px;
  color: #2a334c;
  font-size: 1rem;
}

@media (max-width: 900px) {
  .analysis-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .analysis-controls {
    width: 100%;
  }

  .metric-grid,
  .chart-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .analysis-page {
    width: min(100% - 28px, 1180px);
    padding-top: 36px;
  }

  .analysis-controls,
  .capability-list,
  .section-heading,
  .result-meta {
    align-items: stretch;
    flex-direction: column;
  }

  .metric-grid,
  .chart-grid {
    grid-template-columns: 1fr;
  }

  .section-heading {
    gap: 8px;
  }
}
</style>
