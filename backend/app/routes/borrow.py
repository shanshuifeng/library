"""
借阅路由
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..utils.response import success_response, error_response, paginate_response
from ..utils.auth import admin_required, role_required, get_current_user_id
from ..utils.audit import log_audit
from ..services import borrow_service

# 创建命名空间
ns = Namespace('borrows', description='借阅相关接口')

# ===== 定义模型 =====

borrow_record_model = ns.model('BorrowRecord', {
    'id': fields.Integer(description='借阅记录ID'),
    'user_id': fields.Integer(description='用户ID'),
    'book_id': fields.Integer(description='图书ID'),
    'book_title': fields.String(description='书名'),
    'user_name': fields.String(description='借阅人'),
    'borrow_date': fields.String(description='借阅日期'),
    'due_date': fields.String(description='应还日期'),
    'return_date': fields.String(description='实际归还日期'),
    'status': fields.String(description='状态（borrowed/returned/overdue）'),
    'renew_count': fields.Integer(description='续借次数'),
    'fine': fields.Float(description='罚款金额'),
    'created_at': fields.String(description='创建时间')
})

borrow_request_model = ns.model('BorrowRequest', {
    'book_id': fields.Integer(required=True, description='图书ID', example=1),
    'borrow_days': fields.Integer(description='借阅天数（可选，默认从配置获取）', example=30)
})


# ===== 路由 =====

@ns.route('/')
class BorrowList(Resource):
    """借阅记录"""

    @ns.doc('借书', security='Bearer')
    @ns.expect(borrow_request_model)
    
    @ns.response(400, '参数错误')
    @jwt_required()
    def post(self):
        """借书"""
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data:
            ns.abort(400, '请求数据不能为空')

        book_id = data.get('book_id')
        if not book_id:
            ns.abort(400, '图书ID不能为空')

        borrow_days = data.get('borrow_days')

        record, error = borrow_service.borrow_book(
            user_id=user_id,
            book_id=book_id,
            borrow_days=borrow_days
        )

        if error:
            # 记录失败审计日志
            log_audit(
                action='borrow',
                resource_type='borrow',
                detail=f'借书失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='borrow',
            resource_type='borrow',
            resource_id=record.id,
            detail=f'借阅图书成功，应还日期: {record.due_date}',
            new_value=record.to_dict()
        )

        return success_response(data=record.to_dict(), message='借阅成功', code=201)

    @ns.doc('获取借阅记录列表', security='Bearer')
    @ns.expect(ns.parser()
        .add_argument('page', type=int, help='页码（默认1）', location='args')
        .add_argument('per_page', type=int, help='每页数量（默认20）', location='args')
        .add_argument('status', type=str, help='筛选状态（borrowed/returned/overdue）', location='args')
    )
    @ns.response(200, '获取成功')
    @jwt_required()
    def get(self):
        """获取借阅记录列表（管理员可查看所有，普通用户只能查看自己的）"""
        user_id = int(get_jwt_identity())

        # 检查是否是管理员
        from ..models.user import User
        user = User.query.get(user_id)
        is_admin = user and user.role == 'admin'

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '').strip()

        # 管理员查看全部，普通用户只查看自己的
        query = borrow_service.get_borrow_list(
            user_id=None if is_admin else user_id,
            page=page,
            per_page=per_page,
            status=status if status else None
        )

        return paginate_response(
            query=query,
            schema=BorrowRecordSchema(),
            page=page,
            per_page=per_page
        )


@ns.route('/<int:record_id>/return')
class ReturnBook(Resource):
    """还书"""

    @ns.doc('还书', security='Bearer')
    
    @ns.response(400, '归还失败')
    @jwt_required()
    def put(self, record_id):
        """还书"""
        user_id = int(get_jwt_identity())

        # 获取变更前的数据
        from ..models.borrow import BorrowRecord
        old_record = BorrowRecord.query.get(record_id)
        old_value = old_record.to_dict() if old_record else None

        record, error = borrow_service.return_book(
            record_id=record_id,
            user_id=user_id
        )

        if error:
            # 记录失败审计日志
            log_audit(
                action='return',
                resource_type='borrow',
                resource_id=record_id,
                detail=f'还书失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='return',
            resource_type='borrow',
            resource_id=record_id,
            detail=f'归还图书成功',
            old_value=old_value,
            new_value=record.to_dict()
        )

        return success_response(data=record.to_dict(), message='归还成功')


@ns.route('/<int:record_id>/renew')
class RenewBook(Resource):
    """续借"""

    @ns.doc('续借', security='Bearer')
    
    @ns.response(400, '续借失败')
    @jwt_required()
    def put(self, record_id):
        """续借"""
        user_id = int(get_jwt_identity())

        # 获取变更前的数据
        from ..models.borrow import BorrowRecord
        old_record = BorrowRecord.query.get(record_id)
        old_value = old_record.to_dict() if old_record else None

        record, error = borrow_service.renew_book(
            record_id=record_id,
            user_id=user_id
        )

        if error:
            # 记录失败审计日志
            log_audit(
                action='renew',
                resource_type='borrow',
                resource_id=record_id,
                detail=f'续借失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='renew',
            resource_type='borrow',
            resource_id=record_id,
            detail=f'续借成功，新应还日期: {record.due_date}',
            old_value=old_value,
            new_value=record.to_dict()
        )

        return success_response(data=record.to_dict(), message='续借成功')


@ns.route('/user/<int:user_id>')
class UserBorrows(Resource):
    """指定用户的借阅记录"""

    @ns.doc('获取指定用户的借阅记录', security='Bearer')
    @ns.expect(ns.parser()
        .add_argument('page', type=int, help='页码（默认1）', location='args')
        .add_argument('per_page', type=int, help='每页数量（默认20）', location='args')
        .add_argument('status', type=str, help='筛选状态（borrowed/returned/overdue）', location='args')
    )
    @ns.response(200, '获取成功')
    @ns.response(403, '无权查看')
    @jwt_required()
    def get(self, user_id):
        """获取指定用户的借阅记录（管理员可查看任何用户，普通用户只能查看自己的）"""
        current_user_id = int(get_jwt_identity())

        # 权限检查：普通用户只能查看自己的借阅记录
        from ..models.user import User
        current_user = User.query.get(current_user_id)
        if not current_user:
            ns.abort(404, '用户不存在')

        if current_user.role != 'admin' and current_user_id != user_id:
            ns.abort(403, '无权查看他人的借阅记录')

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '').strip()

        query = borrow_service.get_borrow_list(
            user_id=user_id,
            page=page,
            per_page=per_page,
            status=status if status else None
        )

        return paginate_response(
            query=query,
            schema=BorrowRecordSchema(),
            page=page,
            per_page=per_page
        )


class BorrowRecordSchema:
    """借阅记录序列化器（用于分页列表）"""

    def dump(self, records):
        """序列化借阅记录列表"""
        return [record.to_dict() for record in records]
