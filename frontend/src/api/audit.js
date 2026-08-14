/**
 * 审计日志 API
 */
import request from './request'

/**
 * 获取审计日志列表
 * @param {Object} params 查询参数
 */
export function getAuditLogs(params = {}) {
  return request.get('/audit/logs', { params })
}

/**
 * 获取审计日志详情
 * @param {number} logId 日志ID
 */
export function getAuditLogDetail(logId) {
  return request.get(`/audit/logs/${logId}`)
}

/**
 * 获取访问日志列表
 * @param {Object} params 查询参数
 */
export function getAccessLogs(params = {}) {
  return request.get('/audit/access-logs', { params })
}

/**
 * 获取审计统计信息
 */
export function getAuditStats() {
  return request.get('/audit/stats')
}

/**
 * 清理过期审计日志
 */
export function cleanupAuditLogs() {
  return request.delete('/audit/cleanup')
}
