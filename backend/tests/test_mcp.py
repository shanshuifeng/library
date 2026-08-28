"""
MCP Server pytest 测试
使用 conftest.py 中定义的 fixtures
"""
import pytest
import json
import os

_TEST_PWD = os.environ.get('TEST_PASSWORD', 'admin123')
_WRONG_PWD = os.environ.get('TEST_WRONG_PASSWORD', 'wrong_password')


class TestPublicAPI:
    """公开接口测试（不需要 Token）"""

    def test_login_success(self, client, admin_user):
        """登录成功"""
        resp = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': _TEST_PWD
        })
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['code'] == 200
        assert 'access_token' in data['data']
        assert 'user' in data['data']

    def test_login_wrong_password(self, client, admin_user):
        """登录密码错误"""
        resp = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': _WRONG_PWD
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        """登录用户不存在"""
        resp = client.post('/api/v1/auth/login', json={
            'username': 'nonexistent',
            'password': '123456'
        })
        assert resp.status_code == 401


class TestProtectedAPI:
    """需要认证的接口测试"""

    def test_get_profile(self, client, admin_token):
        """获取个人信息"""
        resp = client.get('/api/v1/auth/profile',
                          headers={'Authorization': f'Bearer {admin_token}'})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['code'] == 200
        assert 'user' in data['data']

    def test_get_profile_no_token(self, client):
        """未认证访问个人信息"""
        resp = client.get('/api/v1/auth/profile')
        assert resp.status_code == 401

    def test_get_books(self, client, admin_token, book):
        """获取图书列表"""
        resp = client.get('/api/v1/books/?page=1&per_page=5',
                          headers={'Authorization': f'Bearer {admin_token}'})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert 'items' in data['data']

    def test_get_books_no_token(self, client):
        """未认证访问图书列表"""
        resp = client.get('/api/v1/books/')
        assert resp.status_code == 401

    def test_get_book_detail(self, client, admin_token, book):
        """获取图书详情"""
        resp = client.get(f'/api/v1/books/{book.id}',
                          headers={'Authorization': f'Bearer {admin_token}'})
        data = json.loads(resp.data)
        assert resp.status_code == 200

    def test_get_categories(self, client, admin_token, category):
        """获取分类树"""
        resp = client.get('/api/v1/books/categories',
                          headers={'Authorization': f'Bearer {admin_token}'})
        data = json.loads(resp.data)
        assert resp.status_code == 200

    def test_get_borrow_list(self, client, admin_token):
        """获取借阅记录"""
        resp = client.get('/api/v1/borrows/?page=1',
                          headers={'Authorization': f'Bearer {admin_token}'})
        data = json.loads(resp.data)
        assert resp.status_code == 200

    def test_get_overview(self, client, admin_token):
        """获取系统概览"""
        resp = client.get('/api/v1/stats/overview',
                          headers={'Authorization': f'Bearer {admin_token}'})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert 'bookCount' in data['data']

    def test_get_daily_trend(self, client, admin_token):
        """获取每日趋势"""
        resp = client.get('/api/v1/stats/daily-trend',
                          headers={'Authorization': f'Bearer {admin_token}'})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert 'dates' in data['data']


class TestSwagger:
    """Swagger 文档测试"""

    def test_swagger_ui(self, client):
        """访问 Swagger UI"""
        resp = client.get('/apidocs/')
        assert resp.status_code == 200

    def test_swagger_json(self, client):
        """获取 Swagger JSON"""
        resp = client.get('/api/v1/swagger.json')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert 'paths' in data
        assert 'definitions' in data
