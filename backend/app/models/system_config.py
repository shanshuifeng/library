"""
系统配置模型
"""
from ..extensions import db


class SystemConfig(db.Model):
    """系统配置表"""
    __tablename__ = 'system_config'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    config_key = db.Column(db.String(50), unique=True, nullable=False, index=True)
    config_value = db.Column(db.String(500), nullable=True)
    description = db.Column(db.String(200), nullable=True)

    # 预定义的系统配置键
    KEYS = {
        'max_borrow_student': '学生最大借阅数量',
        'max_borrow_teacher': '教师最大借阅数量',
        'max_borrow_admin': '管理员最大借阅数量',
        'borrow_days': '默认借阅天数',
        'max_renew_count': '最大续借次数',
        'renew_days': '每次续借天数',
        'fine_per_day': '每天罚款金额',
        'stock_warning_threshold': '库存预警阈值',
        'site_name': '系统名称',
        'site_description': '系统描述',
    }

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.config_value,
            'description': self.description
        }

    def __repr__(self):
        return f'<SystemConfig {self.config_key}={self.config_value}>'
