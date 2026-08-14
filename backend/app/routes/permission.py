"""
权限管理路由
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..utils.response import success_response, error_response
from ..utils.auth import admin_required
from ..utils.audit import log_audit
from ..services import permission_service

# 创建命名空间
ns = Namespace('permissions', description='权限管理相关接口')

# ===== 定义模型 =====

permission_model = ns.model('Permission', {
    'id': fields.Integer(description='权限ID'),
    'code': fields.String(description='权限代码'),
    'name': fields.String(description='权限名称'),
    'group': fields.String(description='权限分组'),
    'description': fields.String(description='描述')
})

permission_group_model = ns.model('PermissionGroup', {
    'group': fields.String(description='分组名称'),
    'permissions': fields.List(fields.Nested(permission_model), description='权限列表')
})

role_model = ns.model('Role', {
    'id': fields.Integer(description='角色ID'),
    'name': fields.String(description='角色名称'),
    'description': fields.String(description='描述'),
    'created_at': fields.String(description='创建时间')
})

role_detail_model = ns.model('RoleDetail', {
    'id': fields.Integer(description='角色ID'),
    'name': fields.String(description='角色名称'),
    'description': fields.String(description='描述'),
    'permissions': fields.List(fields.Nested(permission_model), description='权限列表'),
    'created_at': fields.String(description='创建时间')
})

role_create_model = ns.model('RoleCreate', {
    'name': fields.String(required=True, description='角色名称', example='editor'),
    'description': fields.String(description='描述', example='编辑员'),
    'permission_ids': fields.List(fields.Integer, description='权限ID列表', example=[1, 2, 3])
})

role_update_model = ns.model('RoleUpdate', {
    'name': fields.String(description='角色名称'),
    'description': fields.String(description='描述'),
    'permission_ids': fields.List(fields.Integer, description='权限ID列表')
})

user_roles_model = ns.model('UserRoles', {
    'roles': fields.List(fields.Nested(role_model), description='角色列表')
})

set_user_roles_model = ns.model('SetUserRoles', {
    'role_ids': fields.List(fields.Integer, required=True, description='角色ID列表', example=[1, 2])
})

my_permissions_model = ns.model('MyPermissions', {
    'permissions': fields.List(fields.String, description='权限代码列表')
})


# ===== 路由 =====

@ns.route('/')
class PermissionList(Resource):
    """权限列表"""

    @ns.doc('获取所有权限（分组）', security='Bearer')
    
    @admin_required
    def get(self):
        """获取所有权限（按分组）"""
        groups = permission_service.get_all_permissions(group_by_group=True)
        return success_response(data=groups)


@ns.route('/roles')
class RoleList(Resource):
    """角色列表"""

    @ns.doc('获取所有角色', security='Bearer')
    
    @admin_required
    def get(self):
        """获取所有角色"""
        roles = permission_service.get_all_roles()
        return success_response(data=roles)

    @ns.doc('创建角色', security='Bearer')
    @ns.expect(role_create_model)
    
    @ns.response(400, '参数错误')
    @admin_required
    def post(self):
        """创建角色"""
        data = request.get_json()
        if not data or not data.get('name'):
            ns.abort(400, '请提供角色名称')

        role, error = permission_service.create_role(
            name=data['name'],
            description=data.get('description'),
            permission_ids=data.get('permission_ids')
        )

        if error:
            log_audit(
                action='create',
                resource_type='role',
                detail=f'创建角色失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='create',
            resource_type='role',
            resource_id=role.id,
            detail=f'创建角色: {role.name}',
            new_value=role.to_dict()
        )

        return success_response(data=role.to_dict(), message='角色创建成功', code=201)


@ns.route('/roles/<int:role_id>')
class RoleDetail(Resource):
    """角色详情"""

    @ns.doc('获取角色详情', security='Bearer')
    
    @ns.response(404, '角色不存在')
    @admin_required
    def get(self, role_id):
        """获取角色详情"""
        role = permission_service.get_role_detail(role_id)
        if not role:
            ns.abort(404, '角色不存在')
        return success_response(data=role)

    @ns.doc('更新角色', security='Bearer')
    @ns.expect(role_update_model)
    
    @ns.response(404, '角色不存在')
    @admin_required
    def put(self, role_id):
        """更新角色"""
        data = request.get_json()
        if not data:
            ns.abort(400, '请求数据不能为空')

        # 获取变更前的数据
        from ..models.permission import Role
        old_role = Role.query.get(role_id)
        old_value = old_role.to_dict() if old_role else None

        role, error = permission_service.update_role(role_id, data)

        if error:
            log_audit(
                action='update',
                resource_type='role',
                resource_id=role_id,
                detail=f'更新角色失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='update',
            resource_type='role',
            resource_id=role_id,
            detail=f'更新角色: {role.name}',
            old_value=old_value,
            new_value=role.to_dict_detail()
        )

        return success_response(data=role.to_dict_detail(), message='角色更新成功')

    @ns.doc('删除角色', security='Bearer')
    @ns.response(200, '删除成功')
    @ns.response(404, '角色不存在')
    @admin_required
    def delete(self, role_id):
        """删除角色"""
        # 获取变更前的数据
        from ..models.permission import Role
        old_role = Role.query.get(role_id)
        old_value = old_role.to_dict() if old_role else None
        role_name = old_role.name if old_role else f'#{role_id}'

        ok, error = permission_service.delete_role(role_id)

        if not ok:
            log_audit(
                action='delete',
                resource_type='role',
                resource_id=role_id,
                detail=f'删除角色失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='delete',
            resource_type='role',
            resource_id=role_id,
            detail=f'删除角色: {role_name}',
            old_value=old_value
        )

        return success_response(message='角色删除成功')


@ns.route('/users/<int:user_id>/roles')
class UserRoles(Resource):
    """用户角色"""

    @ns.doc('获取用户的角色', security='Bearer')
    
    @admin_required
    def get(self, user_id):
        """获取用户的角色"""
        roles = permission_service.get_user_roles(user_id)
        return success_response(data=roles)

    @ns.doc('设置用户的角色', security='Bearer')
    @ns.expect(set_user_roles_model)
    @ns.response(200, '设置成功')
    @admin_required
    def put(self, user_id):
        """设置用户的角色"""
        # 获取用户信息
        from ..models.user import User
        user = User.query.get(user_id)
        if not user:
            ns.abort(404, '用户不存在')

        # 获取变更前的角色
        old_roles = permission_service.get_user_roles(user_id)
        old_role_ids = [r['id'] for r in old_roles] if old_roles else []

        data = request.get_json()
        role_ids = data.get('role_ids', []) if data else []
        ok, error = permission_service.set_user_roles(user_id, role_ids)

        if not ok:
            log_audit(
                action='update',
                resource_type='user_role',
                resource_id=user_id,
                detail=f'设置用户角色失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 获取变更后的角色
        new_roles = permission_service.get_user_roles(user_id)
        new_role_ids = [r['id'] for r in new_roles] if new_roles else []

        # 记录成功审计日志
        log_audit(
            action='update',
            resource_type='user_role',
            resource_id=user_id,
            detail=f'设置用户 {user.username} 的角色',
            old_value={'role_ids': old_role_ids},
            new_value={'role_ids': new_role_ids}
        )

        return success_response(message='角色设置成功')


@ns.route('/mine')
class MyPermissions(Resource):
    """我的权限"""

    @ns.doc('获取当前用户的权限代码列表', security='Bearer')
    
    @jwt_required()
    def get(self):
        """获取当前用户的权限代码列表"""
        user_id = int(get_jwt_identity())
        codes = permission_service.get_user_permission_codes(user_id)
        return success_response(data={'permissions': list(codes)})
