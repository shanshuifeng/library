"""
用户管理路由（管理员）
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required

from ..utils.response import success_response, error_response, paginate_response
from ..utils.auth import admin_required
from ..utils.audit import log_audit
from ..models.user import User
from ..extensions import db

# 创建命名空间
ns = Namespace('users', description='用户管理相关接口（管理员）')

# ===== 定义模型 =====

user_model = ns.model('User', {
    'id': fields.Integer(description='用户ID'),
    'username': fields.String(description='用户名'),
    'email': fields.String(description='邮箱'),
    'phone': fields.String(description='手机号'),
    'real_name': fields.String(description='真实姓名'),
    'student_id': fields.String(description='学号/工号'),
    'role': fields.String(description='角色（admin/teacher/student）'),
    'status': fields.Integer(description='状态（1启用/0禁用）'),
    'created_at': fields.String(description='创建时间')
})

user_create_model = ns.model('UserCreate', {
    'username': fields.String(required=True, description='用户名', example='student1'),
    'password': fields.String(required=True, description='密码', example='123456'),
    'email': fields.String(description='邮箱', example='student@example.com'),
    'phone': fields.String(description='手机号', example='13800138000'),
    'real_name': fields.String(description='真实姓名', example='张三'),
    'student_id': fields.String(description='学号/工号', example='2021001'),
    'role': fields.String(description='角色（默认student）', enum=['admin', 'teacher', 'student'], example='student')
})

user_update_model = ns.model('UserUpdate', {
    'email': fields.String(description='邮箱'),
    'phone': fields.String(description='手机号'),
    'real_name': fields.String(description='真实姓名'),
    'student_id': fields.String(description='学号/工号'),
    'role': fields.String(description='角色', enum=['admin', 'teacher', 'student']),
    'status': fields.Integer(description='状态（1启用/0禁用）'),
    'password': fields.String(description='新密码（可选）')
})


# ===== 路由 =====

@ns.route('/')
class UserList(Resource):
    """用户列表"""

    @ns.doc('获取用户列表', security='Bearer')
    @ns.expect(ns.parser()
        .add_argument('page', type=int, help='页码（默认1）', location='args')
        .add_argument('per_page', type=int, help='每页数量（默认20）', location='args')
        .add_argument('keyword', type=str, help='搜索关键词（用户名、姓名、学号）', location='args')
        .add_argument('role', type=str, help='角色筛选（admin/teacher/student）', location='args')
    )
    @ns.response(200, '获取成功')
    @admin_required
    def get(self):
        """获取用户列表"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        keyword = request.args.get('keyword', '').strip()
        role = request.args.get('role', '').strip()

        query = User.query

        # 关键词搜索
        if keyword:
            search_term = f'%{keyword}%'
            query = query.filter(
                db.or_(
                    User.username.ilike(search_term),
                    User.real_name.ilike(search_term),
                    User.student_id.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )

        # 角色筛选
        if role:
            query = query.filter_by(role=role)

        # 按创建时间降序排列
        query = query.order_by(User.created_at.desc())

        return paginate_response(
            query=query,
            schema=UserSchema(),
            page=page,
            per_page=per_page
        )

    @ns.doc('创建用户', security='Bearer')
    @ns.expect(user_create_model)
    
    @ns.response(400, '参数错误')
    @admin_required
    def post(self):
        """创建用户"""
        data = request.get_json()

        if not data:
            ns.abort(400, '请求数据不能为空')

        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            ns.abort(400, '用户名和密码不能为空')

        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            log_audit(
                action='create',
                resource_type='user',
                detail=f'创建用户失败: 用户名 {username} 已存在',
                status='failed',
                error_message='用户名已存在'
            )
            ns.abort(400, '用户名已存在')

        # 检查邮箱是否已存在
        email = data.get('email')
        if email and User.query.filter_by(email=email).first():
            log_audit(
                action='create',
                resource_type='user',
                detail=f'创建用户失败: 邮箱 {email} 已被使用',
                status='failed',
                error_message='邮箱已被使用'
            )
            ns.abort(400, '邮箱已被使用')

        # 检查学号是否已存在
        student_id = data.get('student_id')
        if student_id and User.query.filter_by(student_id=student_id).first():
            log_audit(
                action='create',
                resource_type='user',
                detail=f'创建用户失败: 学号 {student_id} 已被使用',
                status='failed',
                error_message='学号已被使用'
            )
            ns.abort(400, '学号已被使用')

        # 创建用户
        user = User(
            username=username,
            email=email,
            phone=data.get('phone'),
            real_name=data.get('real_name'),
            student_id=student_id,
            role=data.get('role', 'student'),
            status=1
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # 记录成功审计日志
        user_data = user.to_dict()
        user_data.pop('password', None)  # 移除密码字段
        log_audit(
            action='create',
            resource_type='user',
            resource_id=user.id,
            detail=f'创建用户: {username}, 角色: {user.role}',
            new_value=user_data
        )

        return success_response(data=user.to_dict(), message='用户创建成功', code=201)


@ns.route('/<int:user_id>')
class UserDetail(Resource):
    """用户详情"""

    @ns.doc('更新用户', security='Bearer')
    @ns.expect(user_update_model)
    
    @ns.response(404, '用户不存在')
    @admin_required
    def put(self, user_id):
        """更新用户"""
        user = User.query.get(user_id)
        if not user:
            ns.abort(404, '用户不存在')

        # 记录变更前的数据
        old_value = user.to_dict()

        data = request.get_json()
        if not data:
            ns.abort(400, '请求数据不能为空')

        # 检查邮箱是否与其他用户冲突
        if 'email' in data and data['email'] and data['email'] != user.email:
            existing = User.query.filter_by(email=data['email']).first()
            if existing:
                log_audit(
                    action='update',
                    resource_type='user',
                    resource_id=user_id,
                    detail=f'更新用户失败: 邮箱 {data["email"]} 已被使用',
                    status='failed',
                    error_message='邮箱已被使用'
                )
                ns.abort(400, '邮箱已被使用')

        # 检查学号是否与其他用户冲突
        if 'student_id' in data and data['student_id'] and data['student_id'] != user.student_id:
            existing = User.query.filter_by(student_id=data['student_id']).first()
            if existing:
                log_audit(
                    action='update',
                    resource_type='user',
                    resource_id=user_id,
                    detail=f'更新用户失败: 学号 {data["student_id"]} 已被使用',
                    status='failed',
                    error_message='学号已被使用'
                )
                ns.abort(400, '学号已被使用')

        # 更新字段
        if 'email' in data:
            user.email = data['email']
        if 'phone' in data:
            user.phone = data['phone']
        if 'real_name' in data:
            user.real_name = data['real_name']
        if 'student_id' in data:
            user.student_id = data['student_id']
        if 'role' in data:
            user.role = data['role']
        if 'status' in data:
            user.status = data['status']

        # 更新密码（如果有）
        if 'password' in data and data['password']:
            user.set_password(data['password'])

        db.session.commit()

        # 记录成功审计日志
        new_value = user.to_dict()
        log_audit(
            action='update',
            resource_type='user',
            resource_id=user_id,
            detail=f'更新用户: {user.username}',
            old_value=old_value,
            new_value=new_value
        )

        return success_response(data=user.to_dict(), message='用户更新成功')

    @ns.doc('删除用户', security='Bearer')
    @ns.response(200, '删除成功')
    @ns.response(404, '用户不存在')
    @admin_required
    def delete(self, user_id):
        """删除用户"""
        user = User.query.get(user_id)
        if not user:
            ns.abort(404, '用户不存在')

        # 记录删除前的数据
        old_value = user.to_dict()

        # 检查是否有未归还的借阅记录
        from ..models.borrow import BorrowRecord
        active_borrows = BorrowRecord.query.filter_by(
            user_id=user_id, status='borrowed'
        ).count()
        if active_borrows > 0:
            log_audit(
                action='delete',
                resource_type='user',
                resource_id=user_id,
                detail=f'删除用户失败: 用户 {user.username} 有 {active_borrows} 条未归还借阅记录',
                status='failed',
                error_message='该用户有未归还的图书，无法删除'
            )
            ns.abort(400, '该用户有未归还的图书，无法删除')

        db.session.delete(user)
        db.session.commit()

        # 记录成功审计日志
        log_audit(
            action='delete',
            resource_type='user',
            resource_id=user_id,
            detail=f'删除用户: {old_value.get("username", "")} ({old_value.get("real_name", "")})',
            old_value=old_value
        )

        return success_response(message='用户删除成功')


class UserSchema:
    """用户序列化器（用于分页列表）"""

    def dump(self, users):
        """序列化用户列表"""
        return [user.to_dict() for user in users]
