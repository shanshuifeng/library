import request from './request'

// 登录
export function login(data) {
  return request({ url: '/auth/login', method: 'post', data })
}

// 注册
export function register(data) {
  return request({ url: '/auth/register', method: 'post', data })
}

// 退出登录
export function logout() {
  return request({ url: '/auth/logout', method: 'post' })
}

// 获取当前用户信息
export function getProfile() {
  return request({ url: '/auth/profile', method: 'get' })
}

// 修改密码
export function updatePassword(data) {
  return request({ url: '/auth/password', method: 'put', data })
}
