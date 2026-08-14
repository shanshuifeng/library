import request from './request'

// 系统概览（图书/借阅/用户/逾期统计）
export function getOverview() {
  return request({ url: '/stats/overview', method: 'get' })
}

// 每日借阅/归还趋势
export function getDailyTrend() {
  return request({ url: '/stats/daily-trend', method: 'get' })
}

// 借阅趋势（管理员）
export function getBorrowTrend(params) {
  return request({ url: '/stats/borrow-trend', method: 'get', params })
}

// 热门图书
export function getPopularBooks(params) {
  return request({ url: '/stats/popular-books', method: 'get', params })
}
