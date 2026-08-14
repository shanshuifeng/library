"""
图书分类模型
"""
from ..extensions import db


class Category(db.Model):
    """图书分类表（支持多级分类）"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    level = db.Column(db.Integer, default=1)
    sort_order = db.Column(db.Integer, default=0)
    description = db.Column(db.String(200), nullable=True)

    # 自关联：父分类
    parent = db.relationship('Category', remote_side=[id], backref='children')

    # 关联：一个分类下有多本书
    books = db.relationship('Book', backref='category', lazy='dynamic')

    def to_dict(self, include_children=True):
        """转换为字典"""
        data = {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'level': self.level,
            'sort_order': self.sort_order,
            'description': self.description
        }
        if include_children:
            data['children'] = [child.to_dict() for child in self.children]
        return data

    def to_simple_dict(self):
        """转换为简单字典（不含子分类）"""
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'level': self.level
        }

    def __repr__(self):
        return f'<Category {self.name}>'
