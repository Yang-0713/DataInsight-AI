<script setup lang="ts">
import {
  BarChart,
  BoxplotChart,
  HeatmapChart,
  LineChart,
} from 'echarts/charts'
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  VisualMapComponent,
} from 'echarts/components'
import {
  init,
  use,
  type ECharts,
  type EChartsCoreOption,
} from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

use([
  BarChart,
  BoxplotChart,
  HeatmapChart,
  LineChart,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  VisualMapComponent,
  CanvasRenderer,
])

const props = defineProps<{
  option: Record<string, unknown>
  title: string
}>()

const chartElement = ref<HTMLDivElement>()
let chart: ECharts | null = null
let resizeObserver: ResizeObserver | null = null

function render(): void {
  if (!chart) return
  chart.setOption(props.option as EChartsCoreOption, { notMerge: true })
}

onMounted(async () => {
  await nextTick()
  if (!chartElement.value) return
  chart = init(chartElement.value)
  render()
  resizeObserver = new ResizeObserver(() => chart?.resize())
  resizeObserver.observe(chartElement.value)
})

watch(
  () => props.option,
  () => render(),
  { deep: true },
)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chart?.dispose()
})
</script>

<template>
  <div
    ref="chartElement"
    class="echart"
    role="img"
    :aria-label="title"
  ></div>
</template>

<style scoped>
.echart {
  width: 100%;
  height: 330px;
}
</style>
