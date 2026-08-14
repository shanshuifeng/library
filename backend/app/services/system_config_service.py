"""
系统配置服务层
"""
from ..models.system_config import SystemConfig
from ..extensions import db


def get_all_configs():
    """
    获取所有系统配置

    Returns:
        配置列表
    """
    configs = SystemConfig.query.order_by(SystemConfig.id).all()
    return [config.to_dict() for config in configs]


def get_config_by_key(config_key):
    """
    根据键获取配置值

    Args:
        config_key: 配置键

    Returns:
        配置值字符串，不存在返回 None
    """
    config = SystemConfig.query.filter_by(config_key=config_key).first()
    return config.config_value if config else None


def get_config_dict():
    """
    获取所有配置的键值对字典

    Returns:
        {config_key: config_value} 字典
    """
    configs = SystemConfig.query.all()
    return {config.config_key: config.config_value for config in configs}


def create_config(data):
    """
    创建系统配置

    Args:
        data: 配置数据字典
            config_key: 配置键（必填）
            config_value: 配置值
            description: 配置描述

    Returns:
        (SystemConfig, None) 成功返回配置对象
        (None, str) 失败返回错误信息
    """
    config_key = data.get('config_key', '').strip()
    if not config_key:
        return None, '配置键不能为空'

    # 检查键是否已存在
    existing = SystemConfig.query.filter_by(config_key=config_key).first()
    if existing:
        return None, '配置键已存在'

    config = SystemConfig(
        config_key=config_key,
        config_value=data.get('config_value', ''),
        description=data.get('description')
    )

    db.session.add(config)
    db.session.commit()

    return config, None


def update_config(config_id, data):
    """
    更新系统配置

    Args:
        config_id: 配置ID
        data: 更新数据字典

    Returns:
        (SystemConfig, None) 成功返回配置对象
        (None, str) 失败返回错误信息
    """
    config = SystemConfig.query.get(config_id)
    if not config:
        return None, '配置项不存在'

    # 如果修改了键，检查是否冲突
    if 'config_key' in data and data['config_key'] != config.config_key:
        new_key = data['config_key'].strip()
        if not new_key:
            return None, '配置键不能为空'
        existing = SystemConfig.query.filter_by(config_key=new_key).first()
        if existing:
            return None, '配置键已存在'
        config.config_key = new_key

    if 'config_value' in data:
        config.config_value = str(data['config_value'])

    if 'description' in data:
        config.description = data['description']

    db.session.commit()

    return config, None


def delete_config(config_id):
    """
    删除系统配置

    Args:
        config_id: 配置ID

    Returns:
        (True, None) 成功
        (False, str) 失败返回错误信息
    """
    config = SystemConfig.query.get(config_id)
    if not config:
        return False, '配置项不存在'

    db.session.delete(config)
    db.session.commit()

    return True, None


def init_default_configs():
    """
    初始化默认系统配置（用于系统首次部署）

    Returns:
        创建的配置数量
    """
    defaults = {
        'max_borrow_student': '5',
        'max_borrow_teacher': '10',
        'max_borrow_admin': '20',
        'borrow_days': '30',
        'max_renew_count': '2',
        'renew_days': '30',
        'fine_per_day': '0.1',
        'stock_warning_threshold': '5',
        'site_name': '大学图书管理系统',
        'site_description': '基于 Flask + Vue 3 的图书管理系统',
    }

    created = 0
    for key, value in defaults.items():
        if not SystemConfig.query.filter_by(config_key=key).first():
            config = SystemConfig(
                config_key=key,
                config_value=value,
                description=SystemConfig.KEYS.get(key, '')
            )
            db.session.add(config)
            created += 1

    if created > 0:
        db.session.commit()

    return created
