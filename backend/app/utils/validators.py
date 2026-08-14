"""
自定义校验工具函数
提供 ISBN、手机号、用户名、密码等通用校验逻辑
"""
import re


def validate_isbn(isbn: str) -> bool:
    """
    校验 ISBN 格式（支持 ISBN-10 和 ISBN-13）

    Args:
        isbn: ISBN 字符串，可包含连字符

    Returns:
        True 如果格式正确，否则 False
    """
    if not isbn:
        return False

    # 移除连字符和空格
    clean_isbn = isbn.replace('-', '').replace(' ', '')

    # ISBN-10: 10位数字，最后一位可能是X
    if re.match(r'^\d{9}[\dX]$', clean_isbn):
        return _validate_isbn10_checksum(clean_isbn)

    # ISBN-13: 13位数字
    if re.match(r'^\d{13}$', clean_isbn):
        return _validate_isbn13_checksum(clean_isbn)

    return False


def _validate_isbn10_checksum(isbn: str) -> bool:
    """
    校验 ISBN-10 校验位

    Args:
        isbn: 纯数字（最后一位可能为X）的10位ISBN

    Returns:
        True 如果校验位正确
    """
    total = 0
    for i in range(9):
        total += int(isbn[i]) * (10 - i)

    check_digit = isbn[9]
    if check_digit == 'X':
        total += 10
    else:
        total += int(check_digit)

    return total % 11 == 0


def _validate_isbn13_checksum(isbn: str) -> bool:
    """
    校验 ISBN-13 校验位

    Args:
        isbn: 13位纯数字ISBN

    Returns:
        True 如果校验位正确
    """
    total = 0
    for i in range(12):
        weight = 1 if i % 2 == 0 else 3
        total += int(isbn[i]) * weight

    check_digit = (10 - (total % 10)) % 10
    return check_digit == int(isbn[12])


def validate_phone(phone: str) -> bool:
    """
    校验中国大陆手机号格式

    Args:
        phone: 手机号字符串

    Returns:
        True 如果格式正确，否则 False
    """
    if not phone:
        return False
    return bool(re.match(r'^1[3-9]\d{9}$', phone))


def validate_username(username: str) -> tuple:
    """
    校验用户名格式

    规则:
        - 长度 2-50 个字符
        - 只允许字母、数字、下划线
        - 必须以字母开头

    Args:
        username: 用户名

    Returns:
        (bool, str) 校验结果和错误信息
    """
    if not username:
        return False, '用户名不能为空'

    if len(username) < 2 or len(username) > 50:
        return False, '用户名长度应为2-50个字符'

    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        return False, '用户名只能包含字母、数字和下划线，且以字母开头'

    return True, ''


def validate_password_strength(password: str) -> tuple:
    """
    校验密码强度

    规则:
        - 长度 6-128 个字符
        - 不能为纯数字
        - 建议包含字母和数字

    Args:
        password: 密码

    Returns:
        (bool, str) 校验结果和错误信息
    """
    if not password:
        return False, '密码不能为空'

    if len(password) < 6:
        return False, '密码长度不能少于6位'

    if len(password) > 128:
        return False, '密码长度不能超过128位'

    if password.isdigit():
        return False, '密码不能为纯数字'

    return True, ''


def validate_email(email: str) -> bool:
    """
    校验邮箱格式

    Args:
        email: 邮箱字符串

    Returns:
        True 如果格式正确，否则 False
    """
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))


def validate_role(role: str) -> bool:
    """
    校验用户角色

    Args:
        role: 角色字符串

    Returns:
        True 如果角色合法
    """
    return role in ('admin', 'teacher', 'student')


def validate_stock(stock: int) -> tuple:
    """
    校验库存值

    Args:
        stock: 库存数量

    Returns:
        (bool, str) 校验结果和错误信息
    """
    if stock is None:
        return False, '库存值不能为空'

    if not isinstance(stock, int):
        return False, '库存值必须为整数'

    if stock < 0:
        return False, '库存值不能为负数'

    return True, ''


def validate_price(price) -> tuple:
    """
    校验价格

    Args:
        price: 价格值

    Returns:
        (bool, str) 校验结果和错误信息
    """
    if price is None:
        return True, ''  # 价格可选

    try:
        price_float = float(price)
    except (ValueError, TypeError):
        return False, '价格必须为数字'

    if price_float < 0:
        return False, '价格不能为负数'

    if price_float > 9999999.99:
        return False, '价格超出范围'

    return True, ''
