import request from './request'

// 用户列表
export function getUserList(params) {
  return request({ url: '/users/', method: 'get', params })
}

// 创建用户
export function createUser(data) {
  return request({ url: '/users/', method: 'post', data })
}

// 更新用户
export function updateUser(id, data) {
  return request({ url: `/users/${id}`, method: 'put', data })
}

// 删除用户
export function deleteUser(id) {
  return request({ url: `/users/${id}`, method: 'delete' })
}
