<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { DataAnalysis, SwitchButton } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from './store/auth'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const isAuthPage = computed(() => ['login', 'register'].includes(String(route.name)))

onMounted(async () => {
  await authStore.initialize()
  if (route.meta.requiresAuth && !authStore.isAuthenticated) {
    await router.replace({
      name: 'login',
      query: { redirect: route.fullPath },
    })
  }
})

async function logout(): Promise<void> {
  authStore.logout()
  await router.push({ name: 'login' })
}
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
      <div class="header-actions">
        <template v-if="authStore.user && !isAuthPage">
          <nav class="main-nav" aria-label="主要导航">
            <RouterLink to="/dashboard">工作台</RouterLink>
            <RouterLink to="/datasets">数据集</RouterLink>
          </nav>
          <span class="user-chip">
            <span class="user-avatar">{{ authStore.user.username.slice(0, 1).toUpperCase() }}</span>
            {{ authStore.user.username }}
          </span>
          <el-button text :icon="SwitchButton" @click="logout">退出</el-button>
        </template>
        <template v-else-if="isAuthPage">
          <RouterLink v-if="route.name === 'login'" class="header-link" to="/register">
            创建账户
          </RouterLink>
          <RouterLink v-else class="header-link" to="/login">
            返回登录
          </RouterLink>
        </template>
        <span class="phase-badge">第三阶段</span>
      </div>
    </header>

    <main>
      <RouterView />
    </main>
  </div>
</template>
