"""
权限服务层
"""
from ..models import Permission, Role, User
from ..extensions import db


# ===== 权限 =====

def get_all_permissions(group_by_group=True):
    """获取所有权限"""
    perms = Permission.query.order_by(Permission.group, Permission.id).all()
    if not group_by_group:
        return [p.to_dict() for p in perms]
    groups = {}
    for p in perms:
        groups.setdefault(p.group, []).append(p.to_dict())
    return groups


# ===== 角色 =====

def get_all_roles():
    """获取所有角色"""
    return [r.to_dict() for r in Role.query.all()]


def get_role_detail(role_id):
    """获取角色详情（含权限列表）"""
    role = Role.query.get(role_id)
    return role.to_dict_detail() if role else None


def create_role(name, description=None, permission_ids=None):
    """创建角色"""
    if Role.query.filter_by(name=name).first():
        return None, '角色名已存在'
    role = Role(name=name, description=description)
    if permission_ids:
        perms = Permission.query.filter(Permission.id.in_(permission_ids)).all()
        role.permissions = perms
    db.session.add(role)
    db.session.commit()
    return role, None


def update_role(role_id, data):
    """更新角色"""
    role = Role.query.get(role_id)
    if not role:
        return None, '角色不存在'
    if 'name' in data and data['name'] != role.name:
        if Role.query.filter_by(name=data['name']).first():
            return None, '角色名已存在'
        role.name = data['name']
    if 'description' in data:
        role.description = data['description']
    if 'permission_ids' in data:
        perms = Permission.query.filter(Permission.id.in_(data['permission_ids'])).all()
        role.permissions = perms
    db.session.commit()
    return role, None


def delete_role(role_id):
    """删除角色"""
    role = Role.query.get(role_id)
    if not role:
        return False, '角色不存在'
    if role.is_system:
        return False, '系统角色不可删除'
    db.session.delete(role)
    db.session.commit()
    return True, None


# ===== 用户-角色 =====

def get_user_roles(user_id):
    """获取用户的角色列表"""
    user = User.query.get(user_id)
    if not user:
        return []
    return [r.to_dict() for r in user.roles.all()]


def set_user_roles(user_id, role_ids):
    """设置用户的角色"""
    user = User.query.get(user_id)
    if not user:
        return False, '用户不存在'
    roles = Role.query.filter(Role.id.in_(role_ids)).all()
    user.roles = roles
    db.session.commit()
    return True, None


# ===== 权限检查 =====

def user_has_permission(user_id, permission_code):
    """检查用户是否拥有指定权限"""
    user = User.query.get(user_id)
    if not user:
        return False
    # 拥有 admin 角色的用户拥有所有权限
    admin_role = Role.query.filter_by(name='admin').first()
    if admin_role and admin_role in user.roles.all():
        return True
    # 检查用户所有角色的权限
    for role in user.roles.all():
        for perm in role.permissions.all():
            if perm.code == permission_code:
                return True
    return False


def get_user_permission_codes(user_id):
    """获取用户所有权限代码"""
    user = User.query.get(user_id)
    if not user:
        return set()
    codes = set()
    admin_role = Role.query.filter_by(name='admin').first()
    if admin_role and admin_role in user.roles.all():
        # admin 返回所有权限
        return {p.code for p in Permission.query.all()}
    for role in user.roles.all():
        for perm in role.permissions.all():
            codes.add(perm.code)
    return codes
