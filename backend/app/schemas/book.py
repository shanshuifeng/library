"""
图书与分类相关 Schema
"""
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from datetime import datetime


class BookCreateSchema(Schema):
    """创建图书 Schema"""
    title = fields.String(required=True, validate=[
        validate.Length(min=1, max=200, error='书名长度应为1-200个字符')
    ])
    author = fields.String(load_default=None, validate=[
        validate.Length(max=100)
    ])
    isbn = fields.String(load_default=None, validate=[
        validate.Length(max=20)
    ])
    publisher = fields.String(load_default=None, validate=[
        validate.Length(max=100)
    ])
    publish_date = fields.Date(load_default=None, error_messages={'invalid': '出版日期格式不正确，应为 YYYY-MM-DD'})
    category_id = fields.Integer(load_default=None)
    price = fields.Decimal(load_default=None, places=2, validate=[
        validate.Range(min=0, error='价格不能为负数')
    ])
    stock = fields.Integer(load_default=0, validate=[
        validate.Range(min=0, error='库存不能为负数')
    ])
    total_stock = fields.Integer(load_default=0, validate=[
        validate.Range(min=0, error='总库存不能为负数')
    ])
    description = fields.String(load_default=None)
    cover_image = fields.String(load_default=None, validate=[
        validate.Length(max=500)
    ])
    location = fields.String(load_default=None, validate=[
        validate.Length(max=100)
    ])

    @validates('isbn')
    def validate_isbn(self, value):
        """校验 ISBN 格式（支持 ISBN-10 和 ISBN-13）"""
        if value:
            # 移除连字符和空格
            clean_isbn = value.replace('-', '').replace(' ', '')
            if not re.match(r'^\d{10}(\d{3})?$', clean_isbn):
                raise ValidationError('ISBN 格式不正确')

    @post_load
    def process_isbn(self, data, **kwargs):
        """处理 ISBN 格式"""
        if data.get('isbn'):
            data['isbn'] = data['isbn'].replace('-', '').replace(' ', '')
        return data


# 需要导入 re
import re


class BookUpdateSchema(Schema):
    """更新图书 Schema"""
    title = fields.String(load_default=None, validate=[
        validate.Length(min=1, max=200, error='书名长度应为1-200个字符')
    ])
    author = fields.String(load_default=None, validate=[
        validate.Length(max=100)
    ])
    isbn = fields.String(load_default=None, validate=[
        validate.Length(max=20)
    ])
    publisher = fields.String(load_default=None, validate=[
        validate.Length(max=100)
    ])
    publish_date = fields.Date(load_default=None, error_messages={'invalid': '出版日期格式不正确'})
    category_id = fields.Integer(load_default=None)
    price = fields.Decimal(load_default=None, places=2, validate=[
        validate.Range(min=0, error='价格不能为负数')
    ])
    stock = fields.Integer(load_default=None, validate=[
        validate.Range(min=0, error='库存不能为负数')
    ])
    total_stock = fields.Integer(load_default=None, validate=[
        validate.Range(min=0, error='总库存不能为负数')
    ])
    description = fields.String(load_default=None)
    cover_image = fields.String(load_default=None, validate=[
        validate.Length(max=500)
    ])
    location = fields.String(load_default=None, validate=[
        validate.Length(max=100)
    ])


class BookListSchema(Schema):
    """图书列表输出 Schema"""
    id = fields.Integer()
    title = fields.String()
    author = fields.String()
    isbn = fields.String()
    publisher = fields.String()
    publish_date = fields.Date(format='%Y-%m-%d')
    category_id = fields.Integer()
    category_name = fields.String()
    price = fields.Decimal(places=2)
    stock = fields.Integer()
    total_stock = fields.Integer()
    cover_image = fields.String()
    location = fields.String()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')


class BookDetailSchema(Schema):
    """图书详情输出 Schema"""
    id = fields.Integer()
    title = fields.String()
    author = fields.String()
    isbn = fields.String()
    publisher = fields.String()
    publish_date = fields.Date(format='%Y-%m-%d')
    category_id = fields.Integer()
    category_name = fields.String()
    price = fields.Decimal(places=2)
    stock = fields.Integer()
    total_stock = fields.Integer()
    description = fields.String()
    cover_image = fields.String()
    location = fields.String()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')


class CategoryCreateSchema(Schema):
    """创建分类 Schema"""
    name = fields.String(required=True, validate=[
        validate.Length(min=1, max=50, error='分类名称长度应为1-50个字符')
    ])
    parent_id = fields.Integer(load_default=0)
    sort_order = fields.Integer(load_default=0)
    description = fields.String(load_default=None, validate=[
        validate.Length(max=200)
    ])


class CategoryUpdateSchema(Schema):
    """更新分类 Schema"""
    name = fields.String(load_default=None, validate=[
        validate.Length(min=1, max=50, error='分类名称长度应为1-50个字符')
    ])
    parent_id = fields.Integer(load_default=None)
    sort_order = fields.Integer(load_default=None)
    description = fields.String(load_default=None, validate=[
        validate.Length(max=200)
    ])


class CategorySchema(Schema):
    """分类输出 Schema"""
    id = fields.Integer()
    name = fields.String()
    parent_id = fields.Integer()
    level = fields.Integer()
    sort_order = fields.Integer()
    description = fields.String()
    children = fields.List(fields.Nested(lambda: CategorySchema()))
