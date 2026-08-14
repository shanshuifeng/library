"""
预约服务层
"""
from datetime import datetime, timedelta, date
from ..models import Reservation, Book, BorrowRecord
from ..extensions import db


def create_reservation(user_id, book_id):
    """创建预约"""
    book = Book.query.get(book_id)
    if not book:
        return None, '图书不存在'

    # 检查是否已有该用户对该书的未完成预约
    existing = Reservation.query.filter_by(
        user_id=user_id, book_id=book_id
    ).filter(
        Reservation.status.in_(['pending', 'ready'])
    ).first()
    if existing:
        return None, '您已预约过该书，请勿重复预约'

    # 检查是否有库存（没有库存也可以预约，排队）
    reservation = Reservation(
        user_id=user_id,
        book_id=book_id,
        status='pending',
        expiry_date=datetime.now() + timedelta(days=3)  # 3天内取书
    )
    db.session.add(reservation)
    db.session.commit()
    return reservation, None


def cancel_reservation(reservation_id, user_id=None):
    """取消预约"""
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return None, '预约记录不存在'

    if user_id and reservation.user_id != user_id:
        return None, '无权操作此预约'

    if reservation.status not in ('pending', 'ready'):
        return None, '当前状态不允许取消'

    reservation.status = 'cancelled'
    reservation.processed_at = datetime.now()
    db.session.commit()
    return reservation, None


def pickup_book(reservation_id, admin_id):
    """取书（管理员操作：预约 → 借阅）"""
    from flask import current_app

    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return None, '预约记录不存在'

    if reservation.status != 'ready':
        return None, '该预约尚未就绪，无法取书'

    book = Book.query.get(reservation.book_id)
    if not book or book.stock <= 0:
        return None, '图书库存不足'

    borrow_days = current_app.config.get('BORROW_DAYS', 30)

    record = BorrowRecord(
        user_id=reservation.user_id,
        book_id=reservation.book_id,
        borrow_date=date.today(),
        due_date=date.today() + timedelta(days=borrow_days),
        status='borrowed',
        renew_count=0,
        fine=0
    )
    db.session.add(record)
    db.session.flush()

    book.stock -= 1

    reservation.status = 'picked_up'
    reservation.processed_at = datetime.now()
    reservation.borrow_record_id = record.id

    db.session.commit()
    return record, None


def mark_ready(reservation_id):
    """标记预约就绪（管理员操作：书已准备好可借）"""
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return None, '预约记录不存在'

    if reservation.status != 'pending':
        return None, '当前状态不允许标记为就绪'

    reservation.status = 'ready'
    reservation.processed_at = datetime.now()
    db.session.commit()
    return reservation, None


def get_user_reservations(user_id, page=1, per_page=20):
    """获取用户的预约列表"""
    query = Reservation.query.filter_by(user_id=user_id).order_by(
        Reservation.created_at.desc()
    )
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }


def get_all_reservations(page=1, per_page=20, status=None):
    """获取所有预约（管理员）"""
    query = Reservation.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Reservation.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }
