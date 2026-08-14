"""
预约路由
学生在线预约，管理员确认取书
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..utils.response import success_response, error_response
from ..utils.auth import admin_required
from ..utils.audit import log_audit
from ..services import reservation_service

# 创建命名空间
ns = Namespace('reservations', description='预约相关接口')

# ===== 定义模型 =====

reservation_model = ns.model('Reservation', {
    'id': fields.Integer(description='预约ID'),
    'user_id': fields.Integer(description='用户ID'),
    'book_id': fields.Integer(description='图书ID'),
    'book_title': fields.String(description='书名'),
    'user_name': fields.String(description='预约人'),
    'status': fields.String(description='状态（pending/ready/cancelled/completed）'),
    'created_at': fields.String(description='创建时间'),
    'updated_at': fields.String(description='更新时间')
})

reservation_create_model = ns.model('ReservationCreate', {
    'book_id': fields.Integer(required=True, description='图书ID', example=1)
})


# ===== 路由 =====

@ns.route('/')
class ReservationList(Resource):
    """预约列表"""

    @ns.doc('创建预约', security='Bearer')
    @ns.expect(reservation_create_model)
    
    @ns.response(400, '参数错误')
    @jwt_required()
    def post(self):
        """创建预约"""
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or not data.get('book_id'):
            ns.abort(400, '请提供图书ID')

        reservation, error = reservation_service.create_reservation(
            user_id=user_id, book_id=data['book_id']
        )

        if error:
            log_audit(
                action='create',
                resource_type='reservation',
                detail=f'创建预约失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='create',
            resource_type='reservation',
            resource_id=reservation.id,
            detail=f'创建预约: 图书ID {data["book_id"]}',
            new_value=reservation.to_dict()
        )

        return success_response(data=reservation.to_dict(), message='预约成功', code=201)

    @ns.doc('获取所有预约（管理员）', security='Bearer')
    @ns.expect(ns.parser()
        .add_argument('page', type=int, help='页码（默认1）', location='args')
        .add_argument('per_page', type=int, help='每页数量（默认20）', location='args')
        .add_argument('status', type=str, help='筛选状态（pending/ready/cancelled/completed）', location='args')
    )
    @ns.response(200, '获取成功')
    @admin_required
    def get(self):
        """获取所有预约（管理员）"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '').strip() or None
        data = reservation_service.get_all_reservations(page, per_page, status)
        return success_response(data=data)


@ns.route('/my')
class MyReservations(Resource):
    """我的预约"""

    @ns.doc('获取我的预约列表', security='Bearer')
    @ns.expect(ns.parser()
        .add_argument('page', type=int, help='页码（默认1）', location='args')
        .add_argument('per_page', type=int, help='每页数量（默认20）', location='args')
    )
    @ns.response(200, '获取成功')
    @jwt_required()
    def get(self):
        """获取我的预约列表"""
        user_id = int(get_jwt_identity())
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        data = reservation_service.get_user_reservations(user_id, page, per_page)
        return success_response(data=data)


@ns.route('/<int:reservation_id>/cancel')
class CancelReservation(Resource):
    """取消预约"""

    @ns.doc('取消预约', security='Bearer')
    
    @ns.response(400, '取消失败')
    @jwt_required()
    def put(self, reservation_id):
        """取消预约"""
        user_id = int(get_jwt_identity())

        # 获取变更前的数据
        from ..models.reservation import Reservation
        old_reservation = Reservation.query.get(reservation_id)
        old_value = old_reservation.to_dict() if old_reservation else None

        reservation, error = reservation_service.cancel_reservation(reservation_id, user_id)

        if error:
            log_audit(
                action='cancel',
                resource_type='reservation',
                resource_id=reservation_id,
                detail=f'取消预约失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='cancel',
            resource_type='reservation',
            resource_id=reservation_id,
            detail=f'取消预约',
            old_value=old_value,
            new_value=reservation.to_dict()
        )

        return success_response(data=reservation.to_dict(), message='预约已取消')


@ns.route('/<int:reservation_id>/ready')
class MarkReady(Resource):
    """标记就绪"""

    @ns.doc('标记预约就绪（管理员）', security='Bearer')
    
    @ns.response(400, '标记失败')
    @admin_required
    def put(self, reservation_id):
        """标记预约就绪（管理员将书准备好）"""
        # 获取变更前的数据
        from ..models.reservation import Reservation
        old_reservation = Reservation.query.get(reservation_id)
        old_value = old_reservation.to_dict() if old_reservation else None

        reservation, error = reservation_service.mark_ready(reservation_id)

        if error:
            log_audit(
                action='update',
                resource_type='reservation',
                resource_id=reservation_id,
                detail=f'标记预约就绪失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='update',
            resource_type='reservation',
            resource_id=reservation_id,
            detail=f'标记预约就绪',
            old_value=old_value,
            new_value=reservation.to_dict()
        )

        return success_response(data=reservation.to_dict(), message='已标记为就绪')


@ns.route('/<int:reservation_id>/pickup')
class PickupBook(Resource):
    """取书"""

    @ns.doc('取书（管理员确认取书，转为借阅记录）', security='Bearer')
    
    @ns.response(400, '取书失败')
    @admin_required
    def put(self, reservation_id):
        """取书（管理员确认取书，转为借阅记录）"""
        admin_id = int(get_jwt_identity())

        # 获取变更前的数据
        from ..models.reservation import Reservation
        old_reservation = Reservation.query.get(reservation_id)
        old_value = old_reservation.to_dict() if old_reservation else None

        record, error = reservation_service.pickup_book(reservation_id, admin_id)

        if error:
            log_audit(
                action='pickup',
                resource_type='reservation',
                resource_id=reservation_id,
                detail=f'取书失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='pickup',
            resource_type='reservation',
            resource_id=reservation_id,
            detail=f'取书成功，转为借阅记录ID {record.id}',
            old_value=old_value,
            new_value=record.to_dict()
        )

        return success_response(data=record.to_dict(), message='取书成功，已转为借阅记录')
