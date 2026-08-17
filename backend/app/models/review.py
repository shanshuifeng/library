"""
图书评价模型
"""
from datetime import datetime
from ..extensions import db


class BookReview(db.Model):
    """图书评价表（读者对图书的评分与评论）"""
    __tablename__ = 'book_reviews'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)  # 评分：1~5 星
    content = db.Column(db.Text, nullable=True)     # 评价内容（可选）
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联：一条评价属于一个用户（backref 与 BorrowRecord 的 backref='book' 分属不同模型，不冲突）
    user = db.relationship('User', backref=db.backref('book_reviews', lazy='dynamic'))

    __table_args__ = (
        # 同一用户对同一本书仅保留一条评价（提交时按 user_id+book_id 更新）
        db.Index('idx_review_book_user', 'book_id', 'user_id'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'book_id': self.book_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'real_name': self.user.real_name if self.user else None,
            'rating': self.rating,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<BookReview {self.id}: User {self.user_id} -> Book {self.book_id}>'
