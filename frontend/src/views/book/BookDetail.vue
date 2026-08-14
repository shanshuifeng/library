<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getBookDetail } from '@/api/book'
import { borrowBook } from '@/api/borrow'
import { createReservation } from '@/api/reservation'
import { useUserStore } from '@/store/user'
import { stockTagType, formatDate, formatMoney } from '@/utils'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const borrowing = ref(false)
const book = ref({})

// Mock 详情数据（按 id 给出合理内容）
function mockDetail(id) {
  return {
    id: Number(id),
    title: '深入理解计算机系统',
    author: 'Randal E. Bryant / David R. O\'Hallaron',
    isbn: '978-7-111-54493-7',
    category_name: '计算机科学',
    publisher: '机械工业出版社',
    publish_date: '2016-11-01',
    price: 139,
    stock: 8,
    description:
      '本书从程序员的视角，讲解计算机系统的工作原理，涵盖数据的机器级表示、处理器体系结构、优化程序性能、存储器层次结构、链接、异常控制流、虚拟内存、系统级 I/O、网络与并发编程等内容，是程序员的经典必读书目。',
    cover_image: ''
  }
}

async function loadDetail() {
  loading.value = true
  try {
    const res = await getBookDetail(route.params.id)
    book.value = res.data || {}
  } catch {
    // 仅开发环境使用 Mock 数据，生产环境显示空数据
    if (import.meta.env.DEV) {
      book.value = mockDetail(route.params.id)
    } else {
      book.value = {}
    }
  } finally {
    loading.value = false
  }
}

async function handleBorrow() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再借阅')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  if (book.value.stock <= 0) {
    ElMessage.warning('库存不足，暂不可借阅')
    return
  }
  try {
    await ElMessageBox.confirm(`确认借阅《${book.value.title}》？`, '借阅确认', {
      type: 'info',
      confirmButtonText: '确认借阅',
      cancelButtonText: '取消'
    })
    borrowing.value = true
    await borrowBook({ book_id: book.value.id })
    ElMessage.success('借阅成功！借期 30 天，请按时归还')
    book.value.stock -= 1
  } catch (err) {
    // 取消或接口失败（失败时拦截器已提示）
  } finally {
    borrowing.value = false
  }
}

async function handleReserve() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再预约')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  try {
    await createReservation({ book_id: book.value.id })
    ElMessage.success('预约成功！请等待通知后到馆取书')
  } catch { /* 已提示 */ }
}

onMounted(loadDetail)
</script>

<template>
  <div class="page-container" v-loading="loading">
    <el-page-header content="图书详情" @back="router.back()" class="mb-20" />

    <el-card shadow="never">
      <div class="detail-wrapper">
        <!-- 封面 -->
        <div class="cover">
          <el-image
            v-if="book.cover_image"
            :src="book.cover_image"
            fit="cover"
            style="width: 200px; height: 280px; border-radius: 6px"
          />
          <div v-else class="cover-placeholder">
            <el-icon :size="60"><Picture /></el-icon>
            <span>暂无封面</span>
          </div>
        </div>

        <!-- 信息 -->
        <div class="info">
          <h1 class="title">{{ book.title }}</h1>
          <el-descriptions :column="2" border class="mb-20">
            <el-descriptions-item label="作者">{{ book.author }}</el-descriptions-item>
            <el-descriptions-item label="ISBN">{{ book.isbn }}</el-descriptions-item>
            <el-descriptions-item label="分类">{{ book.category_name }}</el-descriptions-item>
            <el-descriptions-item label="出版社">{{ book.publisher }}</el-descriptions-item>
            <el-descriptions-item label="馆藏位置">
              {{ book.location || '未设置' }}
            </el-descriptions-item>
            <el-descriptions-item label="出版日期">
              {{ formatDate(book.publish_date) }}
            </el-descriptions-item>
            <el-descriptions-item label="价格">{{ formatMoney(book.price) }}</el-descriptions-item>
            <el-descriptions-item label="库存">
              <el-tag :type="stockTagType(book.stock)" effect="light">
                剩余 {{ book.stock }} 本
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>

          <div class="description">
            <h3>内容简介</h3>
            <p>{{ book.description }}</p>
          </div>

          <div class="actions">
            <el-button
              type="primary"
              size="large"
              :icon="'Reading'"
              :loading="borrowing"
              :disabled="book.stock <= 0"
              @click="handleBorrow"
            >
              {{ book.stock > 0 ? '立即借阅' : '暂无库存' }}
            </el-button>
            <el-button
              size="large"
              :icon="'Timer'"
              @click="handleReserve"
            >预约到馆取书</el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.detail-wrapper {
  display: flex;
  gap: 32px;
}

.cover {
  flex-shrink: 0;
}

.cover-placeholder {
  width: 200px;
  height: 280px;
  border-radius: 6px;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #c0c4cc;
}

.info {
  flex: 1;
  min-width: 0;
}

.title {
  font-size: 22px;
  margin-bottom: 20px;
  color: #303133;
}

.description h3 {
  margin: 20px 0 8px;
  font-size: 16px;
  color: #303133;
}

.description p {
  color: #606266;
  line-height: 1.8;
}

.actions {
  margin-top: 24px;
}

.mb-20 {
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .detail-wrapper {
    flex-direction: column;
    align-items: center;
  }
}
</style>
