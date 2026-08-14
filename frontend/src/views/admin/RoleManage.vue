<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRoles, getRoleDetail, createRole, updateRole, deleteRole, getPermissions } from '@/api/permission'

const loading = ref(false)
const roles = ref([])
const permissions = ref({})

const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitting = ref(false)
const formRef = ref()
const form = ref({ name: '', description: '', permission_ids: [] })

async function loadRoles() {
  loading.value = true
  try {
    const [roleRes, permRes] = await Promise.all([getRoles(), getPermissions()])
    roles.value = roleRes.data || []
    permissions.value = permRes.data || {}
  } catch { /* 已提示 */ }
  finally { loading.value = false }
}

function handleAdd() {
  form.value = { name: '', description: '', permission_ids: [] }
  dialogTitle.value = '新增角色'
  dialogVisible.value = true
}

async function handleEdit(row) {
  try {
    const res = await getRoleDetail(row.id)
    const d = res.data || {}
    form.value = {
      id: d.id,
      name: d.name,
      description: d.description || '',
      permission_ids: (d.permissions || []).map(p => p.id)
    }
    dialogTitle.value = '编辑角色'
    dialogVisible.value = true
  } catch { /* 已提示 */ }
}

async function handleSubmit() {
  try {
    submitting.value = true
    if (form.value.id) {
      await updateRole(form.value.id, {
        name: form.value.name,
        description: form.value.description,
        permission_ids: form.value.permission_ids
      })
      ElMessage.success('角色更新成功')
    } else {
      await createRole({
        name: form.value.name,
        description: form.value.description,
        permission_ids: form.value.permission_ids
      })
      ElMessage.success('角色创建成功')
    }
    dialogVisible.value = false
    loadRoles()
  } catch { /* 已提示 */ }
  finally { submitting.value = false }
}

async function handleDelete(row) {
  if (row.is_system) {
    ElMessage.warning('系统角色不可删除')
    return
  }
  try {
    await ElMessageBox.confirm(`确认删除角色「${row.name}」？`, '删除确认', { type: 'warning' })
    await deleteRole(row.id)
    ElMessage.success('角色已删除')
    loadRoles()
  } catch { /* 取消 */ }
}

function togglePermission(permId) {
  const idx = form.value.permission_ids.indexOf(permId)
  if (idx >= 0) form.value.permission_ids.splice(idx, 1)
  else form.value.permission_ids.push(permId)
}

onMounted(loadRoles)
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="mb-20">
      <div class="toolbar">
        <span class="title">角色管理</span>
        <el-button type="primary" @click="handleAdd">新增角色</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="roles" stripe style="width: 100%">
        <el-table-column prop="name" label="角色名" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_system" type="danger">{{ row.name }}</el-tag>
            <span v-else>{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="permission_count" label="权限数" width="100" align="center" />
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑权限</el-button>
            <el-button type="danger" link :disabled="row.is_system" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="640px">
      <el-form ref="formRef" :model="form" label-width="80px">
        <el-form-item label="角色名" prop="name" :rules="[{ required: true, message: '请输入角色名' }]">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="权限">
          <div v-for="(perms, group) in permissions" :key="group" class="perm-group">
            <div class="perm-group-title">{{ group }}</div>
            <el-checkbox-group v-model="form.permission_ids">
              <el-checkbox
                v-for="p in perms"
                :key="p.id"
                :label="p.id"
                :value="p.id"
              >{{ p.name }}</el-checkbox>
            </el-checkbox-group>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; }
.title { font-size: 16px; font-weight: 500; }
.perm-group { margin-bottom: 12px; }
.perm-group-title { font-weight: 500; color: #409eff; margin-bottom: 6px; font-size: 14px; }
.mb-20 { margin-bottom: 20px; }
</style>
