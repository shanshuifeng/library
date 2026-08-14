"""
简单的内存请求频率限制器
"""
import time
from functools import wraps
from flask import request
from ..utils.response import error_response


class RateLimiter:
    """基于内存的滑动窗口限流器"""

    def __init__(self):
        self._requests = {}  # {key: [(timestamp, count), ...]}

    def _cleanup(self, key, window):
        """清理过期记录"""
        now = time.time()
        if key in self._requests:
            self._requests[key] = [
                (ts, cnt) for ts, cnt in self._requests[key]
                if now - ts < window
            ]
            if not self._requests[key]:
                del self._requests[key]

    def is_limited(self, key, limit, window):
        """
        检查是否超出限流

        Args:
            key: 限流键（如 IP 或用户ID）
            limit: 窗口内允许的最大请求数
            window: 时间窗口（秒）

        Returns:
            (is_limited, remaining, retry_after)
        """
        self._cleanup(key, window)
        now = time.time()

        if key not in self._requests:
            self._requests[key] = []

        request_count = sum(cnt for _, cnt in self._requests[key])

        if request_count >= limit:
            oldest = self._requests[key][0][0] if self._requests[key] else now
            retry_after = int(window - (now - oldest)) + 1
            return True, 0, retry_after

        # 记录本次请求
        self._requests[key].append((now, 1))
        return False, limit - request_count - 1, 0


# 全局限流器实例
limiter = RateLimiter()


def rate_limit(limit=60, window=60, key_func=None):
    """
    请求频率限制装饰器

    Args:
        limit: 窗口内允许的最大请求数
        window: 时间窗口（秒）
        key_func: 自定义限流键函数，默认使用 IP 地址
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if key_func:
                key = key_func()
            else:
                key = request.remote_addr or 'unknown'

            is_limited, remaining, retry_after = limiter.is_limited(key, limit, window)

            if is_limited:
                return error_response('请求过于频繁，请稍后再试', 429)

            # 在响应头中添加限流信息
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(limit)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
            return response

        return decorated_function
    return decorator
