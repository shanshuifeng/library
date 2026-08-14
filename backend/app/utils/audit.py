"""
审计工具模块
提供审计日志记录功能
"""
import json
from functools import wraps
from flask import request, g
from flask_jwt_extended import get_jwt_identity
from datetime import datetime


def get_current_user():
    """获取当前登录用户信息"""
    try:
        user_id = get_jwt_identity()
        if user_id:
            from ..models.user import User
            user = User.query.get(int(user_id))
            if user:
                return user.id, user.username
    except Exception:
        pass
    return None, None


def get_client_info():
    """获取客户端信息"""
    return {
        'ip': request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown'),
        'user_agent': request.headers.get('User-Agent', '')[:500]
    }


def log_audit(action, resource_type, resource_id=None, detail=None,
              old_value=None, new_value=None, status='success', error_message=None):
    """
    记录审计日志

    Args:
        action: 操作类型 (create/update/delete/login/logout/borrow/return等)
        resource_type: 资源类型 (user/book/borrow/reservation等)
        resource_id: 资源ID
        detail: 操作详情描述
        old_value: 变更前数据（JSON可序列化对象）
        new_value: 变更后数据（JSON可序列化对象）
        status: 操作状态 (success/failed/error)
        error_message: 错误信息
    """
    from ..models.audit import AuditLog
    from ..extensions import db

    try:
        user_id, username = get_current_user()
        client_info = get_client_info()

        audit_log = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
            user_id=user_id,
            username=username,
            ip_address=client_info['ip'],
            user_agent=client_info['user_agent'],
            request_method=request.method if request else None,
            request_path=request.path if request else None,
            old_value=old_value,
            new_value=new_value,
            status=status,
            error_message=error_message
        )

        db.session.add(audit_log)
        db.session.commit()
        print(f'[AUDIT] Success: {action} {resource_type}#{resource_id}')
    except Exception as e:
        # 审计日志记录失败不应影响业务
        import traceback
        print(f'[AUDIT] Failed to log audit: {e}')
        print(traceback.format_exc())
        db.session.rollback()


def log_access(response_status=None, response_time=None):
    """
    记录访问日志

    Args:
        response_status: 响应状态码
        response_time: 响应时间（毫秒）
    """
    from ..models.audit import AccessLog
    from ..extensions import db

    try:
        user_id, username = get_current_user()
        client_info = get_client_info()

        # 脱敏请求体
        request_body = None
        if request.is_json:
            body = request.get_json(silent=True)
            if body:
                request_body = _sanitize_data(body)

        access_log = AccessLog(
            request_method=request.method,
            request_path=request.path,
            query_params=dict(request.args) if request.args else None,
            request_body=request_body,
            response_status=response_status,
            response_time=response_time,
            user_id=user_id,
            username=username,
            ip_address=client_info['ip'],
            user_agent=client_info['user_agent']
        )

        db.session.add(access_log)
        db.session.commit()
    except Exception as e:
        print(f'[ACCESS] Failed to log access: {e}')


def _sanitize_data(data):
    """脱敏敏感数据"""
    if not isinstance(data, dict):
        return data

    sensitive_keys = {'password', 'old_password', 'new_password', 'token', 'secret'}
    sanitized = {}

    for key, value in data.items():
        if key.lower() in sensitive_keys:
            sanitized[key] = '***'
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_data(value)
        else:
            sanitized[key] = value

    return sanitized


def audit_log(action, resource_type, get_id=None, get_detail=None):
    """
    审计日志装饰器

    Args:
        action: 操作类型
        resource_type: 资源类型
        get_id: 获取资源ID的函数，接收返回值
        get_detail: 获取操作详情的函数，接收返回值
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 记录操作前的时间
            start_time = datetime.now()

            try:
                result = f(*args, **kwargs)

                # 提取资源ID
                resource_id = None
                if get_id and callable(get_id):
                    try:
                        resource_id = get_id(result)
                    except Exception:
                        pass

                # 提取操作详情
                detail = None
                if get_detail and callable(get_detail):
                    try:
                        detail = get_detail(result)
                    except Exception:
                        pass

                # 记录成功日志
                log_audit(
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    detail=detail,
                    status='success'
                )

                return result

            except Exception as e:
                # 记录失败日志
                log_audit(
                    action=action,
                    resource_type=resource_type,
                    detail=f'操作失败: {str(e)[:500]}',
                    status='error',
                    error_message=str(e)
                )
                raise

        return decorated_function
    return decorator


def record_change(old_obj, new_data, resource_type, action='update'):
    """
    记录数据变更

    Args:
        old_obj: 变更前的对象
        new_data: 变更后的数据字典
        resource_type: 资源类型
        action: 操作类型
    """
    old_value = None
    new_value = None

    if old_obj:
        old_value = old_obj.to_dict() if hasattr(old_obj, 'to_dict') else str(old_obj)

    if new_data:
        new_value = _sanitize_data(new_data)

    log_audit(
        action=action,
        resource_type=resource_type,
        resource_id=old_obj.id if old_obj and hasattr(old_obj, 'id') else None,
        old_value=old_value,
        new_value=new_value
    )
