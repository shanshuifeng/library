-- ============================================================
-- 用户表
-- ============================================================
CREATE TABLE IF NOT EXISTS `users` (
  `id`          INT          NOT NULL AUTO_INCREMENT,
  `username`    VARCHAR(50)  NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `email`       VARCHAR(100) DEFAULT NULL,
  `phone`       VARCHAR(20)  DEFAULT NULL,
  `real_name`   VARCHAR(50)  DEFAULT NULL,
  `student_id`  VARCHAR(50)  DEFAULT NULL,
  `role`        VARCHAR(10)  NOT NULL DEFAULT 'student',
  `status`      SMALLINT     NOT NULL DEFAULT 1,
  `created_at`  DATETIME     DEFAULT NULL,
  `updated_at`  DATETIME     DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_username` (`username`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `student_id` (`student_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- ============================================================
-- 图书分类表（支持多级分类，自关联）
-- ============================================================
CREATE TABLE IF NOT EXISTS `categories` (
  `id`          INT          NOT NULL AUTO_INCREMENT,
  `name`        VARCHAR(50)  NOT NULL,
  `parent_id`   INT          DEFAULT NULL,
  `level`       INT          DEFAULT 1,
  `sort_order`  INT          DEFAULT 0,
  `description` VARCHAR(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `parent_id` (`parent_id`),
  CONSTRAINT `categories_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `categories` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- ============================================================
-- 图书表
-- ============================================================
CREATE TABLE IF NOT EXISTS `books` (
  `id`           INT            NOT NULL AUTO_INCREMENT,
  `title`        VARCHAR(200)   NOT NULL,
  `author`       VARCHAR(100)   DEFAULT NULL,
  `isbn`         VARCHAR(20)    DEFAULT NULL,
  `publisher`    VARCHAR(100)   DEFAULT NULL,
  `publish_date` DATE           DEFAULT NULL,
  `category_id`  INT            DEFAULT NULL,
  `price`        DECIMAL(10,2)  DEFAULT NULL,
  `stock`        INT            NOT NULL DEFAULT 0,
  `total_stock`  INT            NOT NULL DEFAULT 0,
  `description`  TEXT           DEFAULT NULL,
  `cover_image`  VARCHAR(500)   DEFAULT NULL,
  `location`     VARCHAR(100)   DEFAULT NULL COMMENT '馆藏位置',
  `created_at`   DATETIME       DEFAULT NULL,
  `updated_at`   DATETIME       DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_books_isbn` (`isbn`),
  KEY `ix_books_title` (`title`),
  KEY `ix_books_author` (`author`),
  KEY `category_id` (`category_id`),
  CONSTRAINT `books_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- ============================================================
-- 借阅记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS `borrow_records` (
  `id`           INT            NOT NULL AUTO_INCREMENT,
  `user_id`      INT            NOT NULL,
  `book_id`      INT            NOT NULL,
  `borrow_date`  DATE           NOT NULL,
  `due_date`     DATE           NOT NULL,
  `return_date`  DATE           DEFAULT NULL,
  `renew_count`  INT            DEFAULT 0,
  `fine`         DECIMAL(10,2)  DEFAULT 0.00,
  `status`       VARCHAR(10)    NOT NULL DEFAULT 'borrowed',
  `created_at`   DATETIME       DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `book_id` (`book_id`),
  CONSTRAINT `borrow_records_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `borrow_records_ibfk_2` FOREIGN KEY (`book_id`) REFERENCES `books` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- ============================================================
-- 系统配置表
-- ============================================================
CREATE TABLE IF NOT EXISTS `system_config` (
  `id`           INT          NOT NULL AUTO_INCREMENT,
  `config_key`   VARCHAR(50)  NOT NULL,
  `config_value` VARCHAR(500) DEFAULT NULL,
  `description`  VARCHAR(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_system_config_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- ============================================================
-- 权限表
-- ============================================================
CREATE TABLE IF NOT EXISTS `permissions` (
  `id`          INT          NOT NULL AUTO_INCREMENT,
  `code`        VARCHAR(100) NOT NULL COMMENT '权限代码，如 book:create',
  `name`        VARCHAR(50)  NOT NULL COMMENT '权限名称',
  `group`       VARCHAR(50)  NOT NULL DEFAULT '其他' COMMENT '分组',
  `description` VARCHAR(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_permission_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- ============================================================
-- 角色表
-- ============================================================
CREATE TABLE IF NOT EXISTS `roles` (
  `id`          INT          NOT NULL AUTO_INCREMENT,
  `name`        VARCHAR(50)  NOT NULL,
  `description` VARCHAR(200) DEFAULT NULL,
  `is_system`   TINYINT(1)   DEFAULT 0 COMMENT '系统角色不可删除',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_role_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- ============================================================
-- 角色-权限 关联表
-- ============================================================
CREATE TABLE IF NOT EXISTS `role_permissions` (
  `role_id`       INT NOT NULL,
  `permission_id` INT NOT NULL,
  PRIMARY KEY (`role_id`, `permission_id`),
  KEY `idx_role_permissions_perm` (`permission_id`),
  CONSTRAINT `fk_rp_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_rp_perm` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- ============================================================
-- 用户-角色 关联表
-- ============================================================
CREATE TABLE IF NOT EXISTS `user_roles` (
  `user_id` INT NOT NULL,
  `role_id` INT NOT NULL,
  PRIMARY KEY (`user_id`, `role_id`),
  KEY `idx_user_roles_role` (`role_id`),
  CONSTRAINT `fk_ur_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ur_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- ============================================================
-- 预约表：学生在线预约，线下取书
-- 状态流转：pending → ready → picked_up（转为借阅记录）
--          pending → cancelled
--          ready → expired
-- ============================================================
CREATE TABLE IF NOT EXISTS `reservations` (
  `id`               INT          NOT NULL AUTO_INCREMENT,
  `user_id`          INT          NOT NULL,
  `book_id`          INT          NOT NULL,
  `status`           VARCHAR(20)  NOT NULL DEFAULT 'pending' COMMENT 'pending/ready/cancelled/picked_up/expired',
  `created_at`       DATETIME     DEFAULT NULL,
  `expiry_date`      DATETIME     DEFAULT NULL COMMENT '预约过期时间',
  `processed_at`     DATETIME     DEFAULT NULL COMMENT '处理时间',
  `borrow_record_id` INT          DEFAULT NULL COMMENT '关联借阅记录ID',
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `book_id` (`book_id`),
  KEY `borrow_record_id` (`borrow_record_id`),
  CONSTRAINT `reservations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `reservations_ibfk_2` FOREIGN KEY (`book_id`) REFERENCES `books` (`id`),
  CONSTRAINT `reservations_ibfk_3` FOREIGN KEY (`borrow_record_id`) REFERENCES `borrow_records` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
