"""
借阅服务层
"""
from datetime import date, timedelta
from ..models.borrow import BorrowRecord
from ..models.book import Book
from ..models.user import User
from ..extensions import db


def borrow_book(user_id, book_id, borrow_days=None):
    """
    借书

    Args:
        user_id: 用户ID
        book_id: 图书ID
        borrow_days: 借阅天数（默认从配置获取）

    Returns:
        (BorrowRecord, None) 成功返回借阅记录
        (None, str) 失败返回错误信息
    """
    from flask import current_app

    # 获取用户
    user = User.query.get(user_id)
    if not user:
        return None, '用户不存在'

    if user.status != 1:
        return None, '账号已被禁用'

    # 获取图书
    book = Book.query.get(book_id)
    if not book:
        return None, '图书不存在'

    # 检查库存
    if not book.is_available:
        return None, '图书库存不足'

    # 检查借阅上限
    max_borrow = current_app.config.get('MAX_BORROW_COUNT', {}).get(user.role, 5)
    current_borrowed = BorrowRecord.query.filter_by(
        user_id=user_id, status='borrowed'
    ).count()

    if current_borrowed >= max_borrow:
        return None, f'已达到借阅上限（最多{max_borrow}本）'

    # 检查是否已借阅同一本书
    existing = BorrowRecord.query.filter_by(
        user_id=user_id, book_id=book_id, status='borrowed'
    ).first()
    if existing:
        return None, '您已借阅此书，请先归还后再借'

    # 计算到期日期
    if borrow_days is None:
        borrow_days = current_app.config.get('BORROW_DAYS', 30)

    due_date = date.today() + timedelta(days=borrow_days)

    # 创建借阅记录
    record = BorrowRecord(
        user_id=user_id,
        book_id=book_id,
        borrow_date=date.today(),
        due_date=due_date,
        status='borrowed'
    )

    # 扣减库存
    book.stock -= 1

    db.session.add(record)
    db.session.commit()

    return record, None


def return_book(record_id, user_id=None):
    """
    还书

    Args:
        record_id: 借阅记录ID
        user_id: 用户ID（可选，用于验证权限）

    Returns:
        (BorrowRecord, None) 成功返回借阅记录
        (None, str) 失败返回错误信息
    """
    from flask import current_app
    from ..models.user import User

    record = BorrowRecord.query.get(record_id)
    if not record:
        return None, '借阅记录不存在'

    # 验证用户权限（管理员可以操作任何记录）
    current_user = User.query.get(user_id) if user_id else None
    is_admin = current_user and current_user.role == 'admin'
    if user_id and record.user_id != user_id and not is_admin:
        return None, '无权操作此借阅记录'

    if record.status == 'returned':
        return None, '该书已归还'

    # 计算罚款
    fine_per_day = current_app.config.get('FINE_PER_DAY', 0.1)
    fine = 0
    if record.is_overdue:
        fine = record.days_overdue * fine_per_day

    # 更新借阅记录
    record.return_date = date.today()
    record.fine = fine
    record.status = 'returned'

    # 恢复库存
    book = Book.query.get(record.book_id)
    if book:
        book.stock += 1

    db.session.commit()

    return record, None


def renew_book(record_id, user_id=None):
    """
    续借

    Args:
        record_id: 借阅记录ID
        user_id: 用户ID（可选，用于验证权限）

    Returns:
        (BorrowRecord, None) 成功返回借阅记录
        (None, str) 失败返回错误信息
    """
    from flask import current_app
    from ..models.user import User

    record = BorrowRecord.query.get(record_id)
    if not record:
        return None, '借阅记录不存在'

    # 验证用户权限（管理员可以操作任何记录）
    current_user = User.query.get(user_id) if user_id else None
    is_admin = current_user and current_user.role == 'admin'
    if user_id and record.user_id != user_id and not is_admin:
        return None, '无权操作此借阅记录'

    if record.status != 'borrowed':
        return None, '只能续借借阅中的图书'

    # 检查续借次数上限
    max_renew = current_app.config.get('MAX_RENEW_COUNT', 2)
    if record.renew_count >= max_renew:
        return None, f'已达到续借上限（最多{max_renew}次）'

    # 续借：延长到期日期
    renew_days = current_app.config.get('RENEW_DAYS', 30)
    record.due_date = record.due_date + timedelta(days=renew_days)
    record.renew_count += 1

    db.session.commit()

    return record, None


def get_borrow_list(user_id=None, page=1, per_page=20, status=None):
    """
    获取借阅记录列表

    Args:
        user_id: 用户ID（None表示管理员查看全部）
        page: 页码
        per_page: 每页数量
        status: 筛选状态

    Returns:
        SQLAlchemy 分页查询对象
    """
    query = BorrowRecord.query

    # 用户只能查看自己的借阅记录
    if user_id:
        query = query.filter_by(user_id=user_id)

    # 状态筛选
    if status:
        query = query.filter_by(status=status)

    # 按创建时间降序排列
    query = query.order_by(BorrowRecord.created_at.desc())

    return query


def get_user_active_borrow_count(user_id):
    """
    获取用户当前借阅数量

    Args:
        user_id: 用户ID

    Returns:
        当前借阅数量
    """
    return BorrowRecord.query.filter_by(
        user_id=user_id, status='borrowed'
    ).count()
