// ===== 角色相关 =====
export const ROLE_LABELS = {
  admin: '管理员',
  teacher: '教师',
  student: '学生'
}

// 表单可选项
export const ROLE_OPTIONS = [
  { label: '学生', value: 'student' },
  { label: '教师', value: 'teacher' },
  { label: '管理员', value: 'admin' }
]

export function roleLabel(role) {
  return ROLE_LABELS[role] || '未知'
}

// Element Plus Tag 类型
export const ROLE_TAG_TYPE = {
  admin: 'danger',
  teacher: 'warning',
  student: ''
}

// ===== 借阅状态相关 =====
export const BORROW_STATUS_LABELS = {
  borrowed: '借阅中',
  returned: '已归还',
  overdue: '已逾期'
}

export const BORROW_STATUS_TAG_TYPE = {
  borrowed: 'warning',
  returned: 'success',
  overdue: 'danger'
}

export function borrowStatusLabel(status) {
  return BORROW_STATUS_LABELS[status] || status
}

// ===== 库存状态 =====
export function stockTagType(stock) {
  if (stock <= 0) return 'danger'
  if (stock <= 3) return 'warning'
  return 'success'
}

// ===== 格式化 =====
// 日期格式化：'2026-07-17'
export function formatDate(value) {
  if (!value) return '-'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// 日期时间格式化：'2026-07-17 12:00'
export function formatDateTime(value) {
  if (!value) return '-'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  const pad = (n) => String(n).padStart(2, '0')
  return `${formatDate(value)} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// 金额格式化
export function formatMoney(value) {
  const num = Number(value || 0)
  return `¥${num.toFixed(2)}`
}
