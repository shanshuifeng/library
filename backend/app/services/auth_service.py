"""
认证服务层
"""
from ..models.user import User
from ..models.permission import Role
from ..extensions import db


def authenticate_user(username, password):
    """
    验证用户登录

    Args:
        username: 用户名
        password: 密码

    Returns:
        (User, None) 成功返回用户对象
        (None, str) 失败返回错误信息
    """
    user = User.query.filter_by(username=username).first()

    if not user:
        return None, '用户不存在'

    if not user.check_password(password):
        return None, '密码错误'

    if user.status != 1:
        return None, '账号已被禁用'

    return user, None


def register_user(username, password, email=None, phone=None,
                  real_name=None, student_id=None, role='student'):
    """
    用户注册

    Args:
        username: 用户名
        password: 密码
        email: 邮箱
        phone: 手机号
        real_name: 真实姓名
        student_id: 学号/工号
        role: 角色

    Returns:
        (User, None) 成功返回用户对象
        (None, str) 失败返回错误信息
    """
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return None, '用户名已存在'

    # 检查邮箱是否已存在
    if email and User.query.filter_by(email=email).first():
        return None, '邮箱已被使用'

    # 检查学号是否已存在
    if student_id and User.query.filter_by(student_id=student_id).first():
        return None, '学号已被使用'

    # 创建用户
    user = User(
        username=username,
        email=email,
        phone=phone,
        real_name=real_name,
        student_id=student_id,
        role=role,
        status=1
    )
    user.set_password(password)

    db.session.add(user)

    # 分配默认角色：权限系统通过 user_roles 关联表判断权限，
    # 仅设置 role 字符串字段不会让新用户获得任何菜单权限。
    role_obj = Role.query.filter_by(name=role).first()
    if role_obj:
        user.roles.append(role_obj)

    db.session.commit()

    return user, None


def change_password(user_id, old_password, new_password):
    """
    修改密码

    Args:
        user_id: 用户ID
        old_password: 旧密码
        new_password: 新密码

    Returns:
        (True, None) 成功
        (False, str) 失败返回错误信息
    """
    user = User.query.get(user_id)

    if not user:
        return False, '用户不存在'

    if not user.check_password(old_password):
        return False, '旧密码错误'

    user.set_password(new_password)
    db.session.commit()

    return True, None


def get_user_profile(user_id):
    """
    获取用户信息

    Args:
        user_id: 用户ID

    Returns:
        User 对象或 None
    """
    return User.query.get(user_id)


def update_profile(user_id, data):
    """
    用户自助更新个人信息

    Args:
        user_id: 用户ID
        data: 更新数据字典（仅允许 email, phone, real_name）

    Returns:
        (User, None) 成功返回用户对象
        (None, str) 失败返回错误信息
    """
    user = User.query.get(user_id)
    if not user:
        return None, '用户不存在'

    # 检查邮箱是否与其他用户冲突
    if 'email' in data and data['email'] and data['email'] != user.email:
        existing = User.query.filter_by(email=data['email']).first()
        if existing:
            return None, '邮箱已被使用'
        user.email = data['email']

    if 'phone' in data:
        user.phone = data['phone']

    if 'real_name' in data:
        user.real_name = data['real_name']

    db.session.commit()

    return user, None
