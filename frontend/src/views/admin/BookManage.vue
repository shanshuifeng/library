<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getBookList, createBook, updateBook, deleteBook, uploadCover } from '@/api/book'
import { getCategoryTree } from '@/api/category'
import { stockTagType, formatDate } from '@/utils'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const categoryOptions = ref([])
const selectedRows = ref([])

const query = reactive({ keyword: '', page: 1, per_page: 10 })

// 弹窗表单
const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitting = ref(false)
const formRef = ref()
const form = reactive(createEmptyForm())

function createEmptyForm() {
  return {
    id: null,
    title: '',
    author: '',
    isbn: '',
    category_id: '',
    publisher: '',
    publish_date: '',
    price: 0,
    stock: 0,
    location: '',
    description: '',
    cover_image: ''
  }
}

const rules = {
  title: [{ required: true, message: '请输入书名', trigger: 'blur' }],
  author: [{ required: true, message: '请输入作者', trigger: 'blur' }],
  isbn: [{ required: true, message: '请输入 ISBN', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
  publish_date: [{ required: true, message: '请选择出版日期', trigger: 'change' }]
}

const mockBooks = [
  { id: 1, title: '深入理解计算机系统', author: 'Randal E. Bryant', isbn: '978-7-111-54493-7', category_name: '计算机', publisher: '机械工业出版社', publish_date: '2016-11-01', price: 139, stock: 8 },
  { id: 2, title: '算法导论', author: 'Thomas H. Cormen', isbn: '978-7-111-40701-0', category_name: '计算机', publisher: '机械工业出版社', publish_date: '2013-01-01', price: 128, stock: 2 },
  { id: 3, title: '高等数学', author: '同济大学', isbn: '978-7-04-039663-8', category_name: '数学', publisher: '高等教育出版社', publish_date: '2014-07-01', price: 58, stock: 0 }
]

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
  } catch {
    // 仅开发环境使用 Mock 数据
    if (import.meta.env.DEV) {
      list.value = mockBooks.filter(
        (b) => !query.keyword || b.title.includes(query.keyword)
      )
      total.value = list.value.length
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

function handleAdd() {
  Object.assign(form, createEmptyForm())
  dialogTitle.value = '新增图书'
  dialogVisible.value = true
}

function handleEdit(row) {
  Object.assign(form, createEmptyForm(), row)
  dialogTitle.value = '编辑图书'
  dialogVisible.value = true
}

const coverUploading = ref(false)

async function handleCoverUpload(file) {
  coverUploading.value = true
  try {
    const res = await uploadCover(file)
    form.cover_image = res.data?.cover_image || ''
    ElMessage.success('封面上传成功')
  } catch {
    ElMessage.error('封面上传失败')
  } finally {
    coverUploading.value = false
  }
  return false // 阻止默认上传行为
}

async function handleSubmit() {
  try {
    await formRef.value.validate()
    submitting.value = true
    if (form.id) {
      await updateBook(form.id, form)
      ElMessage.success('更新成功')
    } else {
      await createBook(form)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadList()
  } catch {
    // 校验或接口失败
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除《${row.title}》？删除后不可恢复`, '删除确认', {
      type: 'warning'
    })
    await deleteBook(row.id)
    ElMessage.success('删除成功')
    loadList()
  } catch {
    // 取消
  }
}

function handleSelectionChange(rows) {
  selectedRows.value = rows
}

async function handleBatchDelete() {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择要删除的图书')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认删除选中的 ${selectedRows.value.length} 本图书？`,
      '批量删除',
      { type: 'warning' }
    )
    await Promise.all(selectedRows.value.map((r) => deleteBook(r.id)))
    ElMessage.success('批量删除成功')
    loadList()
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
  loadCategories()
})
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="mb-20">
      <div class="toolbar">
        <el-form :inline="true" :model="query" @submit.prevent>
          <el-form-item>
            <el-input
              v-model="query.keyword"
              placeholder="书名搜索"
              clearable
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="'Search'" @click="handleSearch">查询</el-button>
          </el-form-item>
        </el-form>
        <div>
          <el-button type="primary" :icon="'Plus'" @click="handleAdd">新增图书</el-button>
          <el-button type="danger" :icon="'Delete'" @click="handleBatchDelete">批量删除</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="list"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="title" label="书名" min-width="180" />
        <el-table-column prop="author" label="作者" width="140" />
        <el-table-column prop="isbn" label="ISBN" width="160" />
        <el-table-column prop="category_name" label="分类" width="100" />
        <el-table-column label="库存" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="stockTagType(row.stock)" effect="light">{{ row.stock }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="price" label="价格" width="90" align="right">
          <template #default="{ row }">¥{{ Number(row.price || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="出版日期" width="120">
          <template #default="{ row }">{{ formatDate(row.publish_date) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="640px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="书名" prop="title">
              <el-input v-model="form.title" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="作者" prop="author">
              <el-input v-model="form.author" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="ISBN" prop="isbn">
              <el-input v-model="form.isbn" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类" prop="category_id">
              <el-select v-model="form.category_id" placeholder="选择分类" style="width: 100%">
                <el-option
                  v-for="c in categoryOptions"
                  :key="c.value"
                  :label="c.label"
                  :value="c.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="出版社">
              <el-input v-model="form.publisher" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="出版日期" prop="publish_date">
              <el-date-picker
                v-model="form.publish_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="选择日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="价格">
              <el-input-number v-model="form.price" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="库存">
              <el-input-number v-model="form.stock" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="馆藏位置">
              <el-input v-model="form.location" placeholder="如：A区-3楼-05架" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="封面图片">
              <div class="cover-upload">
                <el-upload
                  :show-file-list="false"
                  :before-upload="handleCoverUpload"
                  accept="image/jpeg,image/png,image/gif,image/webp"
                >
                  <el-button :loading="coverUploading" type="primary">
                    {{ coverUploading ? '上传中...' : '选择图片上传' }}
                  </el-button>
                </el-upload>
                <div v-if="form.cover_image" class="cover-preview">
                  <img :src="form.cover_image" alt="封面预览" />
                  <el-button type="danger" link size="small" @click="form.cover_image = ''">
                    移除
                  </el-button>
                </div>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="简介">
              <el-input v-model="form.description" type="textarea" :rows="3" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.mb-20 {
  margin-bottom: 20px;
}

.cover-upload {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.cover-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.cover-preview img {
  max-width: 120px;
  max-height: 160px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  object-fit: cover;
}
</style>
