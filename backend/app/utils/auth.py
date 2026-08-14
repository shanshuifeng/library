"""
认证工具函数
"""
from functools import wraps
from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from .response import error_response


def get_current_user_id():
    """获取当前用户 ID（转为整数）"""
    return int(get_jwt_identity())


def admin_required(fn):
    """
    管理员权限装饰器（兼容旧代码，新代码建议用 permission_required）
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from ..models.user import User

        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user or user.role != 'admin':
            return error_response('需要管理员权限', 403)

        return fn(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """
    角色权限装饰器

    Args:
        *roles: 允许的角色列表，如 'admin', 'teacher', 'student'

    使用方法:
        @role_required('admin', 'teacher')
        def my_endpoint():
            pass
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from ..models.user import User

            verify_jwt_in_request()
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)

            if not user or user.role not in roles:
                return error_response('权限不足', 403)

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def permission_required(permission_code):
    """
    权限装饰器

    Args:
        permission_code: 权限代码，如 'book:create'

    使用方法:
        @permission_required('book:create')
        def my_endpoint():
            pass
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from ..services.permission_service import user_has_permission

            verify_jwt_in_request()
            user_id = int(get_jwt_identity())

            if not user_has_permission(user_id, permission_code):
                return error_response('权限不足', 403)

            return fn(*args, **kwargs)
        return wrapper
    return decorator
