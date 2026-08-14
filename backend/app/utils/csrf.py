"""
CSRF 保护模块（双重提交 Cookie 模式）
适用于 JWT + Cookie 场景
"""
import secrets
from functools import wraps
from flask import request, make_response
from ..utils.response import error_response


CSRF_TOKEN_KEY = 'csrf_token'
CSRF_HEADER_NAME = 'X-CSRF-Token'


def generate_csrf_token():
    """生成 CSRF Token"""
    token = secrets.token_hex(32)
    return token


def validate_csrf(f):
    """
    CSRF 验证装饰器
    使用双重提交 Cookie 模式：客户端在 Cookie 和 Header 中都发送 Token
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 开发环境可选择跳过 CSRF 检查
        from flask import current_app
        if current_app.config.get('TESTING'):
            return f(*args, **kwargs)

        # 从 Cookie 获取 token
        cookie_token = request.cookies.get(CSRF_TOKEN_KEY)

        # 从 Header 获取 token
        header_token = request.headers.get(CSRF_HEADER_NAME)

        # 验证两者都存在且一致
        if not cookie_token or not header_token:
            return error_response('缺少 CSRF Token', 403)

        if cookie_token != header_token:
            return error_response('CSRF Token 验证失败', 403)

        # 验证 token 格式（防止固定值攻击）
        if len(cookie_token) != 64:  # 32 bytes = 64 hex chars
            return error_response('CSRF Token 无效', 403)

        return f(*args, **kwargs)
    return decorated


@app.after_request
def set_csrf_cookie(response):
    """
    为每个响应设置 CSRF Cookie
    """
    # 只在认证相关的写操作时设置
    if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
        token = request.headers.get(CSRF_HEADER_NAME)
        if token:
            response.set_cookie(
                CSRF_TOKEN_KEY,
                token,
                httponly=False,  # JavaScript 需要读取
                secure=not app.config.get('DEBUG'),  # 生产环境强制 HTTPS
                samesite='Lax'
            )
    return response
