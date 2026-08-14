<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getOverview, getDailyTrend } from '@/api/stats'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

const stats = ref({ bookCount: 0, borrowCount: 0, userCount: 0, overdueCount: 0 })
const loading = ref(false)
const isMock = ref(false)

const cards = computed(() => [
  { title: '图书总数', value: stats.value.bookCount, icon: 'Reading', color: '#409eff' },
  { title: '借阅总数', value: stats.value.borrowCount, icon: 'Tickets', color: '#67c23a' },
  { title: '注册用户', value: stats.value.userCount, icon: 'UserFilled', color: '#e6a23c' },
  { title: '逾期未还', value: stats.value.overdueCount, icon: 'Warning', color: '#f56c6c' }
])

const quickEntries = computed(() => {
  const common = [
    { title: '图书查询', desc: '检索馆藏图书', icon: 'Reading', path: '/books' },
    { title: '我的借阅', desc: '查看借阅记录', icon: 'Tickets', path: '/borrow/my' },
    { title: '个人中心', desc: '管理个人信息', icon: 'User', path: '/profile' }
  ]
  if (userStore.isAdmin) {
    return [
      { title: '图书管理', desc: '维护图书信息', icon: 'Notebook', path: '/admin/books' },
      { title: '借阅管理', desc: '处理借还书', icon: 'Document', path: '/admin/borrows' },
      { title: '用户管理', desc: '管理读者账号', icon: 'UserFilled', path: '/admin/users' },
      ...common.slice(0, 2)
    ]
  }
  return common
})

// 图表
const chartRef = ref(null)
let chartInstance = null

function renderChart(dates, borrows, returns) {
  if (!chartRef.value) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['借阅', '归还'], top: 0 },
    grid: { left: 50, right: 20, bottom: 30, top: 40 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { rotate: 45, fontSize: 11 },
      boundaryGap: false
    },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        name: '借阅',
        type: 'line',
        smooth: true,
        data: borrows,
        itemStyle: { color: '#409eff' },
        areaStyle: { color: 'rgba(64,158,255,0.1)' }
      },
      {
        name: '归还',
        type: 'line',
        smooth: true,
        data: returns,
        itemStyle: { color: '#67c23a' },
        areaStyle: { color: 'rgba(103,194,58,0.1)' }
      }
    ]
  })
}

function handleResize() { chartInstance?.resize() }

async function loadStats() {
  loading.value = true
  try {
    const [overviewRes, trendRes] = await Promise.allSettled([
      getOverview(),
      getDailyTrend()
    ])

    if (overviewRes.status === 'fulfilled') {
      stats.value = overviewRes.value.data || stats.value
      isMock.value = false
    } else {
      stats.value = { bookCount: 1280, borrowCount: 326, userCount: 542, overdueCount: 12 }
      isMock.value = true
    }

    if (trendRes.status === 'fulfilled' && trendRes.value.data) {
      const d = trendRes.value.data
      renderChart(d.dates || [], d.borrows || [], d.returns || [])
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<template>
  <div class="dashboard" v-loading="loading">
    <!-- 欢迎横幅 -->
    <el-card class="welcome" shadow="never">
      <div class="welcome-content">
        <h2>你好，{{ userStore.displayName }} 👋</h2>
        <p>欢迎使用大学图书管理系统，祝您阅读愉快！</p>
      </div>
    </el-card>

    <!-- Mock 数据提示 -->
    <el-alert
      v-if="isMock"
      title="当前为演示数据（后端接口未就绪），联调后将展示真实统计"
      type="info"
      :closable="false"
      show-icon
      class="mb-20"
    />

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col v-for="card in cards" :key="card.title" :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card-body">
            <div class="stat-icon" :style="{ backgroundColor: card.color }">
              <el-icon :size="28"><component :is="card.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ card.value }}</div>
              <div class="stat-title">{{ card.title }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 借阅/归还趋势图 -->
    <el-card shadow="never" class="mb-20">
      <template #header><span>近 30 天借阅 / 归还趋势</span></template>
      <div ref="chartRef" style="width: 100%; height: 340px"></div>
    </el-card>

    <!-- 快捷入口 -->
    <el-card class="quick-card" shadow="never">
      <template #header>
        <span>快捷入口</span>
      </template>
      <el-row :gutter="16">
        <el-col v-for="entry in quickEntries" :key="entry.path" :xs="12" :sm="8" :md="6">
          <div class="quick-item" @click="router.push(entry.path)">
            <el-icon :size="32" color="#409eff"><component :is="entry.icon" /></el-icon>
            <div class="quick-title">{{ entry.title }}</div>
            <div class="quick-desc">{{ entry.desc }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<style scoped>
.welcome {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #409eff 0%, #667eea 100%);
  border: none;
}

.welcome :deep(.el-card__body) {
  padding: 24px;
}

.welcome-content h2 {
  color: #fff;
  margin-bottom: 8px;
}

.welcome-content p {
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
}

.stat-row {
  margin-bottom: 4px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-card-body {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.quick-card {
  margin-bottom: 20px;
}

.quick-item {
  text-align: center;
  padding: 24px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.quick-item:hover {
  background-color: #ecf5ff;
}

.quick-title {
  margin-top: 12px;
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

.quick-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.mb-20 {
  margin-bottom: 20px;
}
</style>
