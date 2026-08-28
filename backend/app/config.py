"""
配置管理模块
"""
import os
import secrets
from datetime import timedelta


def get_required_env(var_name: str, fallback_generate: bool = False) -> str:
    """
    获取必需的环境变量。
    如果未设置且 fallback_generate=True，则自动生成随机值（仅开发环境）。
    生产环境必须设置，否则启动报错。
    """
    value = os.getenv(var_name)
    if value:
        return value
    if fallback_generate:
        return secrets.token_hex(32)
    raise EnvironmentError(f'必须设置环境变量 {var_name}，请在 .env 文件中配置')


class Config:
    """基础配置"""
    SECRET_KEY = get_required_env('SECRET_KEY', fallback_generate=True)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql+psycopg://remote_user:NewPassword%40123@192.168.116.141:5432/book_manager'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 20
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 1800
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True
    }

    JWT_SECRET_KEY = get_required_env('JWT_SECRET_KEY', fallback_generate=True)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # CORS 配置 — 生产环境必须指定具体域名
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # 图书馆配置
    MAX_BORROW_COUNT = {
        'student': 5,
        'teacher': 10,
        'admin': 20
    }
    BORROW_DAYS = 30  # 默认借阅天数
    MAX_RENEW_COUNT = 2  # 最大续借次数
    RENEW_DAYS = 30  # 每次续借天数
    FINE_PER_DAY = 0.1  # 每天罚款金额


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
