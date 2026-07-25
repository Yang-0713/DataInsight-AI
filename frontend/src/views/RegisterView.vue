<script setup lang="ts">
import { reactive, ref } from 'vue'
import { Message, Lock, User } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../store/auth'
import { getApiErrorMessage } from '../utils/errors'

interface RegisterForm {
  username: string
  email: string
  password: string
  confirmPassword: string
}

const formRef = ref<FormInstance>()
const loading = ref(false)
const errorMessage = ref('')
const authStore = useAuthStore()
const router = useRouter()

const form = reactive<RegisterForm>({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const rules: FormRules<RegisterForm> = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为 3–50 位', trigger: 'blur' },
    {
      pattern: /^[A-Za-z0-9_]+$/,
      message: '用户名只能包含字母、数字和下划线',
      trigger: 'blur',
    },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 128, message: '密码长度至少为 8 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
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
    await authStore.register({
      username: form.username,
      email: form.email,
      password: form.password,
    })
    await router.push('/dashboard')
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="auth-page">
    <div class="auth-copy">
      <p class="eyebrow">CREATE YOUR WORKSPACE</p>
      <h1>从一个账户，<br />开始理解数据。</h1>
      <p>
        创建 DataInsight AI 账户，为即将上线的数据集管理、自动化 EDA 和智能分析做好准备。
      </p>
      <div class="security-note">
        <span class="security-dot"></span>
        注册接口仅创建普通用户，管理员权限不会通过公开接口授予
      </div>
    </div>

    <div class="auth-card">
      <div class="auth-card-heading">
        <span>创建账户</span>
        <small>无需填写多余信息</small>
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
        <div class="form-row">
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              :prefix-icon="User"
              placeholder="例如 analyst"
              autocomplete="username"
            />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="form.email"
              :prefix-icon="Message"
              placeholder="name@example.com"
              autocomplete="email"
            />
          </el-form-item>
        </div>
        <div class="form-row">
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              :prefix-icon="Lock"
              type="password"
              placeholder="至少 8 位"
              autocomplete="new-password"
              show-password
            />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              :prefix-icon="Lock"
              type="password"
              placeholder="再次输入密码"
              autocomplete="new-password"
              show-password
              @keyup.enter="submit"
            />
          </el-form-item>
        </div>
        <el-button
          class="submit-button"
          type="primary"
          native-type="submit"
          :loading="loading"
          @click="submit"
        >
          创建并登录
        </el-button>
      </el-form>

      <p class="auth-switch">
        已有账户？<RouterLink to="/login">返回登录</RouterLink>
      </p>
    </div>
  </section>
</template>

<style scoped>
@import '../style/auth.css';
</style>
