"""
借阅相关 Schema
"""
from marshmallow import Schema, fields, validate


class BorrowCreateSchema(Schema):
    """借书 Schema"""
    book_id = fields.Integer(required=True, validate=[
        validate.Range(min=1, error='图书ID必须为正整数')
    ])
    borrow_days = fields.Integer(load_default=None, validate=[
        validate.Range(min=1, max=180, error='借阅天数应为1-180天')
    ])


class BorrowListSchema(Schema):
    """借阅记录列表输出 Schema"""
    id = fields.Integer()
    user_id = fields.Integer()
    username = fields.String()
    user_real_name = fields.String()
    book_id = fields.Integer()
    book_title = fields.String()
    book_author = fields.String()
    book_cover = fields.String()
    borrow_date = fields.Date(format='%Y-%m-%d')
    due_date = fields.Date(format='%Y-%m-%d')
    return_date = fields.Date(format='%Y-%m-%d')
    renew_count = fields.Integer()
    fine = fields.Decimal(places=2)
    status = fields.String()
    is_overdue = fields.Boolean()
    days_overdue = fields.Integer()
    remaining_days = fields.Integer()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')


class BorrowDetailSchema(Schema):
    """借阅记录详情输出 Schema"""
    id = fields.Integer()
    user_id = fields.Integer()
    username = fields.String()
    user_real_name = fields.String()
    book_id = fields.Integer()
    book_title = fields.String()
    book_author = fields.String()
    book_cover = fields.String()
    borrow_date = fields.Date(format='%Y-%m-%d')
    due_date = fields.Date(format='%Y-%m-%d')
    return_date = fields.Date(format='%Y-%m-%d')
    renew_count = fields.Integer()
    fine = fields.Decimal(places=2)
    status = fields.String()
    is_overdue = fields.Boolean()
    days_overdue = fields.Integer()
    remaining_days = fields.Integer()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
