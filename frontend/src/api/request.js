import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 本地存储 Key
export const TOKEN_KEY = 'book_token'
export const USER_KEY = 'book_user'
export const PERMISSIONS_KEY = 'book_permissions'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,  // 15秒超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：自动注入 Token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一解包数据 + 错误处理
request.interceptors.response.use(
  (response) => {
    const res = response.data
    // 后端统一响应：{ code, message, data }
    // 2xx 都视为成功（包括 201 Created）
    if (res && res.code !== undefined && (res.code < 200 || res.code >= 300)) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || 'Error'))
    }
    return res
  },
  (error) => {
    const status = error.response?.status
    const message = error.response?.data?.message || error.message

    // 生产环境不显示详细错误信息
    const isDev = import.meta.env.DEV

    if (status === 401) {
      // 登录接口返回 401 表示「登录失败」（密码错误/用户不存在/账号禁用），
      // 并非 token 失效，应显示后端返回的具体原因
      if (error.config?.url?.includes('/auth/login')) {
        ElMessage.error(message || '登录失败')
      } else {
        // 登录态失效：清除凭证并跳转登录页
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        ElMessage.error('登录已过期，请重新登录')
        if (router.currentRoute.value.path !== '/login') {
          router.push('/login')
        }
      }
    } else if (status === 429) {
      ElMessage.error('请求过于频繁，请稍后再试')
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络后重试')
    } else if (status >= 500) {
      ElMessage.error('服务器内部错误，请稍后再试')
    } else if (isDev) {
      // 开发环境显示详细错误
      ElMessage.error(message || '网络请求失败')
    } else {
      // 生产环境显示通用错误
      ElMessage.error('请求失败，请重试')
    }
    return Promise.reject(error)
  }
)

export default request
