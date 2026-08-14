-- ============================================
-- 审计日志表结构
-- 执行此 SQL 创建审计相关表
-- ============================================

-- 审计日志表（操作审计）
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `action` VARCHAR(50) NOT NULL COMMENT '操作类型',
    `resource_type` VARCHAR(50) NOT NULL COMMENT '资源类型',
    `resource_id` INT COMMENT '资源ID',
    `detail` TEXT COMMENT '操作详情',
    `user_id` INT COMMENT '操作用户ID',
    `username` VARCHAR(50) COMMENT '操作用户名',
    `ip_address` VARCHAR(50) COMMENT '请求IP地址',
    `user_agent` VARCHAR(500) COMMENT '客户端信息',
    `request_method` VARCHAR(10) COMMENT '请求方法',
    `request_path` VARCHAR(500) COMMENT '请求路径',
    `old_value` JSON COMMENT '变更前数据',
    `new_value` JSON COMMENT '变更后数据',
    `status` VARCHAR(20) DEFAULT 'success' COMMENT '操作状态: success/failed/error',
    `error_message` TEXT COMMENT '错误信息',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    INDEX `idx_action` (`action`),
    INDEX `idx_resource_type` (`resource_type`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审计日志表';

-- 访问日志表
CREATE TABLE IF NOT EXISTS `access_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `request_method` VARCHAR(10) NOT NULL COMMENT '请求方法',
    `request_path` VARCHAR(500) NOT NULL COMMENT '请求路径',
    `query_params` JSON COMMENT '查询参数',
    `request_body` JSON COMMENT '请求体（脱敏）',
    `response_status` INT COMMENT '响应状态码',
    `response_time` FLOAT COMMENT '响应时间（毫秒）',
    `user_id` INT COMMENT '用户ID',
    `username` VARCHAR(50) COMMENT '用户名',
    `ip_address` VARCHAR(50) COMMENT 'IP地址',
    `user_agent` VARCHAR(500) COMMENT '客户端信息',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '访问时间',
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_request_path` (`request_path`(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='访问日志表';
