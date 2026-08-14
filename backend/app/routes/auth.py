"""
认证路由
处理用户登录、注册、退出等认证相关接口
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity
)
from marshmallow import ValidationError

from ..services import auth_service
from ..schemas.user import (
    UserLoginSchema,
    UserRegisterSchema,
    UserChangePasswordSchema,
    UserProfileUpdateSchema,
    UserProfileSchema
)
from ..utils.response import success_response, error_response
from ..utils.rate_limit import rate_limit
from ..utils.audit import log_audit

# 创建命名空间
ns = Namespace('auth', description='认证相关接口')

# Schema 实例
login_schema = UserLoginSchema()
register_schema = UserRegisterSchema()
change_password_schema = UserChangePasswordSchema()
profile_update_schema = UserProfileUpdateSchema()
profile_output_schema = UserProfileSchema()

# ===== 定义请求/响应模型 =====

login_model = ns.model('Login', {
    'username': fields.String(required=True, description='用户名', example='admin'),
    'password': fields.String(required=True, description='密码', example='123456')
})

register_model = ns.model('Register', {
    'username': fields.String(required=True, description='用户名', example='student1'),
    'password': fields.String(required=True, description='密码', example='123456'),
    'email': fields.String(description='邮箱', example='student@example.com'),
    'phone': fields.String(description='手机号', example='13800138000'),
    'real_name': fields.String(description='真实姓名', example='张三'),
    'student_id': fields.String(description='学号/工号', example='2021001')
})

user_info_model = ns.model('UserInfo', {
    'id': fields.Integer(description='用户ID'),
    'username': fields.String(description='用户名'),
    'email': fields.String(description='邮箱'),
    'phone': fields.String(description='手机号'),
    'real_name': fields.String(description='真实姓名'),
    'student_id': fields.String(description='学号/工号'),
    'role': fields.String(description='角色'),
    'status': fields.Integer(description='状态'),
    'created_at': fields.String(description='创建时间')
})

token_model = ns.model('Token', {
    'access_token': fields.String(description='访问令牌'),
    'refresh_token': fields.String(description='刷新令牌'),
    'user': fields.Nested(user_info_model, description='用户信息')
})

profile_update_model = ns.model('ProfileUpdate', {
    'email': fields.String(description='邮箱'),
    'phone': fields.String(description='手机号'),
    'real_name': fields.String(description='真实姓名')
})

password_model = ns.model('ChangePassword', {
    'old_password': fields.String(required=True, description='旧密码'),
    'new_password': fields.String(required=True, description='新密码')
})


# ===== 路由 =====

@ns.route('/login')
class Login(Resource):
    """用户登录"""

    @ns.doc('用户登录')
    @ns.expect(login_model)
    @ns.response(200, '登录成功')
    @ns.response(401, '登录失败')
    @ns.response(429, '请求过于频繁')
    @rate_limit(limit=10, window=60)  # 每分钟最多10次登录尝试
    def post(self):
        """用户登录"""
        data = request.get_json()

        if not data:
            ns.abort(400, '请提供登录信息')

        # Schema 校验
        try:
            validated = login_schema.load(data)
        except ValidationError as e:
            ns.abort(400, str(e.messages))

        # 调用服务层进行登录验证
        try:
            user, error = auth_service.authenticate_user(
                validated['username'], validated['password']
            )
        except Exception as e:
            ns.abort(500, '服务器内部错误')

        if error:
            ns.abort(401, error)

        # 创建令牌（identity 必须为字符串）
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        # 记录登录日志
        from ..utils.logger import log_user_login
        log_user_login(user.id, user.username, success=True)

        # 记录审计日志
        log_audit(
            action='login',
            resource_type='user',
            resource_id=user.id,
            detail=f'用户 {user.username} 登录成功',
            new_value={'user_id': user.id, 'username': user.username}
        )

        return success_response(data={
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }, message='登录成功')


@ns.route('/register')
class Register(Resource):
    """用户注册"""

    @ns.doc('用户注册')
    @ns.expect(register_model)
    @ns.response(201, '注册成功')
    @ns.response(400, '注册失败')
    def post(self):
        """用户注册"""
        data = request.get_json()

        if not data:
            ns.abort(400, '请提供注册信息')

        # Schema 校验
        try:
            validated = register_schema.load(data)
        except ValidationError as e:
            ns.abort(400, str(e.messages))

        # 强制注册为学生角色，防止提权攻击
        validated['role'] = 'student'

        # 调用服务层进行注册
        user, error = auth_service.register_user(**validated)

        if error:
            ns.abort(400, error)

        # 记录注册日志
        from ..utils.logger import log_user_register
        log_user_register(user.id, user.username, user.role)

        # 记录审计日志
        log_audit(
            action='register',
            resource_type='user',
            resource_id=user.id,
            detail=f'新用户 {user.username} 注册成功',
            new_value={'user_id': user.id, 'username': user.username, 'role': user.role}
        )

        return success_response(data={
            'user': user.to_dict()
        }, message='注册成功', code=201)


@ns.route('/logout')
class Logout(Resource):
    """用户退出"""

    @ns.doc('用户退出', security='Bearer')
    @ns.response(200, '退出成功')
    @jwt_required()
    def post(self):
        """用户退出（JWT 是无状态的，退出需要客户端删除令牌）"""
        return success_response(message='退出成功')


@ns.route('/profile')
class Profile(Resource):
    """个人信息管理"""

    @ns.doc('获取当前用户信息', security='Bearer')
    @ns.response(200, '获取成功')
    @ns.response(404, '用户不存在')
    @jwt_required()
    def get(self):
        """获取当前用户信息"""
        user_id = int(get_jwt_identity())
        user = auth_service.get_user_profile(user_id)

        if not user:
            ns.abort(404, '用户不存在')

        return success_response(data={
            'user': user.to_dict()
        })

    @ns.doc('更新个人信息', security='Bearer')
    @ns.expect(profile_update_model)
    @ns.response(200, '更新成功')
    @ns.response(400, '参数错误')
    @jwt_required()
    def put(self):
        """更新个人信息"""
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data:
            ns.abort(400, '请提供更新信息')

        # Schema 校验
        try:
            validated = profile_update_schema.load(data)
        except ValidationError as e:
            ns.abort(400, str(e.messages))

        # 移除 None 值（未提供的字段不更新）
        update_data = {k: v for k, v in validated.items() if v is not None}

        if not update_data:
            ns.abort(400, '没有可更新的字段')

        # 调用服务层更新
        user, error = auth_service.update_profile(user_id, update_data)

        if error:
            ns.abort(400, error)

        return success_response(data={'user': user.to_dict()}, message='信息更新成功')


@ns.route('/password')
class ChangePassword(Resource):
    """修改密码"""

    @ns.doc('修改密码', security='Bearer')
    @ns.expect(password_model)
    @ns.response(200, '修改成功')
    @ns.response(400, '修改失败')
    @jwt_required()
    def put(self):
        """修改密码"""
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data:
            ns.abort(400, '请提供密码信息')

        # Schema 校验
        try:
            validated = change_password_schema.load(data)
        except ValidationError as e:
            ns.abort(400, str(e.messages))

        # 调用服务层修改密码
        success, error = auth_service.change_password(
            user_id, validated['old_password'], validated['new_password']
        )

        if not success:
            # 记录失败审计日志
            log_audit(
                action='change_password',
                resource_type='user',
                resource_id=user_id,
                detail='修改密码失败',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='change_password',
            resource_type='user',
            resource_id=user_id,
            detail='密码修改成功'
        )

        return success_response(message='密码修改成功')


@ns.route('/refresh')
class RefreshToken(Resource):
    """刷新访问令牌"""

    @ns.doc('刷新访问令牌', security='Bearer')
    @ns.response(200, '刷新成功')
    @jwt_required(refresh=True)
    def post(self):
        """刷新访问令牌（需要 Refresh Token）"""
        user_id = get_jwt_identity()
        access_token = create_access_token(identity=user_id)

        return success_response(data={
            'access_token': access_token
        }, message='令牌刷新成功')
