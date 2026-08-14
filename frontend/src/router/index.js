import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { title: '登录', guest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { title: '注册', guest: true }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '首页概览', icon: 'HomeFilled', permission: 'stats:overview' }
      },
      {
        path: 'books',
        name: 'BookList',
        component: () => import('@/views/book/BookList.vue'),
        meta: { title: '图书查询', icon: 'Reading', permission: 'book:list' }
      },
      {
        path: 'books/:id',
        name: 'BookDetail',
        component: () => import('@/views/book/BookDetail.vue'),
        meta: { title: '图书详情', permission: 'book:view' }
      },
      {
        path: 'borrow/my',
        name: 'MyBorrow',
        component: () => import('@/views/borrow/MyBorrow.vue'),
        meta: { title: '我的借阅', icon: 'Tickets', permission: 'borrow:list' }
      },
      {
        path: 'reservations',
        name: 'MyReservations',
        component: () => import('@/views/reservation/MyReservations.vue'),
        meta: { title: '我的预约', icon: 'Timer', permission: 'reservation:list-my' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/Index.vue'),
        meta: { title: '个人中心', icon: 'User' }
      },
      // ===== 以下为管理员路由 =====
      {
        path: 'admin/books',
        name: 'BookManage',
        component: () => import('@/views/admin/BookManage.vue'),
        meta: { title: '图书管理', icon: 'Notebook', requiresAdmin: true }
      },
      {
        path: 'admin/categories',
        name: 'CategoryManage',
        component: () => import('@/views/admin/CategoryManage.vue'),
        meta: { title: '分类管理', icon: 'Files', requiresAdmin: true }
      },
      {
        path: 'admin/borrows',
        name: 'BorrowList',
        component: () => import('@/views/borrow/BorrowList.vue'),
        meta: { title: '借阅管理', icon: 'Document', requiresAdmin: true }
      },
      {
        path: 'admin/users',
        name: 'UserManage',
        component: () => import('@/views/admin/UserManage.vue'),
        meta: { title: '用户管理', icon: 'UserFilled', requiresAdmin: true }
      },
      {
        path: 'admin/reservations',
        name: 'ReservationManage',
        component: () => import('@/views/reservation/ReservationManage.vue'),
        meta: { title: '预约管理', icon: 'Timer', requiresAdmin: true }
      },
      {
        path: 'admin/roles',
        name: 'RoleManage',
        component: () => import('@/views/admin/RoleManage.vue'),
        meta: { title: '角色管理', icon: 'Setting', requiresAdmin: true }
      },
      {
        path: 'admin/audit',
        name: 'AuditLog',
        component: () => import('@/views/admin/AuditLog.vue'),
        meta: { title: '审计日志', icon: 'Document', requiresAdmin: true }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFound.vue'),
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

/**
 * 检查 JWT Token 是否过期
 * @param {string} token JWT token
 * @returns {boolean} 是否过期
 */
function isTokenExpired(token) {
  if (!token) return true
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp * 1000 // 转换为毫秒
    return Date.now() >= exp
  } catch {
    return true
  }
}

// 根据用户角色获取默认首页路由名称
function getDefaultPage(userStore) {
  if (userStore.isAdmin) return { name: 'Dashboard' }
  if (userStore.hasPermission('stats:overview')) return { name: 'Dashboard' }
  if (userStore.hasPermission('borrow:list')) return { name: 'MyBorrow' }
  if (userStore.hasPermission('book:list')) return { name: 'BookList' }
  return { name: 'Profile' }
}

// 全局前置守卫：登录校验 + 角色权限控制
router.beforeEach((to) => {
  const userStore = useUserStore()

  // 设置页面标题
  document.title = to.meta.title
    ? `${to.meta.title} - 大学图书管理系统`
    : '大学图书管理系统'

  // 检查 token 是否过期
  if (userStore.token && isTokenExpired(userStore.token)) {
    userStore.reset()
    if (to.meta.requiresAuth) {
      return { path: '/login', query: { redirect: to.fullPath } }
    }
  }

  // 已登录用户访问 登录/注册 → 跳转默认首页
  if (to.meta.guest && userStore.isLoggedIn) {
    return getDefaultPage(userStore)
  }

  // 需要登录但未登录 → 跳转登录（携带回跳地址）
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  // 需要管理员权限但非管理员 → 拒绝访问，回默认首页
  if (to.meta.requiresAdmin && !userStore.isAdmin) {
    return getDefaultPage(userStore)
  }

  // 检查具体权限
  if (to.meta.permission && !userStore.hasPermission(to.meta.permission)) {
    return getDefaultPage(userStore)
  }

  return true
})

export default router
