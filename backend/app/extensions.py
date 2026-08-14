"""
Flask 扩展初始化
"""
import re

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

# openGauss 的 version() 返回 "openGauss 6.0.5 ..."，而非 "PostgreSQL x.y.z"，
# SQLAlchemy 的 PostgreSQL 方言因此无法解析版本号。这里放宽正则以兼容 openGauss。
from sqlalchemy.dialects.postgresql.base import PGDialect


def _get_server_version_info(self, connection):
    v = connection.exec_driver_sql("select pg_catalog.version()").scalar()
    m = re.match(
        r".*(?:PostgreSQL|EnterpriseDB|openGauss) "
        r"(\d+)\.?(\d+)?(?:\.(\d+))?(?:\.\d+)?(?:devel|beta)?",
        v,
    )
    if not m:
        raise AssertionError("Could not determine version from string '%s'" % v)
    return tuple(int(x) for x in m.group(1, 2, 3) if x is not None)


PGDialect._get_server_version_info = _get_server_version_info

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
