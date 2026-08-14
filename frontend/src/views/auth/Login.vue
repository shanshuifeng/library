<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ]
}

// 根据用户权限获取默认首页路由名称
function getDefaultPage() {
  if (userStore.isAdmin) return 'Dashboard'
  if (userStore.hasPermission('stats:overview')) return 'Dashboard'
  if (userStore.hasPermission('borrow:list')) return 'MyBorrow'
  if (userStore.hasPermission('book:list')) return 'BookList'
  return 'Profile'
}

async function handleLogin() {
  try {
    await formRef.value.validate()
    loading.value = true
    await userStore.login(form)
    ElMessage.success('登录成功')
    // 回跳到来源页，否则根据权限跳转到合适页面
    const redirect = route.query.redirect
    if (redirect) {
      router.push(redirect)
    } else {
      router.push({ name: getDefaultPage() })
    }
  } catch {
    // 校验失败或登录失败（错误已由拦截器提示）
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <!-- 品牌展示区 -->
      <div class="brand-panel">
        <el-icon :size="56"><Reading /></el-icon>
        <h1>大学图书管理系统</h1>
        <p>图书管理 · 借阅服务 · 数据统计</p>
        <p class="sub">让每一本好书找到它的读者</p>
      </div>

      <!-- 登录表单区 -->
      <div class="form-panel">
        <h2>用户登录</h2>
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          size="large"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              placeholder="请输入密码"
              :prefix-icon="Lock"
            />
          </el-form-item>
          <el-button
            type="primary"
            class="submit-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form>
        <div class="footer">
          还没有账号？<router-link to="/register">立即注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  display: flex;
  width: 820px;
  max-width: 92vw;
  height: 480px;
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
  margin: 4px 0;
}

.brand-panel .sub {
  margin-top: 24px;
  font-size: 13px;
  opacity: 0.7;
}

.form-panel {
  flex: 1;
  background: #fff;
  padding: 48px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.form-panel h2 {
  text-align: center;
  margin-bottom: 32px;
  color: #303133;
}

.submit-btn {
  width: 100%;
}

.footer {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #606266;
}

.footer a {
  color: #409eff;
}

@media (max-width: 768px) {
  .login-card {
    flex-direction: column;
    height: auto;
  }
  .brand-panel {
    padding: 24px;
  }
  .form-panel {
    padding: 32px 24px;
  }
}
</style>
