<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getBookList } from '@/api/book'
import { getCategoryTree } from '@/api/category'
import { createReservation } from '@/api/reservation'
import { useUserStore } from '@/store/user'
import { stockTagType, formatDate, formatMoney } from '@/utils'

const userStore = useUserStore()

const router = useRouter()

const loading = ref(false)
const list = ref([])
const total = ref(0)
const categoryOptions = ref([])
const isMock = ref(false)

const query = reactive({
  keyword: '',
  category_id: '',
  page: 1,
  per_page: 10
})

// 后端未就绪时的演示数据
const mockBooks = [
  { id: 1, title: '深入理解计算机系统', author: 'Randal E. Bryant', isbn: '978-7-111-54493-7', category_name: '计算机', price: 139, stock: 8, publish_date: '2016-11-01', publisher: '机械工业出版社', cover_image: '' },
  { id: 2, title: '算法导论', author: 'Thomas H. Cormen', isbn: '978-7-111-40701-0', category_name: '计算机', price: 128, stock: 2, publish_date: '2013-01-01', publisher: '机械工业出版社', cover_image: '' },
  { id: 3, title: '高等数学（第七版）', author: '同济大学数学系', isbn: '978-7-04-039663-8', category_name: '数学', price: 58, stock: 0, publish_date: '2014-07-01', publisher: '高等教育出版社', cover_image: '' },
  { id: 4, title: '百年孤独', author: '加西亚·马尔克斯', isbn: '978-7-5442-5399-4', category_name: '文学', price: 39.5, stock: 5, publish_date: '2017-06-01', publisher: '南海出版公司', cover_image: '' },
  { id: 5, title: '人类简史', author: '尤瓦尔·赫拉利', isbn: '978-7-5086-6296-7', category_name: '历史', price: 68, stock: 12, publish_date: '2017-02-01', publisher: '中信出版社', cover_image: '' },
  { id: 6, title: 'Python 编程：从入门到实践', author: 'Eric Matthes', isbn: '978-7-115-42260-2', category_name: '计算机', price: 89, stock: 1, publish_date: '2016-07-01', publisher: '人民邮电出版社', cover_image: '' }
]

// 扁平化分类树为下拉选项
function flatten(tree, result = []) {
  for (const node of tree || []) {
    result.push({ label: node.name, value: node.id })
    if (node.children?.length) flatten(node.children, result)
  }
  return result
}

async function loadList() {
  loading.value = true
  try {
    const res = await getBookList(query)
    const data = res.data || {}
    list.value = data.items || data.list || []
    total.value = data.total || 0
    isMock.value = false
  } catch {
    // 仅开发环境使用 Mock 数据，生产环境显示错误
    if (import.meta.env.DEV) {
      list.value = mockBooks.filter(
        (b) =>
          !query.keyword ||
          b.title.includes(query.keyword) ||
          b.author.includes(query.keyword) ||
          b.isbn.includes(query.keyword)
      )
      total.value = list.value.length
      isMock.value = true
    } else {
      list.value = []
      total.value = 0
    }
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  try {
    const res = await getCategoryTree()
    categoryOptions.value = flatten(res.data)
  } catch {
    categoryOptions.value = []
  }
}

function handleSearch() {
  query.page = 1
  loadList()
}

function handleReset() {
  query.keyword = ''
  query.category_id = ''
  query.page = 1
  loadList()
}

function handlePageChange(page) {
  query.page = page
  loadList()
}

function goDetail(row) {
  router.push(`/books/${row.id}`)
}

async function handleReserve(row) {
  try {
    await createReservation({ book_id: row.id })
    ElMessage.success('预约成功，请等待通知后到馆取书')
  } catch { /* 已提示 */ }
}

onMounted(() => {
  loadList()
  loadCategories()
})
</script>

<template>
  <div class="page-container">
    <el-alert
      v-if="isMock"
      title="当前为演示数据（后端接口未就绪）"
      type="info"
      :closable="false"
      show-icon
      class="mb-20"
    />

    <!-- 搜索区 -->
    <el-card shadow="never" class="mb-20">
      <el-form :inline="true" :model="query" @submit.prevent>
        <el-form-item label="关键字">
          <el-input
            v-model="query.keyword"
            placeholder="书名 / 作者 / ISBN"
            clearable
            style="width: 220px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="分类">
          <el-select
            v-model="query.category_id"
            placeholder="全部分类"
            clearable
            style="width: 160px"
          >
            <el-option
              v-for="c in categoryOptions"
              :key="c.value"
              :label="c.label"
              :value="c.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="'Search'" @click="handleSearch">查询</el-button>
          <el-button :icon="'Refresh'" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 图书列表 -->
    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" stripe style="width: 100%">
        <el-table-column label="书名" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="goDetail(row)">{{ row.title }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="author" label="作者" width="140" />
        <el-table-column prop="isbn" label="ISBN" width="160" />
        <el-table-column prop="category_name" label="分类" width="100" />
        <el-table-column prop="publisher" label="出版社" width="130" />
        <el-table-column prop="location" label="馆藏位置" width="120" />
        <el-table-column label="库存" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="stockTagType(row.stock)" effect="light">{{ row.stock }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="价格" width="80" align="right">
          <template #default="{ row }">{{ formatMoney(row.price) }}</template>
        </el-table-column>
        <el-table-column label="出版日期" width="110">
          <template #default="{ row }">{{ formatDate(row.publish_date) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="goDetail(row)">详情</el-button>
            <el-button
              v-if="userStore.isLoggedIn"
              type="success" link
              :disabled="row.stock <= 0"
              @click="handleReserve(row)"
            >预约</el-button>
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

.mb-20 {
  margin-bottom: 20px;
}
</style>
