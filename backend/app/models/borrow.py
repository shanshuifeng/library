"""
借阅记录模型
"""
from datetime import datetime, date, timedelta
from ..extensions import db


class BorrowRecord(db.Model):
    """借阅记录表"""
    __tablename__ = 'borrow_records'
    __table_args__ = (
        db.Index('idx_borrow_status', 'status'),
        db.Index('idx_borrow_date', 'borrow_date'),
        db.Index('idx_borrow_return_date', 'return_date'),
        db.Index('idx_borrow_user_status', 'user_id', 'status'),
        db.Index('idx_borrow_due_date', 'due_date'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    borrow_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    renew_count = db.Column(db.Integer, default=0)
    fine = db.Column(db.Numeric(10, 2), default=0)
    status = db.Column(db.String(10), default='borrowed', nullable=False)  # borrowed/returned/overdue
    created_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def is_overdue(self):
        """是否逾期"""
        if self.status == 'returned':
            return False
        return date.today() > self.due_date

    @property
    def days_overdue(self):
        """逾期天数"""
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days

    @property
    def remaining_days(self):
        """剩余借阅天数"""
        if self.status == 'returned':
            return 0
        remaining = (self.due_date - date.today()).days
        return max(0, remaining)

    @classmethod
    def calculate_fine(cls, due_date, return_date=None):
        """
        计算逾期罚款

        Args:
            due_date: 到期日期
            return_date: 归还日期（None 表示未归还）

        Returns:
            罚款金额
        """
        if return_date is None:
            return_date = date.today()

        if return_date <= due_date:
            return 0

        overdue_days = (return_date - due_date).days
        # 每天罚款 0.1 元
        return overdue_days * 0.1

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'user_real_name': self.user.real_name if self.user else None,
            'book_id': self.book_id,
            'book_title': self.book.title if self.book else None,
            'book_author': self.book.author if self.book else None,
            'book_cover': self.book.cover_image if self.book else None,
            'borrow_date': self.borrow_date.isoformat() if self.borrow_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'renew_count': self.renew_count,
            'fine': float(self.fine) if self.fine else 0,
            'status': self.status,
            'is_overdue': self.is_overdue,
            'days_overdue': self.days_overdue,
            'remaining_days': self.remaining_days,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def to_simple_dict(self):
        """转换为简单字典"""
        return {
            'id': self.id,
            'book_title': self.book.title if self.book else None,
            'borrow_date': self.borrow_date.isoformat() if self.borrow_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status
        }

    def __repr__(self):
        return f'<BorrowRecord {self.id}: User {self.user_id} -> Book {self.book_id}>'
