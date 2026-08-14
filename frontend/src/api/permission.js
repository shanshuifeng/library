import request from './request'

// 获取所有权限（分组）
export function getPermissions() {
  return request({ url: '/permissions/', method: 'get' })
}

// 获取所有角色
export function getRoles() {
  return request({ url: '/permissions/roles', method: 'get' })
}

// 获取角色详情
export function getRoleDetail(id) {
  return request({ url: `/permissions/roles/${id}`, method: 'get' })
}

// 创建角色
export function createRole(data) {
  return request({ url: '/permissions/roles', method: 'post', data })
}

// 更新角色
export function updateRole(id, data) {
  return request({ url: `/permissions/roles/${id}`, method: 'put', data })
}

// 删除角色
export function deleteRole(id) {
  return request({ url: `/permissions/roles/${id}`, method: 'delete' })
}

// 获取用户角色
export function getUserRoles(userId) {
  return request({ url: `/permissions/users/${userId}/roles`, method: 'get' })
}

// 设置用户角色
export function setUserRoles(userId, roleIds) {
  return request({ url: `/permissions/users/${userId}/roles`, method: 'put', data: { role_ids: roleIds } })
}

// 获取当前用户权限
export function getMyPermissions() {
  return request({ url: '/permissions/mine', method: 'get' })
}
