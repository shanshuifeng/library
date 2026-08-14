<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getReservationList, markReservationReady, pickupReservation } from '@/api/reservation'
import { formatDate } from '@/utils'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ status: '', page: 1, per_page: 10 })

const statusLabels = {
  pending: '待处理',
  ready: '可借阅',
  cancelled: '已取消',
  picked_up: '已取书',
  expired: '已过期'
}
const statusTagTypes = {
  pending: 'warning',
  ready: 'success',
  cancelled: 'info',
  picked_up: '',
  expired: 'danger'
}
const statusOptions = [
  { label: '全部', value: '' },
  { label: '待处理', value: 'pending' },
  { label: '可借阅', value: 'ready' },
  { label: '已取消', value: 'cancelled' },
  { label: '已取书', value: 'picked_up' },
  { label: '已过期', value: 'expired' }
]

async function loadList() {
  loading.value = true
  try {
    const res = await getReservationList(query)
    const d = res.data || {}
    list.value = d.items || []
    total.value = d.total || 0
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

async function handleReady(row) {
  try {
    await markReservationReady(row.id)
    ElMessage.success('已标记为可借阅')
    loadList()
  } catch { /* 已提示 */ }
}

async function handlePickup(row) {
  try {
    await ElMessageBox.confirm(`确认《${row.book_title}》已被用户取走？`, '取书确认', { type: 'info' })
    await pickupReservation(row.id)
    ElMessage.success('取书成功，已转为借阅记录')
    loadList()
  } catch { /* 取消 */ }
}

function handleSearch() { query.page = 1; loadList() }
function handlePageChange(page) { query.page = page; loadList() }

onMounted(loadList)
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="mb-20">
      <el-form :inline="true" :model="query" @submit.prevent>
        <el-form-item label="状态">
          <el-select v-model="query.status" style="width: 140px" @change="handleSearch">
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" stripe style="width: 100%">
        <el-table-column prop="real_name" label="读者" width="100" />
        <el-table-column prop="book_title" label="图书" min-width="180" />
        <el-table-column label="预约时间" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="过期时间" width="160">
          <template #default="{ row }">{{ formatDate(row.expiry_date) || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagTypes[row.status]">{{ statusLabels[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" type="primary" link @click="handleReady(row)">标记就绪</el-button>
            <el-button v-if="row.status === 'ready'" type="success" link @click="handlePickup(row)">确认取书</el-button>
            <span v-else class="text-muted">-</span>
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
  </div>
</template>

<style scoped>
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-muted { color: #c0c4cc; }
.mb-20 { margin-bottom: 20px; }
</style>
