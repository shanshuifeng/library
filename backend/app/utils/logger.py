"""
结构化日志模块
提供统一的日志配置和关键操作记录
"""
import logging
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON 格式日志格式化器"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }

        # 添加额外字段
        if hasattr(record, 'extra_data') and record.extra_data:
            log_data['data'] = record.extra_data

        # 添加异常信息
        if record.exc_info and record.exc_info[0] is not None:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(app=None):
    """
    配置应用日志

    Args:
        app: Flask 应用实例
    """
    # 创建日志目录
    import os
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # 配置根日志器
    logger = logging.getLogger('book_manager')
    logger.setLevel(logging.INFO)

    # 控制台输出（开发环境使用简洁格式）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if (app and app.debug) else logging.INFO)
    console_format = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)

    # 文件输出（JSON 格式，便于日志分析）
    file_handler = logging.FileHandler(
        os.path.join(log_dir, 'app.log'),
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JSONFormatter())

    # 错误日志单独文件
    error_handler = logging.FileHandler(
        os.path.join(log_dir, 'error.log'),
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())

    # 清除已有处理器
    logger.handlers.clear()

    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    return logger


def get_logger():
    """
    获取日志器实例

    Returns:
        Logger 实例
    """
    return logging.getLogger('book_manager')


# ===== 关键操作日志辅助函数 =====

def log_user_login(user_id, username, success=True, ip_address=None):
    """记录用户登录"""
    logger = get_logger()
    logger.info(
        f'用户登录: {username}',
        extra={'extra_data': {
            'action': 'user_login',
            'user_id': user_id,
            'username': username,
            'success': success,
            'ip_address': ip_address
        }}
    )


def log_user_register(user_id, username, role='student'):
    """记录用户注册"""
    logger = get_logger()
    logger.info(
        f'用户注册: {username}',
        extra={'extra_data': {
            'action': 'user_register',
            'user_id': user_id,
            'username': username,
            'role': role
        }}
    )


def log_book_borrow(user_id, book_id, book_title, success=True, error_msg=None):
    """记录借书操作"""
    logger = get_logger()
    if success:
        logger.info(
            f'借书成功: 用户{user_id}借阅《{book_title}》',
            extra={'extra_data': {
                'action': 'book_borrow',
                'user_id': user_id,
                'book_id': book_id,
                'book_title': book_title,
                'success': True
            }}
        )
    else:
        logger.warning(
            f'借书失败: 用户{user_id}借阅《{book_title}》- {error_msg}',
            extra={'extra_data': {
                'action': 'book_borrow',
                'user_id': user_id,
                'book_id': book_id,
                'book_title': book_title,
                'success': False,
                'error': error_msg
            }}
        )


def log_book_return(user_id, book_id, book_title, fine=0):
    """记录还书操作"""
    logger = get_logger()
    logger.info(
        f'还书: 用户{user_id}归还《{book_title}》',
        extra={'extra_data': {
            'action': 'book_return',
            'user_id': user_id,
            'book_id': book_id,
            'book_title': book_title,
            'fine': float(fine)
        }}
    )


def log_book_renew(user_id, book_id, book_title, success=True):
    """记录续借操作"""
    logger = get_logger()
    logger.info(
        f'续借: 用户{user_id}续借《{book_title}》',
        extra={'extra_data': {
            'action': 'book_renew',
            'user_id': user_id,
            'book_id': book_id,
            'book_title': book_title,
            'success': success
        }}
    )


def log_admin_operation(admin_id, operation, target_type, target_id, detail=None):
    """记录管理员操作"""
    logger = get_logger()
    logger.info(
        f'管理员操作: {operation} {target_type}#{target_id}',
        extra={'extra_data': {
            'action': 'admin_operation',
            'admin_id': admin_id,
            'operation': operation,
            'target_type': target_type,
            'target_id': target_id,
            'detail': detail
        }}
    )
