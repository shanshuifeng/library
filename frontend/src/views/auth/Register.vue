<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { register } from '@/api/auth'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

// 新用户注册统一为学生角色（后端强制 role='student'，前端不提供角色选择）
const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: ''
})

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度为 3-20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }]
}

async function handleRegister() {
  try {
    await formRef.value.validate()
    loading.value = true
    const { confirmPassword, email, ...payload } = form
    if (email) payload.email = email
    await register(payload)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch {
    // 校验失败或注册失败
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="register-card">
      <div class="brand-panel">
        <el-icon :size="56"><Reading /></el-icon>
        <h1>加入我们</h1>
        <p>注册账号，开启借阅之旅</p>
      </div>

      <div class="form-panel">
        <h2>用户注册</h2>
        <el-form ref="formRef" :model="form" :rules="rules" size="large">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              placeholder="密码（至少 6 位）"
              :prefix-icon="Lock"
            />
          </el-form-item>
          <el-form-item prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              show-password
              placeholder="确认密码"
              :prefix-icon="Lock"
            />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="form.email" placeholder="邮箱（选填）" :prefix-icon="Message" />
          </el-form-item>
          <el-button
            type="primary"
            class="submit-btn"
            :loading="loading"
            @click="handleRegister"
          >
            注 册
          </el-button>
        </el-form>
        <div class="footer">
          已有账号？<router-link to="/login">返回登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-card {
  display: flex;
  width: 820px;
  max-width: 92vw;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.brand-panel {
  flex: 1;
  background: linear-gradient(160deg, #2b5876 0%, #4e4376 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
}

.brand-panel h1 {
  margin: 16px 0 8px;
  font-size: 24px;
}

.brand-panel p {
  font-size: 14px;
  opacity: 0.9;
}

.form-panel {
  flex: 1.2;
  background: #fff;
  padding: 40px;
}

.form-panel h2 {
  text-align: center;
  margin-bottom: 24px;
  color: #303133;
}

.submit-btn {
  width: 100%;
}

.footer {
  text-align: center;
  margin-top: 16px;
  font-size: 14px;
  color: #606266;
}

.footer a {
  color: #409eff;
}

@media (max-width: 768px) {
  .register-card {
    flex-direction: column;
  }
  .brand-panel {
    padding: 24px;
  }
}
</style>
