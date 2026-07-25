<script setup lang="ts">
import {
  Cpu,
  DataLine,
  Refresh,
  Select,
  Warning,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import EChart from '../components/EChart.vue'
import { useDatasetStore } from '../store/datasets'
import { useMachineLearningStore } from '../store/machineLearning'
import { getApiErrorMessage } from '../utils/errors'

const route = useRoute()
const router = useRouter()
const datasetStore = useDatasetStore()
const mlStore = useMachineLearningStore()
const selectedDatasetId = ref<number>()
const selectedFeatures = ref<string[]>([])
const parameters = reactive({
  contamination: 0.05,
  lofNeighbors: 20,
})

const result = computed(() => mlStore.current?.result_json ?? null)
const hasDataset = computed(() => datasetStore.items.length > 0)
const canRun = computed(
  () =>
    Boolean(selectedDatasetId.value) &&
    selectedFeatures.value.length >= 2 &&
    !mlStore.running,
)
const rowLimitExceeded = computed(
  () =>
    Boolean(mlStore.features) &&
    mlStore.features!.rows > mlStore.features!.max_rows,
)

const predictionRows = computed(() => {
  if (!result.value) return []
  const lofById = new Map(
    result.value.lof.samples.map((sample) => [sample.sample_id, sample]),
  )
  return result.value.isolation_forest.samples
    .map((sample) => {
      const lof = lofById.get(sample.sample_id)
      return {
        sample_id: sample.sample_id,
        if_score: sample.anomaly_score,
        if_label: sample.label,
        lof_score: lof?.anomaly_score ?? 0,
        lof_label: lof?.label ?? 'normal',
        is_anomaly: sample.label === 'anomaly' || lof?.label === 'anomaly',
      }
    })
    .sort(
      (left, right) =>
        Math.max(right.if_score, right.lof_score) -
        Math.max(left.if_score, left.lof_score),
    )
})

const pcaOption = computed<Record<string, unknown>>(() => {
  if (!result.value) return {}
  const labels = new Map(
    result.value.isolation_forest.samples.map((sample) => [
      sample.sample_id,
      sample.label,
    ]),
  )
  const normal: Array<[number, number, string]> = []
  const anomaly: Array<[number, number, string]> = []
  for (const point of result.value.pca.visualization) {
    const target = labels.get(point.sample_id) === 'anomaly' ? anomaly : normal
    target.push([point.x, point.y, point.sample_id])
  }
  const ratios = result.value.pca.explained_variance_ratio
  return {
    grid: { left: 58, right: 24, top: 42, bottom: 48 },
    tooltip: {
      trigger: 'item',
      formatter: (params: { data: [number, number, string] }) =>
        `${params.data[2]}<br/>PC1: ${params.data[0]}<br/>PC2: ${params.data[1]}`,
    },
    legend: { data: ['正常样本', '异常样本'] },
    xAxis: {
      type: 'value',
      name: `PC1 (${formatPercent(ratios[0] ?? 0)})`,
      scale: true,
    },
    yAxis: {
      type: 'value',
      name: `PC2 (${formatPercent(ratios[1] ?? 0)})`,
      scale: true,
    },
    series: [
      {
        name: '正常样本',
        type: 'scatter',
        data: normal,
        symbolSize: 10,
        itemStyle: { color: '#5b5cf0', opacity: 0.72 },
      },
      {
        name: '异常样本',
        type: 'scatter',
        data: anomaly,
        symbolSize: 15,
        itemStyle: { color: '#ef665d', borderColor: '#fff', borderWidth: 2 },
      },
    ],
  }
})

const scoreOption = computed<Record<string, unknown>>(() => {
  const rows = predictionRows.value.slice(0, 20).reverse()
  return {
    grid: { left: 88, right: 24, top: 38, bottom: 36 },
    tooltip: { trigger: 'axis' },
    legend: { data: ['Isolation Forest', 'LOF'] },
    xAxis: { type: 'value', min: 0, max: 1, name: '异常分数' },
    yAxis: {
      type: 'category',
      data: rows.map((row) => row.sample_id),
      axisLabel: { width: 70, overflow: 'truncate' },
    },
    series: [
      {
        name: 'Isolation Forest',
        type: 'bar',
        data: rows.map((row) => row.if_score),
        itemStyle: { color: '#5b5cf0' },
      },
      {
        name: 'LOF',
        type: 'bar',
        data: rows.map((row) => row.lof_score),
        itemStyle: { color: '#2fc49a' },
      },
    ],
  }
})

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
  mlStore.clear()
  selectedFeatures.value = []
  await router.replace({
    name: 'machine-learning',
    params: { datasetId: String(datasetId) },
  })
  try {
    const features = await mlStore.loadFeatures(datasetId)
    selectedFeatures.value = [...features.recommended_features]
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '数值字段识别失败'))
  }
})

