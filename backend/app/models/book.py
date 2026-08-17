"""
图书模型
"""
from datetime import datetime
from ..extensions import db


class Book(db.Model):
    """图书表"""
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(100), nullable=True, index=True)
    isbn = db.Column(db.String(20), unique=True, nullable=True, index=True)
    publisher = db.Column(db.String(100), nullable=True)
    publish_date = db.Column(db.Date, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=True)
    stock = db.Column(db.Integer, default=0, nullable=False)
    total_stock = db.Column(db.Integer, default=0, nullable=False)  # 总库存
    description = db.Column(db.Text, nullable=True)
    cover_image = db.Column(db.String(500), nullable=True)
    location = db.Column(db.String(100), nullable=True)  # 馆藏位置
    avg_rating = db.Column(db.Numeric(3, 2), default=0, nullable=False)  # 平均评分（1~5）
    review_count = db.Column(db.Integer, default=0, nullable=False)  # 评价数量
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联：一本图书有多条借阅记录
    borrow_records = db.relationship('BorrowRecord', backref='book', lazy='dynamic')
    # 关联：一本图书有多条评价
    reviews = db.relationship('BookReview', backref='book', lazy='dynamic')

    @property
    def available_stock(self):
        """可借库存"""
        return self.stock

    @property
    def is_available(self):
        """是否有库存"""
        return self.stock > 0

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn,
            'publisher': self.publisher,
            'publish_date': self.publish_date.isoformat() if self.publish_date else None,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'price': float(self.price) if self.price else None,
            'stock': self.stock,
            'total_stock': self.total_stock,
            'description': self.description,
            'cover_image': self.cover_image,
            'location': self.location,
            'avg_rating': float(self.avg_rating) if self.avg_rating else 0,
            'review_count': self.review_count or 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_simple_dict(self):
        """转换为简单字典"""
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn,
            'stock': self.stock,
            'cover_image': self.cover_image
        }

    def __repr__(self):
        return f'<Book {self.title}>'
