<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  DataAnalysis,
  Delete,
  Document,
  InfoFilled,
  UploadFilled,
} from '@element-plus/icons-vue'
import {
  ElMessage,
  ElMessageBox,
  type UploadFile,
  type UploadInstance,
} from 'element-plus'
import { useRouter } from 'vue-router'

import type { Dataset } from '../api/datasets'
import { useDatasetStore } from '../store/datasets'
import { getApiErrorMessage } from '../utils/errors'

const datasetStore = useDatasetStore()
const router = useRouter()
const uploadRef = ref<UploadInstance>()
const selectedFile = ref<File | null>(null)
const detailVisible = ref(false)
const selectedDataset = ref<Dataset | null>(null)
const detailLoading = ref(false)

const totalRows = computed(() =>
  datasetStore.items.reduce((total, item) => total + item.rows, 0),
)
const totalColumns = computed(() =>
  datasetStore.items.reduce((total, item) => total + item.columns, 0),
)

onMounted(async () => {
  try {
    await datasetStore.load()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '数据集列表加载失败'))
  }
})

function onFileChange(uploadFile: UploadFile): void {
  selectedFile.value = uploadFile.raw ?? null
}

function onFileRemove(): void {
  selectedFile.value = null
}

function onFileExceed(): void {
  ElMessage.warning('每次只能上传一个 CSV 文件')
}

async function submitUpload(): Promise<void> {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择一个 CSV 文件')
    return
  }

  try {
    const dataset = await datasetStore.upload(selectedFile.value)
    ElMessage.success(`“${dataset.filename}”上传成功`)
    selectedFile.value = null
    uploadRef.value?.clearFiles()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '上传失败，请检查 CSV 文件'))
  }
}

async function showDetail(dataset: Dataset): Promise<void> {
  detailVisible.value = true
  detailLoading.value = true
  try {
    selectedDataset.value = await datasetStore.fetchOne(dataset.id)
  } catch (error) {
    detailVisible.value = false
    ElMessage.error(getApiErrorMessage(error, '数据集详情加载失败'))
  } finally {
    detailLoading.value = false
  }
}

async function confirmDelete(dataset: Dataset): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `删除后将同时移除本地文件。确定删除“${dataset.filename}”吗？`,
      '删除数据集',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
  } catch {
    return
  }

  try {
    await datasetStore.remove(dataset.id)
    if (selectedDataset.value?.id === dataset.id) {
      detailVisible.value = false
    }
    ElMessage.success('数据集已删除')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '删除失败，请稍后重试'))
  }
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

function formatNumber(value: number): string {
  return new Intl.NumberFormat('zh-CN').format(value)
}

async function openAnalysis(dataset: Dataset): Promise<void> {
  detailVisible.value = false
  await router.push({
    name: 'analysis',
    params: { datasetId: String(dataset.id) },
  })
}
</script>

