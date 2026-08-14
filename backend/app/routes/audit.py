"""
审计日志路由
提供审计日志查询和统计功能
"""
from datetime import datetime, timedelta
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required

from ..utils.response import success_response, paginate_response
from ..utils.auth import admin_required
from ..models.audit import AuditLog, AccessLog
from ..extensions import db

# 创建命名空间
ns = Namespace('audit', description='审计日志相关接口')

# ===== 定义模型 =====

audit_log_model = ns.model('AuditLog', {
    'id': fields.Integer(description='日志ID'),
    'action': fields.String(description='操作类型'),
    'resource_type': fields.String(description='资源类型'),
    'resource_id': fields.Integer(description='资源ID'),
    'detail': fields.String(description='操作详情'),
    'user_id': fields.Integer(description='用户ID'),
    'username': fields.String(description='用户名'),
    'ip_address': fields.String(description='IP地址'),
    'request_method': fields.String(description='请求方法'),
    'request_path': fields.String(description='请求路径'),
    'old_value': fields.Raw(description='变更前数据'),
    'new_value': fields.Raw(description='变更后数据'),
    'status': fields.String(description='操作状态'),
    'error_message': fields.String(description='错误信息'),
    'created_at': fields.String(description='操作时间')
})

access_log_model = ns.model('AccessLog', {
    'id': fields.Integer(description='日志ID'),
    'request_method': fields.String(description='请求方法'),
    'request_path': fields.String(description='请求路径'),
    'query_params': fields.Raw(description='查询参数'),
    'response_status': fields.Integer(description='响应状态码'),
    'response_time': fields.Float(description='响应时间(ms)'),
    'user_id': fields.Integer(description='用户ID'),
    'username': fields.String(description='用户名'),
    'ip_address': fields.String(description='IP地址'),
    'created_at': fields.String(description='访问时间')
})

stats_model = ns.model('AuditStats', {
    'total_count': fields.Integer(description='总日志数'),
    'today_count': fields.Integer(description='今日日志数'),
    'action_stats': fields.List(fields.Raw, description='操作类型统计'),
    'user_stats': fields.List(fields.Raw, description='用户操作统计')
})


# ===== 审计日志路由 =====

