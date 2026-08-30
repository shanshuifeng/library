"""
用户相关 Schema
"""
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
import re


def validate_password_strength(value):
    """校验密码强度：至少包含字母和数字"""
    if not re.search(r'[A-Za-z]', value):
        raise ValidationError('密码必须包含至少一个字母')
    if not re.search(r'\d', value):
        raise ValidationError('密码必须包含至少一个数字')


class UserLoginSchema(Schema):
    """用户登录 Schema"""
    username = fields.String(required=True, validate=[
        validate.Length(min=2, max=50, error='用户名长度应为2-50个字符')
    ])
    password = fields.String(required=True, validate=[
        validate.Length(min=1, error='密码不能为空')
    ])


class UserRegisterSchema(Schema):
    """用户注册 Schema"""
    class Meta:
        unknown = 'exclude'

    username = fields.String(required=True, validate=[
        validate.Length(min=2, max=50, error='用户名长度应为2-50个字符')
    ])
    password = fields.String(required=True, validate=[
        validate.Length(min=6, max=128, error='密码长度应为6-128个字符'),
        validate_password_strength
    ])
    email = fields.Email(load_default=None, error_messages={'invalid': '邮箱格式不正确'})
    phone = fields.String(load_default=None, validate=[
        validate.Length(max=20)
    ])
    real_name = fields.String(load_default=None, validate=[
        validate.Length(max=50)
    ])
    student_id = fields.String(load_default=None, validate=[
        validate.Length(max=50)
    ])

    @validates('phone')
    def validate_phone(self, value, **kwargs):
        """校验手机号格式"""
        if value and not re.match(r'^1[3-9]\d{9}$', value):
            raise ValidationError('手机号格式不正确')


class UserUpdateSchema(Schema):
    """用户更新 Schema（管理员操作）"""
    email = fields.Email(load_default=None, error_messages={'invalid': '邮箱格式不正确'})
    phone = fields.String(load_default=None, validate=[
        validate.Length(max=20)
    ])
    real_name = fields.String(load_default=None, validate=[
        validate.Length(max=50)
    ])
    student_id = fields.String(load_default=None, validate=[
        validate.Length(max=50)
    ])
    role = fields.String(load_default=None, validate=[
        validate.OneOf(['admin', 'teacher', 'student'], error='角色必须是 admin/teacher/student')
    ])
    status = fields.Integer(load_default=None, validate=[
        validate.OneOf([0, 1], error='状态值必须为0或1')
    ])
    password = fields.String(load_default=None, validate=[
        validate.Length(min=6, max=128, error='密码长度应为6-128个字符')
    ])

    @validates('phone')
    def validate_phone(self, value, **kwargs):
        """校验手机号格式"""
        if value and not re.match(r'^1[3-9]\d{9}$', value):
            raise ValidationError('手机号格式不正确')


class UserChangePasswordSchema(Schema):
    """修改密码 Schema"""
    old_password = fields.String(required=True, validate=[
        validate.Length(min=1, error='旧密码不能为空')
    ])
    new_password = fields.String(required=True, validate=[
        validate.Length(min=6, max=128, error='新密码长度应为6-128个字符'),
        validate_password_strength
    ])


class UserProfileUpdateSchema(Schema):
    """用户自助更新个人信息 Schema"""
    email = fields.Email(load_default=None, error_messages={'invalid': '邮箱格式不正确'})
    phone = fields.String(load_default=None, validate=[
        validate.Length(max=20)
    ])
    real_name = fields.String(load_default=None, validate=[
        validate.Length(max=50)
    ])

    @validates('phone')
    def validate_phone(self, value, **kwargs):
        """校验手机号格式"""
        if value and not re.match(r'^1[3-9]\d{9}$', value):
            raise ValidationError('手机号格式不正确')


class UserProfileSchema(Schema):
    """用户信息输出 Schema"""
    id = fields.Integer()
    username = fields.String()
    email = fields.String()
    phone = fields.String()
    real_name = fields.String()
    student_id = fields.String()
    role = fields.String()
    status = fields.Integer()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')


class UserListSchema(Schema):
    """用户列表输出 Schema（不含敏感信息）"""
    id = fields.Integer()
    username = fields.String()
    email = fields.String()
    phone = fields.String()
    real_name = fields.String()
    student_id = fields.String()
    role = fields.String()
    status = fields.Integer()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