<template>
  <section class="datasets-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">DATASET LIBRARY</p>
        <h1>数据集管理</h1>
        <p>上传 CSV，系统会验证文件并自动提取行列规模。</p>
      </div>
      <div class="summary-strip">
        <div>
          <span>数据集</span>
          <strong>{{ datasetStore.count }}</strong>
        </div>
        <div>
          <span>总记录</span>
          <strong>{{ formatNumber(totalRows) }}</strong>
        </div>
        <div>
          <span>总字段</span>
          <strong>{{ formatNumber(totalColumns) }}</strong>
        </div>
      </div>
    </div>

    <div class="dataset-layout">
      <aside class="upload-panel">
        <div class="panel-heading">
          <span class="panel-icon"><el-icon :size="21"><UploadFilled /></el-icon></span>
          <div>
            <h2>上传新数据集</h2>
            <p>支持 UTF-8 或 GB18030 编码</p>
          </div>
        </div>

        <el-upload
          ref="uploadRef"
          class="csv-uploader"
          drag
          accept=".csv,text/csv"
          :auto-upload="false"
          :limit="1"
          :on-change="onFileChange"
          :on-remove="onFileRemove"
          :on-exceed="onFileExceed"
        >
          <el-icon class="upload-illustration" :size="34"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            拖拽 CSV 到这里<br />
            <em>或点击选择文件</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">单个文件最大 50 MB</div>
          </template>
        </el-upload>

        <el-progress
          v-if="datasetStore.uploading"
          :percentage="datasetStore.uploadProgress"
          :stroke-width="7"
        />

        <el-button
          class="upload-button"
          type="primary"
          size="large"
          :icon="UploadFilled"
          :loading="datasetStore.uploading"
          :disabled="!selectedFile"
          @click="submitUpload"
        >
          上传并提取信息
        </el-button>

        <div class="privacy-note">
          <span></span>
          文件仅存储在你的本地项目目录中，其他用户无法查看或删除。
        </div>
      </aside>

      <div class="library-panel">
        <div class="library-heading">
          <div>
            <span>MY DATASETS</span>
            <h2>我的数据资产</h2>
          </div>
          <small>按上传时间排序</small>
        </div>

        <div v-loading="datasetStore.loading" class="dataset-table-wrap">
          <el-empty
            v-if="!datasetStore.loading && datasetStore.items.length === 0"
            description="还没有数据集，先上传一个 CSV 吧"
          />
          <el-table v-else :data="datasetStore.items" class="dataset-table">
            <el-table-column min-width="230" label="文件">
              <template #default="{ row }">
                <div class="file-cell">
                  <span><el-icon :size="19"><Document /></el-icon></span>
                  <div>
                    <strong>{{ row.filename }}</strong>
                    <small>#{{ row.id }}</small>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column width="120" label="记录数">
              <template #default="{ row }">{{ formatNumber(row.rows) }}</template>
            </el-table-column>
            <el-table-column width="105" label="字段数" prop="columns" />
            <el-table-column min-width="170" label="上传时间">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
            <el-table-column width="170" align="right">
              <template #default="{ row }">
                <el-button
                  circle
                  text
                  type="primary"
                  :icon="DataAnalysis"
                  aria-label="分析数据集"
                  @click="openAnalysis(row)"
                />
                <el-button
                  circle
                  text
                  :icon="InfoFilled"
                  aria-label="查看详情"
                  @click="showDetail(row)"
                />
                <el-button
                  circle
                  text
                  type="danger"
                  :icon="Delete"
                  aria-label="删除数据集"
                  @click="confirmDelete(row)"
                />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <el-drawer
      v-model="detailVisible"
      title="数据集详情"
      size="min(440px, 92vw)"
    >
      <div v-loading="detailLoading" class="detail-content">
        <template v-if="selectedDataset">
          <span class="detail-file-icon"><el-icon :size="28"><Document /></el-icon></span>
          <p class="detail-kicker">DATASET #{{ selectedDataset.id }}</p>
          <h2>{{ selectedDataset.filename }}</h2>

          <div class="detail-grid">
            <div>
              <span>记录数</span>
              <strong>{{ formatNumber(selectedDataset.rows) }}</strong>
            </div>
            <div>
              <span>字段数</span>
              <strong>{{ formatNumber(selectedDataset.columns) }}</strong>
            </div>
          </div>

          <div class="detail-meta">
            <span>上传时间</span>
            <strong>{{ formatDate(selectedDataset.created_at) }}</strong>
          </div>

          <el-button
            class="detail-analysis"
            type="primary"
            :icon="DataAnalysis"
            @click="openAnalysis(selectedDataset)"
          >
            开始自动 EDA
          </el-button>

          <el-button
            class="detail-delete"
            type="danger"
            plain
            :icon="Delete"
            @click="confirmDelete(selectedDataset)"
          >
            删除数据集
          </el-button>
        </template>
      </div>
    </el-drawer>
  </section>
</template>

<style scoped>
.datasets-page {
  width: min(1180px, calc(100% - 40px));
  padding: 56px 0 88px;
  margin: 0 auto;
}

.page-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 40px;
}

.eyebrow {
  margin: 0 0 10px;
  color: #5b5cf0;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.15em;
}

.page-heading h1 {
  margin: 0;
  color: #17213a;
  font-size: clamp(2.4rem, 5vw, 4rem);
  letter-spacing: -0.055em;
}

.page-heading > div:first-child > p:last-child {
  margin: 14px 0 0;
  color: #727b91;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(90px, 1fr));
  min-width: 330px;
  padding: 16px 4px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(30, 42, 76, 0.08);
  border-radius: 16px;
}

.summary-strip div {
  display: grid;
  gap: 4px;
  padding: 0 18px;
  border-right: 1px solid rgba(30, 42, 76, 0.09);
}

.summary-strip div:last-child {
  border-right: 0;
}

.summary-strip span {
  color: #9298aa;
  font-size: 0.7rem;
}

.summary-strip strong {
  color: #252e48;
  font-size: 1.15rem;
}

.dataset-layout {
  display: grid;
  grid-template-columns: 330px minmax(0, 1fr);
  gap: 20px;
  align-items: start;
  margin-top: 46px;
}

