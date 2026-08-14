<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/store/user'
import { roleLabel, ROLE_TAG_TYPE } from '@/utils'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isCollapse = ref(false)

// 普通用户菜单（带权限标识）
const commonMenus = [
  { index: '/dashboard', title: '首页概览', icon: 'HomeFilled', permission: 'stats:overview' },
  { index: '/books', title: '图书查询', icon: 'Reading', permission: 'book:list' },
  { index: '/borrow/my', title: '我的借阅', icon: 'Tickets', permission: 'borrow:list' },
  { index: '/reservations', title: '我的预约', icon: 'Timer', permission: 'reservation:list-my' },
  { index: '/profile', title: '个人中心', icon: 'User', permission: '' }
]

// 管理员菜单
const adminMenus = [
  { index: '/admin/books', title: '图书管理', icon: 'Notebook' },
  { index: '/admin/categories', title: '分类管理', icon: 'Files' },
  { index: '/admin/borrows', title: '借阅管理', icon: 'Document' },
  { index: '/admin/users', title: '用户管理', icon: 'UserFilled' },
  { index: '/admin/reservations', title: '预约管理', icon: 'Timer' },
  { index: '/admin/roles', title: '角色管理', icon: 'Setting' },
  { index: '/admin/audit', title: '审计日志', icon: 'Document' }
]

// 根据权限过滤菜单
const filteredCommonMenus = computed(() => {
  return commonMenus.filter(m => {
    if (!m.permission) return true
    return userStore.hasPermission(m.permission)
  })
})

// 当前高亮菜单（详情页归到对应列表）
const activeMenu = computed(() => {
  if (route.path.startsWith('/books/')) return '/books'
  return route.path
})

const roleTagType = computed(() => ROLE_TAG_TYPE[userStore.role] || '')

function handleSelect(index) {
  router.push(index)
}

function handleCommand(command) {
  if (command === 'profile') router.push('/profile')
  else if (command === 'logout') handleLogout()
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<template>
  <el-container class="layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '210px'" class="sidebar">
      <div class="logo">
        <el-icon :size="24" color="#409eff"><Reading /></el-icon>
        <span v-show="!isCollapse" class="logo-text">图书管理系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        background-color="#001529"
        text-color="#bfcbd9"
        active-text-color="#ffffff"
        @select="handleSelect"
      >
        <el-menu-item v-for="m in filteredCommonMenus" :key="m.index" :index="m.index">
          <el-icon><component :is="m.icon" /></el-icon>
          <template #title>{{ m.title }}</template>
        </el-menu-item>

        <el-sub-menu v-if="userStore.isAdmin" index="system">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item v-for="m in adminMenus" :key="m.index" :index="m.index">
            <el-icon><component :is="m.icon" /></el-icon>
            <template #title>{{ m.title }}</template>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶栏 -->
      <el-header class="header">
        <el-icon class="collapse-btn" :size="20" @click="isCollapse = !isCollapse">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>

        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-avatar :size="32" icon="UserFilled" />
            <span class="username">{{ userStore.displayName }}</span>
            <el-tag size="small" :type="roleTagType">{{ roleLabel(userStore.role) }}</el-tag>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon> 个人中心
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
}

.sidebar {
  height: 100vh;
  background-color: #001529;
  overflow-x: hidden;
  transition: width 0.28s;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  background-color: #002140;
}

.logo-text {
  white-space: nowrap;
}

.el-menu {
  border-right: none;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.collapse-btn {
  cursor: pointer;
  color: #5a5e66;
}

.collapse-btn:hover {
  color: #409eff;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}

.username {
  font-size: 14px;
  color: #303133;
}

.main {
  background-color: #f5f7fa;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