async function startAnalysis(): Promise<void> {
  if (!selectedDatasetId.value || selectedFeatures.value.length < 2) {
    ElMessage.warning('请至少选择两个数值字段')
    return
  }
  try {
    await mlStore.run(selectedDatasetId.value, {
      features: selectedFeatures.value,
      contamination: parameters.contamination,
      lof_neighbors: parameters.lofNeighbors,
    })
    ElMessage.success('机器学习分析已完成')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '机器学习分析失败'))
  }
}

function formatNumber(value: number, digits = 3): string {
  return new Intl.NumberFormat('zh-CN', {
    maximumFractionDigits: digits,
  }).format(value)
}

function formatPercent(value: number): string {
  return `${formatNumber(value * 100, 1)}%`
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
</script>

<template>
  <section class="ml-page">
    <div class="ml-heading">
      <div>
        <p class="eyebrow">MACHINE LEARNING LAB</p>
        <h1>发现数据中的异常</h1>
        <p>通过降维和双重异常检测，定位值得进一步调查的样本。</p>
      </div>
      <div class="dataset-control">
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
      </div>
    </div>

    <el-empty
      v-if="!datasetStore.loading && !hasDataset"
      class="empty-state"
      description="请先上传包含数值字段的 CSV 数据集"
    >
      <RouterLink to="/datasets">
        <el-button type="primary">前往数据集管理</el-button>
      </RouterLink>
    </el-empty>

    <div v-else class="workspace-grid">
      <aside v-loading="mlStore.loadingFeatures" class="settings-panel">
        <div class="settings-title">
          <span><el-icon :size="21"><Cpu /></el-icon></span>
          <div>
            <h2>分析配置</h2>
            <p>选择参与建模的数值字段</p>
          </div>
        </div>

        <label>特征字段</label>
        <el-select
          v-model="selectedFeatures"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="至少选择两个字段"
        >
          <el-option
            v-for="feature in mlStore.features?.numeric_features ?? []"
            :key="feature"
            :label="feature"
            :value="feature"
          />
        </el-select>
        <small class="field-help">
          已选择 {{ selectedFeatures.length }} 个字段，系统会自动补全缺失值并标准化。
        </small>

        <label>预计异常比例</label>
        <div class="slider-row">
          <el-slider
            v-model="parameters.contamination"
            :min="0.01"
            :max="0.3"
            :step="0.01"
          />
          <strong>{{ formatPercent(parameters.contamination) }}</strong>
        </div>

        <label>LOF 邻居数</label>
        <el-input-number
          v-model="parameters.lofNeighbors"
          :min="2"
          :max="200"
          controls-position="right"
        />

        <el-alert
          v-if="rowLimitExceeded"
          :title="`当前数据有 ${mlStore.features?.rows} 行，超过 ${mlStore.features?.max_rows} 行限制。`"
          type="warning"
          :closable="false"
          show-icon
        />

        <el-button
          class="run-button"
          type="primary"
          size="large"
          :icon="mlStore.current ? Refresh : Cpu"
          :loading="mlStore.running"
          :disabled="!canRun || rowLimitExceeded"
          @click="startAnalysis"
        >
          {{ mlStore.current ? '重新运行' : '运行三种算法' }}
        </el-button>
      </aside>

      <main
        v-if="!result"
        v-loading="mlStore.running"
        class="intro-panel"
      >
        <span class="intro-icon"><el-icon :size="31"><DataLine /></el-icon></span>
        <h2>从多维数据中寻找信号</h2>
        <p>
          PCA 展示样本在二维空间中的结构，Isolation Forest 发现全局异常，LOF
          识别局部密度异常。
        </p>
        <div class="algorithm-list">
          <div>
            <span>01</span>
            <strong>PCA</strong>
            <small>降维与解释方差</small>
          </div>
          <div>
            <span>02</span>
            <strong>Isolation Forest</strong>
            <small>全局孤立程度</small>
          </div>
          <div>
            <span>03</span>
            <strong>LOF</strong>
            <small>局部密度偏离</small>
          </div>
        </div>
      </main>

      <main v-else class="result-workspace">
        <div class="result-banner">
          <div>
            <span>ML RESULT #{{ mlStore.current?.id }}</span>
            <strong>{{ result.dataset.filename }}</strong>
          </div>
          <small>{{ formatDate(mlStore.current!.created_at) }}</small>
        </div>

        <div class="metric-grid">
          <article>
            <span>参与样本</span>
            <strong>{{ result.preprocessing.sample_count }}</strong>
            <small>{{ result.preprocessing.features.length }} 个特征</small>
          </article>
          <article>
            <span>PCA 累计解释</span>
            <strong>{{ formatPercent(result.pca.cumulative_explained_variance) }}</strong>
            <small>前两个主成分</small>
          </article>
          <article>
            <span>Isolation Forest</span>
            <strong>{{ result.isolation_forest.anomaly_count }}</strong>
            <small>个异常样本</small>
          </article>
          <article>
            <span>LOF</span>
            <strong>{{ result.lof.anomaly_count }}</strong>
            <small>{{ result.lof.n_neighbors }} 个邻居</small>
          </article>
        </div>

        <div class="chart-grid">
          <article class="chart-card">
            <div class="card-heading">
              <div>
                <span>PCA PROJECTION</span>
                <h3>二维样本投影</h3>
              </div>
              <small>红色为 Isolation Forest 异常</small>
            </div>
            <EChart :option="pcaOption" title="PCA 二维样本投影" />
          </article>
          <article class="chart-card">
            <div class="card-heading">
              <div>
                <span>ANOMALY SCORE</span>
                <h3>高风险样本对比</h3>
              </div>
              <small>展示最高的 20 条</small>
            </div>
            <EChart :option="scoreOption" title="异常分数对比" />
          </article>
        </div>

        <section class="result-section">
          <div class="section-heading">
            <div>
              <span>COMPONENT LOADINGS</span>
              <h2>主成分载荷</h2>
            </div>
            <p>权重绝对值越大，对该主成分影响越明显。</p>
          </div>
          <div class="loading-grid">
            <article
              v-for="(component, index) in result.pca.components"
              :key="component.component"
            >
              <div>
                <strong>{{ component.component }}</strong>
                <span>
                  解释 {{ formatPercent(result.pca.explained_variance_ratio[index] ?? 0) }}
                </span>
              </div>
              <ul>
                <li v-for="loading in component.loadings" :key="loading.feature">
                  <span>{{ loading.feature }}</span>
                  <strong>{{ formatNumber(loading.weight) }}</strong>
                </li>
              </ul>
            </article>
          </div>
        </section>

        <section class="result-section">
          <div class="section-heading">
            <div>
              <span>ANOMALY REVIEW</span>
              <h2>样本异常对照</h2>
            </div>
            <p>按两种算法中的最高异常分数排序，最多展示 100 条。</p>
          </div>
          <div class="prediction-table">
            <el-table :data="predictionRows.slice(0, 100)">
              <el-table-column min-width="150" prop="sample_id" label="样本编号" />
              <el-table-column width="155" label="Isolation Forest">
                <template #default="{ row }">
                  {{ formatNumber(row.if_score) }}
                </template>
              </el-table-column>
              <el-table-column width="110" label="IF 判断">
                <template #default="{ row }">
                  <el-tag
                    :type="row.if_label === 'anomaly' ? 'danger' : 'success'"
                    effect="plain"
                  >
                    {{ row.if_label === 'anomaly' ? '异常' : '正常' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column width="120" label="LOF">
                <template #default="{ row }">
                  {{ formatNumber(row.lof_score) }}
                </template>
              </el-table-column>
              <el-table-column width="110" label="LOF 判断">
                <template #default="{ row }">
                  <el-tag
                    :type="row.lof_label === 'anomaly' ? 'danger' : 'success'"
                    effect="plain"
                  >
                    {{ row.lof_label === 'anomaly' ? '异常' : '正常' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column width="120" align="right" label="综合">
                <template #default="{ row }">
                  <span :class="['review-state', { alert: row.is_anomaly }]">
                    <el-icon v-if="row.is_anomaly"><Warning /></el-icon>
                    <el-icon v-else><Select /></el-icon>
                    {{ row.is_anomaly ? '需复核' : '正常' }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>
      </main>
    </div>
  </section>
</template>

<style scoped>
.ml-page {
  width: min(1220px, calc(100% - 40px));
  padding: 52px 0 90px;
  margin: 0 auto;
}

.ml-heading {
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

.ml-heading h1 {
  margin: 0;
  color: #17213a;
  font-size: clamp(2.35rem, 5vw, 3.9rem);
  letter-spacing: -0.055em;
}

.ml-heading > div:first-child > p:last-child {
  margin: 14px 0 0;
  color: #727b91;
}

.dataset-control {
  width: min(100%, 330px);
}

.dataset-control .el-select {
  width: 100%;
}

.empty-state,
.settings-panel,
.intro-panel,
.chart-card,
.loading-grid article,
.prediction-table {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(30, 42, 76, 0.08);
  border-radius: 20px;
  box-shadow: 0 16px 40px rgba(31, 42, 76, 0.06);
}

.empty-state {
  min-height: 360px;
  margin-top: 44px;
}

.workspace-grid {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
  margin-top: 42px;
}

.settings-panel {
  position: sticky;
  top: 18px;
  display: grid;
  gap: 11px;
  padding: 22px;
}

.settings-title {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 10px;
}

.settings-title > span {
  display: grid;
  width: 42px;
  height: 42px;
  color: #5556d9;
  background: #eeeeff;
  border-radius: 13px;
  place-items: center;
}

.settings-title h2 {
  margin: 0;
  font-size: 1rem;
}

.settings-title p,
.field-help {
  margin: 4px 0 0;
  color: #949aab;
  font-size: 0.7rem;
}

.settings-panel label {
  margin-top: 9px;
  color: #555e75;
  font-size: 0.74rem;
  font-weight: 750;
}

.settings-panel .el-select,
.settings-panel .el-input-number {
  width: 100%;
}

.slider-row {
  display: grid;
  grid-template-columns: 1fr 42px;
  gap: 12px;
  align-items: center;
}

.slider-row strong {
  color: #5556d9;
  font-size: 0.78rem;
  text-align: right;
}

.run-button {
  width: 100%;
  margin-top: 12px;
}

.intro-panel {
  display: flex;
  min-height: 490px;
  align-items: center;
  flex-direction: column;
  justify-content: center;
  padding: 50px;
  text-align: center;
}

.intro-icon {
  display: grid;
  width: 66px;
  height: 66px;
  color: white;
  background: linear-gradient(145deg, #7779ff, #4b4cd3);
  border-radius: 20px;
  place-items: center;
  box-shadow: 0 14px 28px rgba(78, 79, 204, 0.24);
}

.intro-panel h2 {
  margin: 23px 0 10px;
  font-size: 1.55rem;
}

.intro-panel > p {
  max-width: 580px;
  margin: 0;
  color: #737c91;
  line-height: 1.7;
}

.algorithm-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  width: min(100%, 650px);
  margin-top: 30px;
}

.algorithm-list div {
  display: grid;
  gap: 5px;
  padding: 16px;
  text-align: left;
  background: #f7f8fc;
  border-radius: 13px;
}

.algorithm-list span {
  color: #5b5cf0;
  font-size: 0.65rem;
  font-weight: 800;
}

.algorithm-list strong {
  font-size: 0.8rem;
}

.algorithm-list small {
  color: #949aab;
  font-size: 0.68rem;
}

.result-workspace {
  min-width: 0;
}

.result-banner {
  display: flex;
  align-items: end;
  justify-content: space-between;
  padding: 24px 27px;
  color: white;
  background: linear-gradient(120deg, #292d64, #5557cb);
  border-radius: 19px;
}

.result-banner div {
  display: grid;
  gap: 6px;
}

.result-banner span,
.result-banner small {
  color: #cecfff;
  font-size: 0.7rem;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-top: 12px;
}

.metric-grid article {
  display: grid;
  gap: 6px;
  padding: 18px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(30, 42, 76, 0.08);
  border-radius: 15px;
}

.metric-grid span,
.metric-grid small {
  color: #8b92a5;
  font-size: 0.68rem;
}

.metric-grid strong {
  color: #29324c;
  font-size: 1.35rem;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 13px;
  margin-top: 13px;
}

.chart-card {
  min-width: 0;
  padding: 20px 17px 12px;
}

.card-heading,
.section-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
}

.card-heading span,
.section-heading span {
  color: #5b5cf0;
  font-size: 0.66rem;
  font-weight: 800;
  letter-spacing: 0.11em;
}

.card-heading h3 {
  margin: 5px 0 0;
  font-size: 0.95rem;
}

.card-heading small,
.section-heading p {
  margin: 0;
  color: #949aab;
  font-size: 0.68rem;
}

.result-section {
  margin-top: 38px;
}

.section-heading {
  margin-bottom: 15px;
}

.section-heading h2 {
  margin: 6px 0 0;
  font-size: 1.35rem;
}

.loading-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.loading-grid article {
  padding: 20px;
}

.loading-grid article > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.loading-grid article > div span {
  color: #8b92a5;
  font-size: 0.72rem;
}

.loading-grid ul {
  display: grid;
  gap: 8px;
  padding: 0;
  margin: 18px 0 0;
  list-style: none;
}

.loading-grid li {
  display: flex;
  justify-content: space-between;
  padding-bottom: 8px;
  color: #5e677c;
  font-size: 0.75rem;
  border-bottom: 1px solid #eef0f6;
}

.prediction-table {
  overflow: hidden;
  padding: 8px;
}

.review-state {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  color: #2ba27f;
  font-size: 0.72rem;
  font-weight: 700;
}

.review-state.alert {
  color: #e45e56;
}

@media (max-width: 1050px) {
  .workspace-grid {
    grid-template-columns: 1fr;
  }

  .settings-panel {
    position: static;
  }
}

@media (max-width: 800px) {
  .ml-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .dataset-control {
    width: 100%;
  }

  .metric-grid,
  .chart-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .ml-page {
    width: min(100% - 28px, 1220px);
    padding-top: 35px;
  }

  .algorithm-list,
  .metric-grid,
  .chart-grid,
  .loading-grid {
    grid-template-columns: 1fr;
  }

  .card-heading,
  .section-heading,
  .result-banner {
    align-items: flex-start;
    flex-direction: column;
    gap: 7px;
  }
}
</style>
