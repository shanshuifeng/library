import { defineStore } from 'pinia'
import { login as loginApi, logout as logoutApi, getProfile } from '@/api/auth'
import { getMyPermissions } from '@/api/permission'
import { TOKEN_KEY, USER_KEY, PERMISSIONS_KEY } from '@/api/request'

/**
 * 安全的 JSON.parse，防止格式错误导致应用崩溃
 */
function safeJsonParse(key, fallback) {
  try {
    const value = localStorage.getItem(key)
    return value ? JSON.parse(value) : fallback
  } catch {
    localStorage.removeItem(key)
    return fallback
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    // 从 localStorage 恢复登录态，保证刷新后仍登录
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: safeJsonParse(USER_KEY, null),
    permissions: safeJsonParse(PERMISSIONS_KEY, [])
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    role: (state) => state.user?.role || '',
    isAdmin: (state) => state.user?.role === 'admin',
    userId: (state) => state.user?.id,
    displayName: (state) => state.user?.real_name || state.user?.username || state.user?.nickname || '用户',
    hasPermission: (state) => (code) => {
      // 管理员拥有所有权限
      if (state.user?.role === 'admin') return true
      return state.permissions.includes(code)
    }
  },

  actions: {
    // 登录：保存 token 与用户信息
    async login(payload) {
      const res = await loginApi(payload)
      const data = res.data || {}
      this.token = data.token || data.access_token
      this.user = data.user
      localStorage.setItem(TOKEN_KEY, this.token)
      localStorage.setItem(USER_KEY, JSON.stringify(this.user))
      // 登录后获取权限
      await this.fetchPermissions()
      return res
    },

    // 获取用户权限列表
    async fetchPermissions() {
      try {
        const res = await getMyPermissions()
        this.permissions = res.data?.permissions || []
        localStorage.setItem(PERMISSIONS_KEY, JSON.stringify(this.permissions))
      } catch {
        this.permissions = []
      }
    },

    // 拉取最新个人信息
    async fetchProfile() {
      const res = await getProfile()
      this.user = res.data?.user || res.data
      localStorage.setItem(USER_KEY, JSON.stringify(this.user))
      return this.user
    },

    // 退出登录
    async logout() {
      try {
        await logoutApi()
      } catch {
        // 即使后端接口失败，前端仍需清除登录态
      } finally {
        this.reset()
      }
    },

    // 清空登录态
    reset() {
      this.token = ''
      this.user = null
      this.permissions = []
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      localStorage.removeItem(PERMISSIONS_KEY)
    }
  }
})
