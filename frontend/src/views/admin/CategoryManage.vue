<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getCategoryTree,
  createCategory,
  updateCategory,
  deleteCategory
} from '@/api/category'

const loading = ref(false)
const treeData = ref([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitting = ref(false)
const formRef = ref()

function createEmptyForm() {
  return { id: null, name: '', parent_id: 0, sort_order: 0 }
}

const form = reactive(createEmptyForm())
const rules = {
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }]
}

// 顶级分类作为可选父级（限制最多 2 级）
const parentOptions = computed(() =>
  treeData.value.map((c) => ({ label: c.name, value: c.id }))
)

const mockTree = [
  {
    id: 1,
    name: '计算机',
    parent_id: 0,
    sort_order: 1,
    children: [
      { id: 11, name: '编程语言', parent_id: 1, sort_order: 1 },
      { id: 12, name: '操作系统', parent_id: 1, sort_order: 2 }
    ]
  },
  { id: 2, name: '文学', parent_id: 0, sort_order: 2 },
  { id: 3, name: '数学', parent_id: 0, sort_order: 3 }
]

async function loadTree() {
  loading.value = true
  try {
    const res = await getCategoryTree()
    treeData.value = res.data || []
  } catch {
    // 仅开发环境使用 Mock 数据
    if (import.meta.env.DEV) {
      treeData.value = mockTree
    } else {
      treeData.value = []
    }
  } finally {
    loading.value = false
  }
}

function handleAdd(parent = null) {
  Object.assign(form, createEmptyForm())
  form.parent_id = parent ? parent.id : 0
  dialogTitle.value = parent ? `新增子分类（父级：${parent.name}）` : '新增分类'
  dialogVisible.value = true
}

function handleEdit(row) {
  Object.assign(form, createEmptyForm(), row)
  dialogTitle.value = '编辑分类'
  dialogVisible.value = true
}

async function handleSubmit() {
  try {
    await formRef.value.validate()
    submitting.value = true
    if (form.id) {
      await updateCategory(form.id, form)
      ElMessage.success('更新成功')
    } else {
      await createCategory(form)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadTree()
  } catch {
    // 校验或接口失败
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除分类「${row.name}」？子分类将一并删除`,
      '删除确认',
      { type: 'warning' }
    )
    await deleteCategory(row.id)
    ElMessage.success('删除成功')
    loadTree()
  } catch {
    // 取消
  }
}

onMounted(loadTree)
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="mb-20">
      <div class="toolbar">
        <span class="title">分类管理（树形结构，最多 2 级）</span>
        <div>
          <el-button :icon="'Refresh'" @click="loadTree">刷新</el-button>
          <el-button type="primary" :icon="'Plus'" @click="handleAdd()">新增顶级分类</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="treeData"
        row-key="id"
        :tree-props="{ children: 'children' }"
        default-expand-all
        border
        style="width: 100%"
      >
        <el-table-column prop="name" label="分类名称" min-width="220" />
        <el-table-column prop="sort_order" label="排序" width="120" align="center" />
        <el-table-column label="操作" width="260" align="center">
          <template #default="{ row }">
            <el-button type="primary" link :icon="'Plus'" @click="handleAdd(row)">
              添加子项
            </el-button>
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="父级分类">
          <el-select
            v-model="form.parent_id"
            placeholder="无（顶级分类）"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="opt in parentOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" style="width: 100%" />
        </el-form-item>
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
}

.title {
  font-size: 16px;
  font-weight: 500;
}

.mb-20 {
  margin-bottom: 20px;
}
</style>
