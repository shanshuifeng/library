"""
统一响应格式工具
兼容 flask-restx：返回 (dict, status_code) 而非 jsonify Response
"""
from marshmallow import ValidationError


def success_response(data=None, message='成功', code=200):
    """
    成功响应

    Args:
        data: 响应数据
        message: 响应消息
        code: HTTP 状态码

    Returns:
        (dict, int) 兼容 flask-restx
    """
    response = {
        'code': code,
        'message': message,
        'data': data
    }
    return response, code


def error_response(message='错误', code=400, data=None):
    """
    错误响应

    Args:
        message: 错误消息
        code: HTTP 状态码
        data: 附加数据

    Returns:
        (dict, int) 兼容 flask-restx
    """
    response = {
        'code': code,
        'message': message,
        'data': data
    }
    return response, code


def validation_error_response(error):
    """
    Marshmallow 校验错误响应

    Args:
        error: marshmallow.ValidationError 实例

    Returns:
        (dict, int) 兼容 flask-restx
    """
    # 格式化错误消息
    messages = error.messages
    errors = []
    for field, msgs in messages.items():
        if isinstance(msgs, list):
            for msg in msgs:
                errors.append({'field': field, 'message': msg})
        elif isinstance(msgs, dict):
            for sub_field, sub_msgs in msgs.items():
                if isinstance(sub_msgs, list):
                    for msg in sub_msgs:
                        errors.append({'field': f'{field}.{sub_field}', 'message': msg})

    # 用第一个错误作为主消息
    first_error = errors[0]['message'] if errors else '数据校验失败'

    response = {
        'code': 400,
        'message': first_error,
        'data': None,
        'errors': errors
    }
    return response, 400


def paginate_response(query, schema, page=1, per_page=20):
    """
    分页响应

    Args:
        query: SQLAlchemy 查询对象
        schema: 序列化器（支持 Marshmallow Schema 或自定义 Schema）
        page: 当前页码
        per_page: 每页数量

    Returns:
        包含分页数据的响应
    """
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 兼容 Marshmallow Schema 和自定义 Schema（有 dump 方法）
    if hasattr(schema, 'dump'):
        items = schema.dump(pagination.items)
    else:
        items = [item.to_dict() for item in pagination.items]

    return success_response(data={
        'items': items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })
