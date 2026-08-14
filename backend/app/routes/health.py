"""
健康检查路由
用于监控系统状态，无需认证
"""
from datetime import datetime
from flask import current_app
from flask_restx import Namespace, Resource, fields

from ..utils.response import success_response

# 创建命名空间
ns = Namespace('health', description='系统健康检查')

# 定义响应模型
health_model = ns.model('Health', {
    'status': fields.String(description='系统状态'),
    'timestamp': fields.String(description='当前时间'),
    'version': fields.String(description='API 版本'),
    'database': fields.String(description='数据库状态')
})


@ns.route('/')
class HealthCheck(Resource):
    """系统健康检查"""

    @ns.doc('系统健康检查（无需认证）')
    @ns.response(200, '系统正常')
    @ns.response(503, '系统异常')
    def get(self):
        """检查系统健康状态"""
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'database': 'unknown'
        }

        # 检查数据库连接
        try:
            from ..extensions import db
            db.session.execute(db.text('SELECT 1'))
            health_data['database'] = 'connected'
        except Exception as e:
            health_data['database'] = 'disconnected'
            health_data['status'] = 'unhealthy'
            return success_response(data=health_data, code=503)

        return success_response(data=health_data)
