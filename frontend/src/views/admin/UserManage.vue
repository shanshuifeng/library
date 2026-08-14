<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserList, createUser, updateUser, deleteUser } from '@/api/user'
import { getRoles, getUserRoles, setUserRoles } from '@/api/permission'
import { ROLE_OPTIONS, ROLE_LABELS, ROLE_TAG_TYPE, formatDate } from '@/utils'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ keyword: '', role: '', page: 1, per_page: 10 })

const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitting = ref(false)
const formRef = ref()

function createEmptyForm() {
  return {
    id: null,
    username: '',
    password: '',
    email: '',
    phone: '',
    role: 'student',
    status: 1
  }
}

const form = reactive(createEmptyForm())

// 编辑时密码非必填（留空表示不修改），新增时必填
const rules = computed(() => ({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度 3-20 个字符', trigger: 'blur' }
  ],
  password: form.id ? [] : [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}))

const mockUsers = [
  { id: 1, username: 'admin', email: 'admin@lib.edu', phone: '13800000000', role: 'admin', status: 1, created_at: '2026-01-01' },
  { id: 2, username: 'teacher01', email: 't01@lib.edu', phone: '13800000001', role: 'teacher', status: 1, created_at: '2026-02-01' },
  { id: 3, username: 'student01', email: 's01@lib.edu', phone: '13800000002', role: 'student', status: 0, created_at: '2026-03-01' }
]

async function loadList() {
  loading.value = true
  try {
    const res = await getUserList(query)
    const data = res.data || {}
    list.value = data.items || data.list || []
    total.value = data.total || 0
  } catch {
    // 仅开发环境使用 Mock 数据
    if (import.meta.env.DEV) {
      list.value = mockUsers.filter(
        (u) => (!query.role || u.role === query.role) && (!query.keyword || u.username.includes(query.keyword))
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

function handleSearch() {
  query.page = 1
  loadList()
}

function handleAdd() {
  Object.assign(form, createEmptyForm())
  dialogTitle.value = '新增用户'
  dialogVisible.value = true
}

function handleEdit(row) {
  Object.assign(form, createEmptyForm(), row, { password: '' })
  // 编辑时密码非必填
  dialogTitle.value = '编辑用户'
  dialogVisible.value = true
}

async function handleSubmit() {
  try {
    await formRef.value.validate()
    submitting.value = true
    // 构造提交数据：编辑且未填密码时不下发 password 字段
    const payload = { ...form }
    if (form.id && !payload.password) {
      delete payload.password
    }
    if (form.id) {
      await updateUser(form.id, payload)
      ElMessage.success('更新成功')
    } else {
      await createUser(payload)
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
    await ElMessageBox.confirm(`确认删除用户「${row.username}」？`, '删除确认', {
      type: 'warning'
    })
    await deleteUser(row.id)
    ElMessage.success('删除成功')
    loadList()
  } catch {
    // 取消
  }
}

async function handleToggleStatus(row) {
  const action = row.status === 1 ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确认${action}用户「${row.username}」？`, '提示', {
      type: 'warning'
    })
    await updateUser(row.id, { status: row.status === 1 ? 0 : 1 })
    ElMessage.success(`${action}成功`)
    loadList()
  } catch {
    // 取消
  }
}

const roleDialogVisible = ref(false)
const roleUser = ref(null)
const allRoles = ref([])
const userRoleIds = ref([])

async function handleAssignRole(row) {
  roleUser.value = row
  try {
    const [roleRes, userRoleRes] = await Promise.all([getRoles(), getUserRoles(row.id)])
    allRoles.value = roleRes.data || []
    userRoleIds.value = (userRoleRes.data || []).map(r => r.id)
    roleDialogVisible.value = true
  } catch { /* 已提示 */ }
}

async function submitAssignRole() {
  try {
    await setUserRoles(roleUser.value.id, userRoleIds.value)
    ElMessage.success('角色分配成功')
    roleDialogVisible.value = false
  } catch { /* 已提示 */ }
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
      <div class="toolbar">
        <el-form :inline="true" :model="query" @submit.prevent>
          <el-form-item>
            <el-input
              v-model="query.keyword"
              placeholder="用户名搜索"
              clearable
              style="width: 180px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item>
            <el-select v-model="query.role" placeholder="全部角色" clearable style="width: 130px">
              <el-option
                v-for="o in ROLE_OPTIONS"
                :key="o.value"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="'Search'" @click="handleSearch">查询</el-button>
          </el-form-item>
        </el-form>
        <el-button type="primary" :icon="'Plus'" @click="handleAdd">新增用户</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" stripe style="width: 100%">
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column label="角色" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="ROLE_TAG_TYPE[row.role]">{{ ROLE_LABELS[row.role] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="120">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="primary" link @click="handleAssignRole(row)">角色</el-button>
            <el-button type="warning" link @click="handleToggleStatus(row)">
              {{ row.status === 1 ? '禁用' : '启用' }}
            </el-button>
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
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="form.id ? '留空则不修改' : '请输入密码'"
          />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option
              v-for="o in ROLE_OPTIONS"
              :key="o.value"
              :label="o.label"
              :value="o.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch
            v-model="form.status"
            :active-value="1"
            :inactive-value="0"
            active-text="正常"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 分配角色弹窗 -->
    <el-dialog v-model="roleDialogVisible" title="分配角色" width="480px">
      <p v-if="roleUser" style="margin-bottom:12px;color:#606266">
        为用户 <strong>{{ roleUser.username }}</strong> 分配角色
      </p>
      <el-checkbox-group v-model="userRoleIds">
        <el-checkbox v-for="r in allRoles" :key="r.id" :label="r.id" :value="r.id">
          {{ r.name }}
          <span style="color:#909399;font-size:12px"> - {{ r.description }}</span>
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAssignRole">保存</el-button>
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
</style>
