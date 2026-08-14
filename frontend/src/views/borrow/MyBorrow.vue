<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getUserBorrows, renewBook } from '@/api/borrow'
import { useUserStore } from '@/store/user'
import {
  borrowStatusLabel,
  BORROW_STATUS_TAG_TYPE,
  formatDate,
  formatMoney
} from '@/utils'

const userStore = useUserStore()
const loading = ref(false)
const list = ref([])
const activeTab = ref('all')

const mockList = [
  { id: 2, book_title: '算法导论', borrow_date: '2026-07-01', due_date: '2026-07-31', return_date: null, status: 'borrowed', renew_count: 1, fine: 0 },
  { id: 4, book_title: '人类简史', borrow_date: '2026-05-20', due_date: '2026-06-19', return_date: '2026-06-15', status: 'returned', renew_count: 0, fine: 0 }
]

async function loadList() {
  loading.value = true
  try {
    if (!userStore.userId) {
      list.value = import.meta.env.DEV ? mockList : []
      return
    }
    const res = await getUserBorrows(userStore.userId, {})
    list.value = res.data?.items || res.data?.list || res.data || []
  } catch {
    // 仅开发环境使用 Mock 数据
    if (import.meta.env.DEV) {
      list.value = mockList
    } else {
      list.value = []
    }
  } finally {
    loading.value = false
  }
}

const filteredList = computed(() => {
  if (activeTab.value === 'all') return list.value
  return list.value.filter((r) => r.status === activeTab.value)
})

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

onMounted(loadList)
</script>

<template>
  <div class="page-container">
    <el-card shadow="never">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="借阅中" name="borrowed" />
        <el-tab-pane label="已归还" name="returned" />
        <el-tab-pane label="已逾期" name="overdue" />
      </el-tabs>

      <el-table v-loading="loading" :data="filteredList" stripe style="width: 100%">
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
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              v-if="row.status !== 'returned'"
              type="primary"
              link
              @click="handleRenew(row)"
            >
              续借
            </el-button>
            <span v-else class="text-muted">已完结</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.fine-active {
  color: #f56c6c;
  font-weight: 600;
}

.text-muted {
  color: #c0c4cc;
}
</style>
