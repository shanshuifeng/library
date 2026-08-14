"""
预约模型
学生在线预约，线下取书
"""
from datetime import datetime, timedelta
from ..extensions import db


class Reservation(db.Model):
    """预约表"""
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    # pending: 待处理, ready: 已就绪可借, cancelled: 已取消,
    # picked_up: 已取书(转为借阅), expired: 已过期
    created_at = db.Column(db.DateTime, default=datetime.now)
    expiry_date = db.Column(db.DateTime, nullable=True)  # 预约过期时间
    processed_at = db.Column(db.DateTime, nullable=True)  # 处理时间
    borrow_record_id = db.Column(db.Integer, db.ForeignKey('borrow_records.id'), nullable=True)

    user = db.relationship('User', backref=db.backref('reservations', lazy='dynamic'))
    book = db.relationship('Book', backref=db.backref('reservations', lazy='dynamic'))
    borrow_record = db.relationship('BorrowRecord', backref='reservation')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'real_name': self.user.real_name if self.user else None,
            'book_id': self.book_id,
            'book_title': self.book.title if self.book else None,
            'book_author': self.book.author if self.book else None,
            'book_isbn': self.book.isbn if self.book else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'borrow_record_id': self.borrow_record_id,
        }

    def __repr__(self):
        return f'<Reservation {self.id}: user={self.user_id} book={self.book_id}>'
