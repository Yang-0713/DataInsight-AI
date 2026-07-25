import { createRouter, createWebHistory } from 'vue-router'

import DashboardView from '../views/DashboardView.vue'
import DatasetsView from '../views/DatasetsView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import { getAuthToken } from '../utils/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: () => (getAuthToken() ? '/dashboard' : '/login'),
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { guestOnly: true },
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true },
    },
    {
      path: '/datasets',
      name: 'datasets',
      component: DatasetsView,
      meta: { requiresAuth: true },
    },
    {
      path: '/analysis/:datasetId?',
      name: 'analysis',
      component: () => import('../views/AnalysisView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/machine-learning/:datasetId?',
      name: 'machine-learning',
      component: () => import('../views/MachineLearningView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/ai-analyst/:datasetId?',
      name: 'ai-analyst',
      component: () => import('../views/AIAnalystView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to) => {
  const hasToken = Boolean(getAuthToken())

  if (to.meta.requiresAuth && !hasToken) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }
  if (to.meta.guestOnly && hasToken) {
    return { name: 'dashboard' }
  }
  return true
})

export default router
