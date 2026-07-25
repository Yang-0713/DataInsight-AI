<script setup lang="ts">
import { Connection, DataBoard, Setting } from '@element-plus/icons-vue'

import StatusCard from '../components/StatusCard.vue'

const foundations = [
  {
    icon: DataBoard,
    title: 'Vue application',
    description:
      'Vue 3, TypeScript, routing, state management, Element Plus, ECharts, and Tailwind are ready.',
  },
  {
    icon: Connection,
    title: 'FastAPI service',
    description:
      'A versioned API foundation and health endpoint are available for the upcoming modules.',
  },
  {
    icon: Setting,
    title: 'MySQL configuration',
    description:
      'SQLAlchemy reads safe, environment-based MySQL settings with no credentials committed.',
  },
]
</script>

<template>
  <section class="home">
    <div class="hero">
      <p class="eyebrow">OPEN-SOURCE DATA INTELLIGENCE</p>
      <h1>Your intelligent data analyst is taking shape.</h1>
      <p class="intro">
        The DataInsight AI foundation is ready. Uploads, automated exploration,
        anomaly detection, and AI-generated reports will arrive phase by phase.
      </p>
      <div class="hero-actions">
        <el-button type="primary" size="large" disabled>
          Start an analysis
        </el-button>
        <span>Available after dataset management is implemented</span>
      </div>
    </div>

    <div class="foundation-grid" aria-label="Phase 1 project status">
      <StatusCard
        v-for="item in foundations"
        :key="item.title"
        v-bind="item"
      />
    </div>

    <div class="next-step">
      <span>Next milestone</span>
      <strong>Secure authentication with JWT</strong>
      <p>Registration, login, protected routes, and the user model are planned for Phase 2.</p>
    </div>
  </section>
</template>

<style scoped>
.home {
  width: min(1120px, calc(100% - 40px));
  padding: 64px 0 88px;
  margin: 0 auto;
}

.hero {
  max-width: 790px;
}

.eyebrow {
  margin: 0 0 18px;
  color: #5b5cf0;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.15em;
}

h1 {
  max-width: 760px;
  margin: 0;
  color: #17213a;
  font-size: clamp(2.6rem, 7vw, 5.2rem);
  font-weight: 780;
  letter-spacing: -0.065em;
  line-height: 0.99;
}

.intro {
  max-width: 670px;
  margin: 28px 0 0;
  color: #626c84;
  font-size: 1.08rem;
  line-height: 1.75;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-top: 28px;
}

.hero-actions span {
  max-width: 260px;
  color: #8a91a5;
  font-size: 0.78rem;
  line-height: 1.45;
}

.foundation-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  margin-top: 72px;
}

.next-step {
  display: grid;
  grid-template-columns: 130px 1fr 1.7fr;
  gap: 20px;
  align-items: center;
  padding: 24px 4px;
  margin-top: 24px;
  color: #4d566e;
  border-top: 1px solid rgba(30, 42, 76, 0.1);
  border-bottom: 1px solid rgba(30, 42, 76, 0.1);
}

.next-step span {
  color: #8a91a5;
  font-size: 0.76rem;
  font-weight: 750;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.next-step strong {
  color: #252e48;
  font-size: 0.92rem;
}

.next-step p {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.5;
}

@media (max-width: 800px) {
  .foundation-grid {
    grid-template-columns: 1fr;
  }

  .next-step {
    grid-template-columns: 1fr;
    gap: 8px;
  }
}

@media (max-width: 640px) {
  .home {
    width: min(100% - 28px, 1120px);
    padding-top: 42px;
  }

  .hero-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .foundation-grid {
    margin-top: 52px;
  }
}
</style>