.upload-panel,
.library-panel {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(30, 42, 76, 0.08);
  border-radius: 21px;
  box-shadow: 0 16px 40px rgba(31, 42, 76, 0.07);
}

.upload-panel {
  padding: 23px;
}

.panel-heading {
  display: flex;
  gap: 13px;
  align-items: center;
  margin-bottom: 22px;
}

.panel-icon {
  display: grid;
  width: 41px;
  height: 41px;
  color: #5556d9;
  background: #eeeeff;
  border-radius: 12px;
  place-items: center;
}

.panel-heading h2,
.library-heading h2 {
  margin: 0;
  font-size: 1rem;
}

.panel-heading p {
  margin: 4px 0 0;
  color: #969bad;
  font-size: 0.7rem;
}

.csv-uploader :deep(.el-upload) {
  width: 100%;
}

.csv-uploader :deep(.el-upload-dragger) {
  width: 100%;
  padding: 32px 16px;
  background: #f8f9fd;
  border-color: #d9daec;
  border-radius: 15px;
}

.upload-illustration {
  color: #6a6be6;
  margin-bottom: 12px;
}

.csv-uploader :deep(.el-upload__text) {
  color: #6f778d;
  line-height: 1.55;
}

.csv-uploader :deep(.el-upload__text em) {
  color: #5556d9;
  font-style: normal;
  font-weight: 700;
}

.upload-button {
  width: 100%;
  margin-top: 18px;
  border-radius: 11px;
}

.privacy-note {
  display: flex;
  gap: 9px;
  align-items: flex-start;
  padding-top: 18px;
  margin-top: 18px;
  color: #8a91a4;
  font-size: 0.7rem;
  line-height: 1.55;
  border-top: 1px solid rgba(30, 42, 76, 0.08);
}

.privacy-note span {
  flex: 0 0 auto;
  width: 7px;
  height: 7px;
  margin-top: 3px;
  background: #2cc78f;
  border-radius: 99px;
}

.library-panel {
  min-width: 0;
  overflow: hidden;
}

.library-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  padding: 23px 25px 18px;
  border-bottom: 1px solid rgba(30, 42, 76, 0.08);
}

.library-heading span {
  color: #8d93a5;
  font-size: 0.66rem;
  font-weight: 800;
  letter-spacing: 0.11em;
}

.library-heading h2 {
  margin-top: 5px;
}

.library-heading small {
  color: #9ba0b0;
  font-size: 0.7rem;
}

.dataset-table-wrap {
  min-height: 310px;
}

.dataset-table {
  width: 100%;
}

.file-cell {
  display: flex;
  gap: 11px;
  align-items: center;
}

.file-cell > span {
  display: grid;
  width: 35px;
  height: 35px;
  color: #5758d8;
  background: #f0f0ff;
  border-radius: 10px;
  place-items: center;
}

.file-cell div {
  display: grid;
  min-width: 0;
}

.file-cell strong {
  overflow: hidden;
  color: #313a53;
  font-size: 0.82rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-cell small {
  color: #a0a5b4;
  font-size: 0.66rem;
}

.detail-content {
  min-height: 420px;
}

.detail-file-icon {
  display: grid;
  width: 58px;
  height: 58px;
  color: white;
  background: linear-gradient(145deg, #7779ff, #4b4cd3);
  border-radius: 17px;
  place-items: center;
}

.detail-kicker {
  margin: 24px 0 7px;
  color: #8c92a3;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.detail-content h2 {
  margin: 0;
  word-break: break-word;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 28px;
}

.detail-grid div,
.detail-meta {
  display: grid;
  gap: 6px;
  padding: 18px;
  background: #f7f8fc;
  border-radius: 13px;
}

.detail-grid span,
.detail-meta span {
  color: #9298a9;
  font-size: 0.7rem;
}

.detail-grid strong {
  font-size: 1.35rem;
}

.detail-meta {
  margin: 12px 0 22px;
}

.detail-meta strong {
  font-size: 0.84rem;
}

.detail-delete {
  width: 100%;
  margin-top: 12px;
}

.detail-analysis {
  width: 100%;
}

@media (max-width: 900px) {
  .dataset-layout {
    grid-template-columns: 1fr;
  }

  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .summary-strip {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .datasets-page {
    width: min(100% - 28px, 1180px);
    padding-top: 36px;
  }

  .summary-strip {
    min-width: 0;
  }

  .summary-strip div {
    padding: 0 10px;
  }

  .library-panel {
    overflow-x: auto;
  }
}
</style>
