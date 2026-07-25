<script setup lang="ts">
import { DataAnalysis } from '@element-plus/icons-vue'
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <RouterLink class="brand" to="/" aria-label="DataInsight AI home">
        <span class="brand-mark">
          <el-icon :size="22"><DataAnalysis /></el-icon>
        </span>
        <span>DataInsight AI</span>
      </RouterLink>
      <span class="phase-badge">Phase 1</span>
    </header>

    <main>
      <RouterView />
    </main>
  </div>
</template>

