<script setup lang="ts">
import { computed } from 'vue'
import {
  DataAnalysis,
  Lock,
  MagicStick,
  UploadFilled,
} from '@element-plus/icons-vue'

import { useAuthStore } from '../store/auth'

const authStore = useAuthStore()
const joinedDate = computed(() => {
  if (!authStore.user) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date(authStore.user.created_at))
})

const upcomingModules = [
  {
    icon: UploadFilled,
    title: '数据集管理',
    description: '上传 CSV、查看数据集信息并管理个人数据资产。',
    phase: '第三阶段',
  },
  {
    icon: DataAnalysis,
    title: '自动化 EDA',
    description: '生成数据画像、统计结果和适用于 ECharts 的图表数据。',
    phase: '第四阶段',
  },
  {
    icon: MagicStick,
    title: 'AI 数据分析师',
    description: '基于分析结果给出发现、问题解释和行动建议。',
    phase: '第六阶段',
  },
]
</script>

<template>
  <section class="dashboard">
    <div class="dashboard-hero">
      <div>
        <p class="eyebrow">AUTHENTICATED WORKSPACE</p>
        <h1>你好，{{ authStore.user?.username }}。</h1>
        <p>身份认证系统已经就绪。你的个人数据分析空间将在这里逐步展开。</p>
      </div>
      <div class="account-card">
        <span class="account-icon"><el-icon :size="20"><Lock /></el-icon></span>
        <div>
          <small>当前账户</small>
          <strong>{{ authStore.user?.email }}</strong>
          <span>{{ authStore.user?.role === 'ADMIN' ? '管理员' : '普通用户' }} · {{ joinedDate }} 加入</span>
        </div>
      </div>
    </div>

    <div class="phase-status">
      <div>
        <span class="status-kicker">PHASE 2</span>
        <strong>账户与访问控制</strong>
      </div>
      <p>注册、登录、密码哈希、JWT 签发和受保护用户接口已连接。</p>
      <span class="status-complete">已完成</span>
    </div>

    <div class="module-heading">
      <div>
        <span>接下来</span>
        <h2>你的分析能力路线图</h2>
      </div>
      <p>每个模块都会建立在当前安全账户体系之上。</p>
    </div>

    <div class="module-grid">
      <article v-for="module in upcomingModules" :key="module.title" class="module-card">
        <span class="module-icon">
          <el-icon :size="23"><component :is="module.icon" /></el-icon>
        </span>
        <span class="module-phase">{{ module.phase }}</span>
        <h3>{{ module.title }}</h3>
        <p>{{ module.description }}</p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.dashboard {
  width: min(1120px, calc(100% - 40px));
  padding: 60px 0 88px;
  margin: 0 auto;
}

.dashboard-hero {
  display: grid;
  grid-template-columns: 1.4fr 0.8fr;
  gap: 50px;
  align-items: end;
}

.eyebrow {
  margin: 0 0 14px;
  color: #5b5cf0;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.15em;
}

h1 {
  margin: 0;
  color: #17213a;
  font-size: clamp(2.6rem, 6vw, 4.8rem);
  font-weight: 780;
  letter-spacing: -0.06em;
}

.dashboard-hero > div > p:last-child {
  max-width: 640px;
  margin: 20px 0 0;
  color: #687189;
  line-height: 1.7;
}

.account-card {
  display: flex;
  gap: 15px;
  align-items: flex-start;
  padding: 22px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(30, 42, 76, 0.08);
  border-radius: 18px;
}

.account-icon {
  display: grid;
  flex: 0 0 auto;
  width: 42px;
  height: 42px;
  color: #5657dc;
  background: #eeeeff;
  border-radius: 13px;
  place-items: center;
}

.account-card div {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.account-card small,
.account-card span {
  color: #8990a4;
  font-size: 0.72rem;
}

.account-card strong {
  overflow: hidden;
  color: #2a334c;
  font-size: 0.88rem;
  text-overflow: ellipsis;
}

.phase-status {
  display: grid;
  grid-template-columns: 1fr 1.5fr auto;
  gap: 30px;
  align-items: center;
  padding: 26px 30px;
  margin-top: 64px;
  color: white;
  background: linear-gradient(120deg, #272b5f, #4d4fbe);
  border-radius: 20px;
  box-shadow: 0 18px 45px rgba(58, 59, 142, 0.22);
}

.phase-status > div {
  display: grid;
  gap: 6px;
}

.status-kicker {
  color: #bfc0ff;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.13em;
}

.phase-status p {
  margin: 0;
  color: #d7d8f7;
  font-size: 0.84rem;
  line-height: 1.6;
}

.status-complete {
  padding: 7px 12px;
  color: #caffea;
  font-size: 0.74rem;
  font-weight: 700;
  background: rgba(44, 199, 143, 0.16);
  border: 1px solid rgba(112, 236, 190, 0.2);
  border-radius: 999px;
}

.module-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  margin-top: 64px;
}

.module-heading span {
  color: #8b92a7;
  font-size: 0.72rem;
  font-weight: 750;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.module-heading h2 {
  margin: 7px 0 0;
  font-size: 1.65rem;
}

.module-heading p {
  margin: 0;
  color: #858da2;
  font-size: 0.82rem;
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  margin-top: 24px;
}

.module-card {
  position: relative;
  min-height: 210px;
  padding: 25px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(30, 42, 76, 0.08);
  border-radius: 20px;
  box-shadow: 0 14px 35px rgba(31, 42, 76, 0.06);
}

.module-icon {
  display: grid;
  width: 44px;
  height: 44px;
  color: #5556d9;
  background: #eeeeff;
  border-radius: 13px;
  place-items: center;
}

.module-phase {
  position: absolute;
  top: 25px;
  right: 25px;
  color: #9a9fb0;
  font-size: 0.72rem;
}

.module-card h3 {
  margin: 24px 0 9px;
  font-size: 1rem;
}

.module-card p {
  margin: 0;
  color: #727b91;
  font-size: 0.83rem;
  line-height: 1.65;
}

@media (max-width: 850px) {
  .dashboard-hero,
  .module-grid {
    grid-template-columns: 1fr;
  }

  .phase-status {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .status-complete {
    justify-self: start;
  }
}

@media (max-width: 640px) {
  .dashboard {
    width: min(100% - 28px, 1120px);
    padding-top: 38px;
  }

  .module-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 12px;
  }
}
</style>
