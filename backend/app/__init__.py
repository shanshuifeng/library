"""
Flask 应用工厂
"""
import os
from flask import Flask, send_from_directory, request
from flask_cors import CORS
from flask_restx import Api

from .config import config
from .extensions import db, migrate, jwt

# 创建全局 Api 实例（flask-restx）
authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'JWT Token 认证，格式: Bearer <token>'
    }
}

api = Api(
    title='大学图书管理系统 API',
    version='1.0.0',
    description='基于 Flask + Vue 3 的前后端分离图书管理系统接口文档',
    doc='/apidocs/',
    authorizations=authorizations,
    # 不设置全局 security，由各接口单独指定
    prefix='/api/v1'
)


def create_app(config_name=None):
    """创建 Flask 应用实例"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    register_extensions(app)

    # 注册 JWT 错误回调
    register_jwt_callbacks(app)

    # 初始化 flask-restx Api 并注册命名空间
    api.init_app(app)
    register_namespaces()

    # 注册错误处理器
    register_error_handlers(app)

    # 注册静态文件服务（上传文件访问）
    register_static_routes(app)

    # JSON 输出使用中文而非 Unicode 转义
    app.json.ensure_ascii = False

    # 初始化日志
    from .utils.logger import setup_logger
    setup_logger(app)

    # 注册访问日志钩子
    register_access_log_hook(app)

    # 创建上传目录
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)

    return app


def register_extensions(app: Flask) -> None:
    """初始化 Flask 扩展"""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config.get('CORS_ORIGINS', '*')}})


def register_jwt_callbacks(app: Flask) -> None:
    """注册 JWT 相关错误回调"""

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Token 过期回调"""
        return {
            'code': 401,
            'message': '登录已过期，请重新登录',
            'data': None
        }, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """无效 Token 回调"""
        return {
            'code': 401,
            'message': '无效的身份凭证',
            'data': None
        }, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """缺少 Token 回调"""
        return {
            'code': 401,
            'message': '缺少身份凭证，请先登录',
            'data': None
        }, 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Token 已被撤销回调"""
        return {
            'code': 401,
            'message': '身份凭证已被撤销',
            'data': None
        }, 401


def register_access_log_hook(app: Flask) -> None:
    """注册访问日志钩子"""
    import time
    from flask import g
    from .utils.audit import log_access

    @app.before_request
    def before_request():
        """记录请求开始时间"""
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        """记录访问日志"""
        # 跳过静态文件和健康检查
        if request.path.startswith('/uploads/') or request.path.startswith('/static/'):
            return response
        if request.path == '/api/v1/health/':
            return response

        # 计算响应时间
        start_time = getattr(g, 'start_time', None)
        response_time = None
        if start_time:
            response_time = round((time.time() - start_time) * 1000, 2)

        # 记录访问日志
        log_access(
            response_status=response.status_code,
            response_time=response_time
        )

        return response


def register_namespaces() -> None:
    """注册所有 API 命名空间"""
    from .routes.auth import ns as auth_ns
    from .routes.book import ns as book_ns
    from .routes.borrow import ns as borrow_ns
    from .routes.user import ns as user_ns
    from .routes.stats import ns as stats_ns
    from .routes.reservation import ns as reservation_ns
    from .routes.permission import ns as permission_ns
    from .routes.health import ns as health_ns
    from .routes.audit import ns as audit_ns

    # 注意：Api 实例已设置 prefix='/api/v1'，所以命名空间路径只需相对路径
    api.add_namespace(auth_ns, path='/auth')
    api.add_namespace(book_ns, path='/books')
    api.add_namespace(borrow_ns, path='/borrows')
    api.add_namespace(user_ns, path='/users')
    api.add_namespace(stats_ns, path='/stats')
    api.add_namespace(reservation_ns, path='/reservations')
    api.add_namespace(permission_ns, path='/permissions')
    api.add_namespace(health_ns, path='/health')
    api.add_namespace(audit_ns, path='/audit')


def register_error_handlers(app: Flask) -> None:
    """注册全局错误处理器"""
    from .utils.response import error_response, validation_error_response
    from marshmallow import ValidationError

    @app.errorhandler(400)
    def bad_request(error):
        return error_response('请求参数错误', 400)

    @app.errorhandler(401)
    def unauthorized(error):
        return error_response('未授权访问', 401)

    @app.errorhandler(403)
    def forbidden(error):
        return error_response('禁止访问', 403)

    @app.errorhandler(404)
    def not_found(error):
        return error_response('资源未找到', 404)

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return error_response('服务器内部错误', 500)

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """全局 Marshmallow 校验错误处理"""
        return validation_error_response(error)


def register_static_routes(app: Flask) -> None:
    """注册静态文件路由（上传文件访问）"""

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """提供上传文件的访问"""
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        return send_from_directory(upload_folder, filename)
