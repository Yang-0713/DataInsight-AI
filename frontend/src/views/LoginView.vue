<script setup lang="ts">
import { reactive, ref } from 'vue'
import { Lock, User } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../store/auth'
import { getApiErrorMessage } from '../utils/errors'

const formRef = ref<FormInstance>()
const loading = ref(false)
const errorMessage = ref('')
const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const form = reactive({
  identity: '',
  password: '',
})

const rules: FormRules<typeof form> = {
  identity: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' },
    { min: 3, max: 255, message: '请输入有效的用户名或邮箱', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 128, message: '密码长度至少为 8 位', trigger: 'blur' },
  ],
}

async function submit(): Promise<void> {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    await authStore.login(form)
    const redirect = typeof route.query.redirect === 'string'
      && route.query.redirect.startsWith('/')
      ? route.query.redirect
      : '/dashboard'
    await router.push(redirect)
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '登录失败，请检查账户信息')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="auth-page">
    <div class="auth-copy">
      <p class="eyebrow">WELCOME BACK</p>
      <h1>重新连接你的<br />数据工作台。</h1>
      <p>
        登录后即可进入 DataInsight AI。你的数据集、分析任务和智能报告将在后续阶段汇聚于此。
      </p>
      <div class="security-note">
        <span class="security-dot"></span>
        密码使用 Argon2 单向哈希保存，接口由 JWT 访问令牌保护
      </div>
    </div>

    <div class="auth-card">
      <div class="auth-card-heading">
        <span>账户登录</span>
        <small>第二阶段 · 身份认证</small>
      </div>

      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        :closable="false"
        show-icon
      />

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="submit"
      >
        <el-form-item label="用户名或邮箱" prop="identity">
          <el-input
            v-model="form.identity"
            :prefix-icon="User"
            placeholder="analyst 或 analyst@example.com"
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            :prefix-icon="Lock"
            type="password"
            placeholder="输入账户密码"
            autocomplete="current-password"
            show-password
            @keyup.enter="submit"
          />
        </el-form-item>
        <el-button
          class="submit-button"
          type="primary"
          native-type="submit"
          :loading="loading"
          @click="submit"
        >
          登录工作台
        </el-button>
      </el-form>

      <p class="auth-switch">
        还没有账户？<RouterLink to="/register">立即注册</RouterLink>
      </p>
    </div>
  </section>
</template>

<style scoped>
@import '../style/auth.css';
</style>
