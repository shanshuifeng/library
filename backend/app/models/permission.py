"""
权限与角色模型
"""
from datetime import datetime
from ..extensions import db


# 角色-权限 关联表
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
)


# 用户-角色 关联表
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
)


class Permission(db.Model):
    """权限表"""
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(100), unique=True, nullable=False)  # book:create
    name = db.Column(db.String(50), nullable=False)  # 新增图书
    group = db.Column(db.String(50), nullable=False, default='其他')  # 分组：图书管理
    description = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'group': self.group,
            'description': self.description
        }


class Role(db.Model):
    """角色表"""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    is_system = db.Column(db.Boolean, default=False)  # 系统角色不可删除

    permissions = db.relationship('Permission', secondary=role_permissions,
                                  backref=db.backref('roles', lazy='dynamic'),
                                  lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_system': self.is_system,
            'permission_count': self.permissions.count()
        }

    def to_dict_detail(self):
        return {
            **self.to_dict(),
            'permissions': [p.to_dict() for p in self.permissions.all()]
        }
