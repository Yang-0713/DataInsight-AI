<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  icon: Component
  title: string
  description: string
}>()
</script>

<template>
  <article class="status-card">
    <span class="status-icon">
      <el-icon :size="21"><component :is="icon" /></el-icon>
    </span>
    <div>
      <h2>{{ title }}</h2>
      <p>{{ description }}</p>
    </div>
    <span class="ready-dot" aria-label="Ready"></span>
  </article>
</template>

<style scoped>
.status-card {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 16px;
  min-height: 152px;
  padding: 24px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(30, 42, 76, 0.08);
  border-radius: 20px;
  box-shadow: 0 16px 45px rgba(31, 42, 76, 0.07);
}

.status-icon {
  display: grid;
  width: 42px;
  height: 42px;
  color: #5556d9;
  background: #eeeeff;
  border-radius: 13px;
  place-items: center;
}

h2 {
  margin: 2px 0 8px;
  font-size: 1rem;
}

p {
  margin: 0;
  color: #69728a;
  font-size: 0.88rem;
  line-height: 1.6;
}

.ready-dot {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 8px;
  height: 8px;
  background: #2cc78f;
  border-radius: 999px;
  box-shadow: 0 0 0 5px rgba(44, 199, 143, 0.12);
}
</style>

