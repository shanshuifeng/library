"""
审计日志模型
记录系统中的所有操作，用于安全审计和问题追踪
"""
from datetime import datetime
from ..extensions import db


class AuditLog(db.Model):
    """审计日志表"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # 操作信息
    action = db.Column(db.String(50), nullable=False, index=True, comment='操作类型')
    resource_type = db.Column(db.String(50), nullable=False, comment='资源类型')
    resource_id = db.Column(db.Integer, comment='资源ID')
    detail = db.Column(db.Text, comment='操作详情')

    # 用户信息
    user_id = db.Column(db.Integer, comment='操作用户ID')
    username = db.Column(db.String(50), comment='操作用户名')

    # 请求信息
    ip_address = db.Column(db.String(50), comment='请求IP地址')
    user_agent = db.Column(db.String(500), comment='客户端信息')
    request_method = db.Column(db.String(10), comment='请求方法')
    request_path = db.Column(db.String(500), comment='请求路径')

    # 数据变更
    old_value = db.Column(db.JSON, comment='变更前数据')
    new_value = db.Column(db.JSON, comment='变更后数据')

    # 状态
    status = db.Column(db.String(20), default='success', comment='操作状态: success/failed/error')
    error_message = db.Column(db.Text, comment='错误信息')

    # 时间
    created_at = db.Column(db.DateTime, default=datetime.now, comment='操作时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'detail': self.detail,
            'user_id': self.user_id,
            'username': self.username,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'request_method': self.request_method,
            'request_path': self.request_path,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class AccessLog(db.Model):
    """访问日志表"""
    __tablename__ = 'access_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # 请求信息
    request_method = db.Column(db.String(10), nullable=False, comment='请求方法')
    request_path = db.Column(db.String(500), nullable=False, comment='请求路径')
    query_params = db.Column(db.JSON, comment='查询参数')
    request_body = db.Column(db.JSON, comment='请求体（敏感数据脱敏）')

    # 响应信息
    response_status = db.Column(db.Integer, comment='响应状态码')
    response_time = db.Column(db.Float, comment='响应时间（毫秒）')

    # 用户信息
    user_id = db.Column(db.Integer, comment='用户ID')
    username = db.Column(db.String(50), comment='用户名')
    ip_address = db.Column(db.String(50), comment='IP地址')
    user_agent = db.Column(db.String(500), comment='客户端信息')

    # 时间
    created_at = db.Column(db.DateTime, default=datetime.now, comment='访问时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'request_method': self.request_method,
            'request_path': self.request_path,
            'query_params': self.query_params,
            'request_body': self.request_body,
            'response_status': self.response_status,
            'response_time': self.response_time,
            'user_id': self.user_id,
            'username': self.username,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