@ns.route('/logs')
class AuditLogList(Resource):
    """审计日志列表"""

    @ns.doc('获取审计日志列表', security='Bearer')
    @ns.expect(ns.parser()
        .add_argument('page', type=int, help='页码', location='args')
        .add_argument('per_page', type=int, help='每页数量', location='args')
        .add_argument('action', type=str, help='操作类型', location='args')
        .add_argument('resource_type', type=str, help='资源类型', location='args')
        .add_argument('user_id', type=int, help='用户ID', location='args')
        .add_argument('status', type=str, help='操作状态', location='args')
        .add_argument('start_date', type=str, help='开始日期 YYYY-MM-DD', location='args')
        .add_argument('end_date', type=str, help='结束日期 YYYY-MM-DD', location='args')
        .add_argument('keyword', type=str, help='搜索关键词', location='args')
    )
    @admin_required
    def get(self):
        """获取审计日志列表（管理员）"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = AuditLog.query

        # 筛选条件
        action = request.args.get('action')
        if action:
            query = query.filter(AuditLog.action == action)

        resource_type = request.args.get('resource_type')
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)

        user_id = request.args.get('user_id', type=int)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        status = request.args.get('status')
        if status:
            query = query.filter(AuditLog.status == status)

        start_date = request.args.get('start_date')
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(AuditLog.created_at >= start)
            except ValueError:
                pass

        end_date = request.args.get('end_date')
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(AuditLog.created_at < end)
            except ValueError:
                pass

        keyword = request.args.get('keyword')
        if keyword:
            query = query.filter(
                db.or_(
                    AuditLog.detail.ilike(f'%{keyword}%'),
                    AuditLog.username.ilike(f'%{keyword}%'),
                    AuditLog.resource_type.ilike(f'%{keyword}%')
                )
            )

        # 按时间倒序
        query = query.order_by(AuditLog.created_at.desc())

        return paginate_response(
            query=query,
            schema=None,
            page=page,
            per_page=per_page
        )


@ns.route('/logs/<int:log_id>')
class AuditLogDetail(Resource):
    """审计日志详情"""

    @ns.doc('获取审计日志详情', security='Bearer')
    @admin_required
    def get(self, log_id):
        """获取审计日志详情"""
        log = AuditLog.query.get(log_id)
        if not log:
            ns.abort(400, '日志不存在')

        return success_response(data=log.to_dict())


@ns.route('/access-logs')
class AccessLogList(Resource):
    """访问日志列表"""

    @ns.doc('获取访问日志列表', security='Bearer')
    @ns.expect(ns.parser()
        .add_argument('page', type=int, help='页码', location='args')
        .add_argument('per_page', type=int, help='每页数量', location='args')
        .add_argument('user_id', type=int, help='用户ID', location='args')
        .add_argument('path', type=str, help='请求路径', location='args')
        .add_argument('status', type=int, help='响应状态码', location='args')
        .add_argument('start_date', type=str, help='开始日期', location='args')
        .add_argument('end_date', type=str, help='结束日期', location='args')
    )
    @admin_required
    def get(self):
        """获取访问日志列表（管理员）"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = AccessLog.query

        # 筛选条件
        user_id = request.args.get('user_id', type=int)
        if user_id:
            query = query.filter(AccessLog.user_id == user_id)

        path = request.args.get('path')
        if path:
            query = query.filter(AccessLog.request_path.ilike(f'%{path}%'))

        status = request.args.get('status', type=int)
        if status:
            query = query.filter(AccessLog.response_status == status)

        start_date = request.args.get('start_date')
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(AccessLog.created_at >= start)
            except ValueError:
                pass

        end_date = request.args.get('end_date')
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(AccessLog.created_at < end)
            except ValueError:
                pass

        query = query.order_by(AccessLog.created_at.desc())

        return paginate_response(
            query=query,
            schema=None,
            page=page,
            per_page=per_page
        )


@ns.route('/stats')
class AuditStats(Resource):
    """审计统计"""

    @ns.doc('获取审计统计信息', security='Bearer')
    @admin_required
    def get(self):
        """获取审计统计信息"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # 总数
        total_count = AuditLog.query.count()

        # 今日数量
        today_count = AuditLog.query.filter(AuditLog.created_at >= today).count()

        # 操作类型统计（近7天）
        week_ago = today - timedelta(days=7)
        action_stats = db.session.query(
            AuditLog.action,
            db.func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.created_at >= week_ago
        ).group_by(
            AuditLog.action
        ).order_by(
            db.desc('count')
        ).limit(10).all()

        # 用户操作统计（近7天）
        user_stats = db.session.query(
            AuditLog.username,
            db.func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.created_at >= week_ago,
            AuditLog.username.isnot(None)
        ).group_by(
            AuditLog.username
        ).order_by(
            db.desc('count')
        ).limit(10).all()

        return success_response(data={
            'total_count': total_count,
            'today_count': today_count,
            'action_stats': [{'action': a[0], 'count': a[1]} for a in action_stats],
            'user_stats': [{'username': u[0], 'count': u[1]} for u in user_stats]
        })


@ns.route('/cleanup')
class AuditCleanup(Resource):
    """审计日志清理"""

    @ns.doc('清理过期审计日志（保留90天）', security='Bearer')
    @admin_required
    def delete(self):
        """清理过期审计日志"""
        from flask import current_app
        retention_days = current_app.config.get('AUDIT_RETENTION_DAYS', 90)
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        # 删除过期审计日志
        audit_deleted = AuditLog.query.filter(
            AuditLog.created_at < cutoff_date
        ).delete()

        # 删除过期访问日志
        access_deleted = AccessLog.query.filter(
            AccessLog.created_at < cutoff_date
        ).delete()

        db.session.commit()

        return success_response(data={
            'audit_deleted': audit_deleted,
            'access_deleted': access_deleted
        }, message=f'清理完成：审计日志 {audit_deleted} 条，访问日志 {access_deleted} 条')
