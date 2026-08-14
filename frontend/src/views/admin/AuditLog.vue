<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAuditLogs, getAuditLogDetail, getAuditStats, cleanupAuditLogs } from '@/api/audit'
import { formatDate } from '@/utils'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const stats = ref({})
const detailVisible = ref(false)
const currentLog = ref(null)

const query = reactive({
  page: 1,
  per_page: 20,
  action: '',
  resource_type: '',
  status: '',
  keyword: '',
  start_date: '',
  end_date: ''
})

// 操作类型选项
const actionOptions = [
  { label: '全部', value: '' },
  { label: '登录', value: 'login' },
  { label: '注册', value: 'register' },
  { label: '修改密码', value: 'change_password' },
  { label: '创建', value: 'create' },
  { label: '更新', value: 'update' },
  { label: '删除', value: 'delete' },
  { label: '借书', value: 'borrow' },
  { label: '还书', value: 'return' },
  { label: '续借', value: 'renew' },
  { label: '预约', value: 'reservation' }
]

// 状态选项
const statusOptions = [
  { label: '全部', value: '' },
  { label: '成功', value: 'success' },
  { label: '失败', value: 'failed' },
  { label: '错误', value: 'error' }
]

// 资源类型选项
const resourceOptions = [
  { label: '全部', value: '' },
  { label: '用户', value: 'user' },
  { label: '图书', value: 'book' },
  { label: '借阅', value: 'borrow' },
  { label: '预约', value: 'reservation' },
  { label: '分类', value: 'category' },
  { label: '权限', value: 'permission' }
]

// 操作标签颜色
const actionTagType = {
  login: 'primary',
  register: 'success',
  change_password: 'warning',
  create: 'success',
  update: 'primary',
  delete: 'danger',
  borrow: 'primary',
  return: 'success',
  renew: 'warning',
  reservation: 'info'
}

// 状态标签颜色
const statusTagType = {
  success: 'success',
  failed: 'warning',
  error: 'danger'
}

async function loadStats() {
  try {
    const res = await getAuditStats()
    stats.value = res.data || {}
  } catch {
    // 忽略
  }
}

async function loadList() {
  loading.value = true
  try {
    const params = { ...query }
    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    const res = await getAuditLogs(params)
    const data = res.data || {}
    list.value = data.items || data.list || []
    total.value = data.total || 0
  } catch {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  query.page = 1
  loadList()
}

function handleReset() {
  Object.assign(query, {
    page: 1,
    action: '',
    resource_type: '',
    status: '',
    keyword: '',
    start_date: '',
    end_date: ''
  })
  loadList()
}

async function handleViewDetail(row) {
  try {
    const res = await getAuditLogDetail(row.id)
    currentLog.value = res.data || row
    detailVisible.value = true
  } catch {
    currentLog.value = row
    detailVisible.value = true
  }
}

async function handleCleanup() {
  try {
    await ElMessageBox.confirm(
      '确认清理90天前的审计日志？此操作不可恢复。',
      '清理确认',
      { type: 'warning' }
    )
    const res = await cleanupAuditLogs()
    ElMessage.success(res.message || '清理成功')
    loadList()
    loadStats()
  } catch {
    // 取消
  }
}

function handlePageChange(page) {
  query.page = page
  loadList()
}

onMounted(() => {
  loadList()
  loadStats()
})
</script>

<template>
  <div class="page-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="mb-20">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ stats.total_count || 0 }}</div>
            <div class="stat-label">总日志数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ stats.today_count || 0 }}</div>
            <div class="stat-label">今日操作</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ stats.action_stats?.length || 0 }}</div>
            <div class="stat-label">操作类型数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ stats.user_stats?.length || 0 }}</div>
            <div class="stat-label">活跃用户数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索区 -->
    <el-card shadow="never" class="mb-20">
      <el-form :inline="true" :model="query" @submit.prevent>
        <el-form-item label="操作类型">
          <el-select v-model="query.action" style="width: 120px" clearable>
            <el-option v-for="o in actionOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="资源类型">
          <el-select v-model="query.resource_type" style="width: 120px" clearable>
            <el-option v-for="o in resourceOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" style="width: 100px" clearable>
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="搜索详情/用户名" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="query.start_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="开始日期"
            style="width: 140px"
          />
          <span style="margin: 0 8px">-</span>
          <el-date-picker
            v-model="query.end_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="结束日期"
            style="width: 140px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="danger" @click="handleCleanup">清理旧日志</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志列表 -->
    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="操作类型" width="110">
          <template #default="{ row }">
            <el-tag :type="actionTagType[row.action] || 'info'" size="small">
              {{ row.action }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resource_type" label="资源类型" width="100" />
        <el-table-column prop="resource_id" label="资源ID" width="80" />
        <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip />
        <el-table-column prop="username" label="操作人" width="100" />
        <el-table-column prop="ip_address" label="IP地址" width="130" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="statusTagType[row.status] || 'info'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="query.page"
          :page-size="query.per_page"
          :total="total"
          layout="total, prev, pager, next, jumper"
          background
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="审计日志详情" width="700px">
      <el-descriptions :column="2" border v-if="currentLog">
        <el-descriptions-item label="日志ID">{{ currentLog.id }}</el-descriptions-item>
        <el-descriptions-item label="操作类型">
          <el-tag :type="actionTagType[currentLog.action]">{{ currentLog.action }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="资源类型">{{ currentLog.resource_type }}</el-descriptions-item>
        <el-descriptions-item label="资源ID">{{ currentLog.resource_id }}</el-descriptions-item>
        <el-descriptions-item label="操作人">{{ currentLog.username || '-' }}</el-descriptions-item>
        <el-descriptions-item label="用户ID">{{ currentLog.user_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentLog.ip_address }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTagType[currentLog.status]">{{ currentLog.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="请求方法">{{ currentLog.request_method }}</el-descriptions-item>
        <el-descriptions-item label="请求路径" :span="2">{{ currentLog.request_path }}</el-descriptions-item>
        <el-descriptions-item label="操作详情" :span="2">{{ currentLog.detail }}</el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2" v-if="currentLog.error_message">
          <span style="color: #f56c6c">{{ currentLog.error_message }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="操作时间" :span="2">{{ currentLog.created_at }}</el-descriptions-item>
      </el-descriptions>

      <!-- 数据变更 -->
      <div v-if="currentLog?.old_value || currentLog?.new_value" style="margin-top: 20px">
        <h4>数据变更</h4>
        <el-row :gutter="20">
          <el-col :span="12" v-if="currentLog.old_value">
            <div class="diff-label">变更前</div>
            <pre class="diff-content old">{{ JSON.stringify(currentLog.old_value, null, 2) }}</pre>
          </el-col>
          <el-col :span="12" v-if="currentLog.new_value">
            <div class="diff-label">变更后</div>
            <pre class="diff-content new">{{ JSON.stringify(currentLog.new_value, null, 2) }}</pre>
          </el-col>
        </el-row>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.stat-item {
  text-align: center;
  padding: 10px 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.mb-20 {
  margin-bottom: 20px;
}

.diff-label {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #606266;
}

.diff-content {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  font-size: 12px;
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.diff-content.old {
  background: #fef0f0;
  border-color: #fbc4c4;
}

.diff-content.new {
  background: #f0f9eb;
  border-color: #c2e7b0;
}
</style>
