import request from './request'

// 借书
export function borrowBook(data) {
  return request({ url: '/borrows/', method: 'post', data })
}

// 还书
export function returnBook(id) {
  return request({ url: `/borrows/${id}/return`, method: 'put' })
}

// 续借
export function renewBook(id) {
  return request({ url: `/borrows/${id}/renew`, method: 'put' })
}

// 借阅记录列表（管理端）
export function getBorrowList(params) {
  return request({ url: '/borrows/', method: 'get', params })
}

// 某用户的借阅记录
export function getUserBorrows(userId, params) {
  return request({ url: `/borrows/user/${userId}`, method: 'get', params })
}
