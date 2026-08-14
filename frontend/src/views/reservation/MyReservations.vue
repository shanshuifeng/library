<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMyReservations, cancelReservation } from '@/api/reservation'
import { formatDate } from '@/utils'

const loading = ref(false)
const list = ref([])
const query = ref({ page: 1, per_page: 20 })
const total = ref(0)

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

async function loadList() {
  loading.value = true
  try {
    const res = await getMyReservations(query.value)
    const d = res.data || {}
    list.value = d.items || []
    total.value = d.total || 0
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

async function handleCancel(row) {
  try {
    await ElMessageBox.confirm('确定取消该预约？', '提示', { type: 'warning' })
    await cancelReservation(row.id)
    ElMessage.success('预约已取消')
    loadList()
  } catch { /* 取消 */ }
}

function handlePageChange(page) {
  query.value.page = page
  loadList()
}

onMounted(loadList)
</script>

<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header><span>我的预约</span></template>
      <el-table v-loading="loading" :data="list" stripe style="width: 100%">
        <el-table-column prop="book_title" label="图书" min-width="180" />
        <el-table-column prop="book_author" label="作者" width="140" />
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
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending' || row.status === 'ready'"
              type="danger" link @click="handleCancel(row)"
            >取消预约</el-button>
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
</style>
