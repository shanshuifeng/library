<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { updateUser } from '@/api/user'
import { updatePassword } from '@/api/auth'
import { roleLabel } from '@/utils'

const userStore = useUserStore()
const activeTab = ref('info')

const infoLoading = ref(false)
const infoSubmitting = ref(false)
const infoForm = reactive({ nickname: '', email: '', phone: '' })

const pwdRef = ref()
const pwdSubmitting = ref(false)
const pwdForm = reactive({ old_password: '', new_password: '', confirm_password: '' })

const validateConfirm = (rule, value, callback) => {
  if (value !== pwdForm.new_password) callback(new Error('两次输入的密码不一致'))
  else callback()
}

const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
}

async function loadProfile() {
  infoLoading.value = true
  try {
    const profile = await userStore.fetchProfile()
    infoForm.nickname = profile.nickname || profile.username || ''
    infoForm.email = profile.email || ''
    infoForm.phone = profile.phone || ''
  } catch {
    // 使用 store 中已有信息兜底
    infoForm.nickname = userStore.displayName
  } finally {
    infoLoading.value = false
  }
}

async function handleSaveInfo() {
  infoSubmitting.value = true
  try {
    await updateUser(userStore.userId, infoForm)
    await userStore.fetchProfile()
    ElMessage.success('信息保存成功')
  } catch {
    // 失败已提示
  } finally {
    infoSubmitting.value = false
  }
}

async function handleChangePassword() {
  try {
    await pwdRef.value.validate()
    pwdSubmitting.value = true
    await updatePassword({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password
    })
    ElMessage.success('密码修改成功，请重新登录')
    pwdForm.old_password = ''
    pwdForm.new_password = ''
    pwdForm.confirm_password = ''
  } catch {
    // 校验或接口失败
  } finally {
    pwdSubmitting.value = false
  }
}

onMounted(loadProfile)
</script>

<template>
  <div class="page-container">
    <el-card shadow="never">
      <!-- 用户概要 -->
      <div class="profile-header">
        <el-avatar :size="64" icon="UserFilled" />
        <div class="profile-meta">
          <h2>{{ userStore.displayName }}</h2>
          <el-tag>{{ roleLabel(userStore.role) }}</el-tag>
        </div>
      </div>

      <el-tabs v-model="activeTab">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="info">
          <el-form
            v-loading="infoLoading"
            :model="infoForm"
            label-width="80px"
            style="max-width: 480px"
          >
            <el-form-item label="用户名">
              <el-input :value="userStore.displayName" disabled />
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="infoForm.nickname" placeholder="请输入昵称" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="infoForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="手机">
              <el-input v-model="infoForm.phone" placeholder="请输入手机号" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="infoSubmitting" @click="handleSaveInfo">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 修改密码 -->
        <el-tab-pane label="修改密码" name="password">
          <el-form
            ref="pwdRef"
            :model="pwdForm"
            :rules="pwdRules"
            label-width="90px"
            style="max-width: 480px"
          >
            <el-form-item label="原密码" prop="old_password">
              <el-input v-model="pwdForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="pwdForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input v-model="pwdForm.confirm_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="pwdSubmitting" @click="handleChangePassword">
                确认修改
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.profile-meta h2 {
  font-size: 20px;
  margin-bottom: 6px;
}
</style>
