import request from './request'

// 创建预约
export function createReservation(data) {
  return request({ url: '/reservations/', method: 'post', data })
}

// 我的预约列表
export function getMyReservations(params) {
  return request({ url: '/reservations/my', method: 'get', params })
}

// 取消预约
export function cancelReservation(id) {
  return request({ url: `/reservations/${id}/cancel`, method: 'put' })
}

// 管理员：所有预约列表
export function getReservationList(params) {
  return request({ url: '/reservations/', method: 'get', params })
}

// 管理员：标记就绪
export function markReservationReady(id) {
  return request({ url: `/reservations/${id}/ready`, method: 'put' })
}

// 管理员：确认取书
export function pickupReservation(id) {
  return request({ url: `/reservations/${id}/pickup`, method: 'put' })
}
