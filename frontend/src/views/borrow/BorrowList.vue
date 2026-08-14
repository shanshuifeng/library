<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getBorrowList, returnBook, renewBook } from '@/api/borrow'
import {
  borrowStatusLabel,
  BORROW_STATUS_TAG_TYPE,
  formatDate,
  formatMoney
} from '@/utils'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ status: '', keyword: '', page: 1, per_page: 10 })

const statusOptions = [
  { label: '全部', value: '' },
  { label: '借阅中', value: 'borrowed' },
  { label: '已归还', value: 'returned' },
  { label: '已逾期', value: 'overdue' }
]

const mockList = [
  { id: 1, username: '张三', book_title: '深入理解计算机系统', borrow_date: '2026-06-01', due_date: '2026-07-01', return_date: null, status: 'overdue', renew_count: 0, fine: 1.6 },
  { id: 2, username: '李四', book_title: '算法导论', borrow_date: '2026-07-01', due_date: '2026-07-31', return_date: null, status: 'borrowed', renew_count: 1, fine: 0 },
  { id: 3, username: '王五', book_title: '百年孤独', borrow_date: '2026-06-15', due_date: '2026-07-15', return_date: '2026-07-10', status: 'returned', renew_count: 0, fine: 0 }
]

async function loadList() {
  loading.value = true
  try {
    const res = await getBorrowList(query)
    const data = res.data || {}
    list.value = data.items || data.list || []
    total.value = data.total || 0
  } catch {
    // 仅开发环境使用 Mock 数据
    if (import.meta.env.DEV) {
      list.value = mockList.filter((r) => !query.status || r.status === query.status)
      total.value = list.value.length
    } else {
      list.value = []
      total.value = 0
    }
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  query.page = 1
  loadList()
}

async function handleReturn(row) {
  try {
    await ElMessageBox.confirm(`确认归还《${row.book_title}》？`, '归还确认', {
      type: 'info'
    })
    await returnBook(row.id)
    ElMessage.success('归还成功')
    loadList()
  } catch {
    // 取消
  }
}

async function handleRenew(row) {
  if (row.renew_count >= 2) {
    ElMessage.warning('已达最大续借次数（2 次）')
    return
  }
  try {
    await renewBook(row.id)
    ElMessage.success('续借成功，借期延长 30 天')
    loadList()
  } catch {
    // 失败已提示
  }
}

function handlePageChange(page) {
  query.page = page
  loadList()
}

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
          <el-button type="primary" :icon="'Search'" @click="handleSearch">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" stripe style="width: 100%">
        <el-table-column prop="username" label="读者" width="100" />
        <el-table-column prop="book_title" label="图书" min-width="180" />
        <el-table-column label="借阅日期" width="120">
          <template #default="{ row }">{{ formatDate(row.borrow_date) }}</template>
        </el-table-column>
        <el-table-column label="应还日期" width="120">
          <template #default="{ row }">{{ formatDate(row.due_date) }}</template>
        </el-table-column>
        <el-table-column label="归还日期" width="120">
          <template #default="{ row }">{{ formatDate(row.return_date) }}</template>
        </el-table-column>
        <el-table-column label="续借次数" width="90" align="center" prop="renew_count" />
        <el-table-column label="罚款" width="90" align="right">
          <template #default="{ row }">
            <span :class="{ 'fine-active': row.fine > 0 }">{{ formatMoney(row.fine) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="BORROW_STATUS_TAG_TYPE[row.status]">
              {{ borrowStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <template v-if="row.status !== 'returned'">
              <el-button type="success" link @click="handleReturn(row)">归还</el-button>
              <el-button type="primary" link @click="handleRenew(row)">续借</el-button>
            </template>
            <span v-else class="text-muted">已完结</span>
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
.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.fine-active {
  color: #f56c6c;
  font-weight: 600;
}

.text-muted {
  color: #c0c4cc;
}

.mb-20 {
  margin-bottom: 20px;
}
</style>
