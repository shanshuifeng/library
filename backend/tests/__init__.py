"""
认证模块测试
"""
import pytest


class TestAuthLogin:
    """登录接口测试"""

    def test_login_success(self, client, student_user):
        """测试正常登录"""
        response = client.post('/api/v1/auth/login', json={
            'username': 'student1',
            'password': '123456'
        })
        data = response.get_json()

        assert response.status_code == 200
        assert data['code'] == 200
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']
        assert data['data']['user']['username'] == 'student1'

    def test_login_wrong_password(self, client, student_user):
        """测试密码错误"""
        response = client.post('/api/v1/auth/login', json={
            'username': 'student1',
            'password': 'wrongpassword'
        })
        data = response.get_json()

        assert data['code'] == 401

    def test_login_user_not_found(self, client, db):
        """测试用户不存在"""
        response = client.post('/api/v1/auth/login', json={
            'username': 'nouser',
            'password': '123456'
        })
        data = response.get_json()

        assert data['code'] == 401

    def test_login_missing_fields(self, client, db):
        """测试缺少字段"""
        response = client.post('/api/v1/auth/login', json={
            'username': ''
        })
        data = response.get_json()

        assert data['code'] == 400

    def test_login_no_data(self, client, db):
        """测试空请求体"""
        response = client.post('/api/v1/auth/login',
                               content_type='application/json')
        data = response.get_json()

        assert data['code'] == 400


class TestAuthRegister:
    """注册接口测试"""

    def test_register_success(self, client, db):
        """测试正常注册"""
        response = client.post('/api/v1/auth/register', json={
            'username': 'newuser',
            'password': '123456',
            'email': 'newuser@test.com',
            'real_name': '新用户'
        })
        data = response.get_json()

        assert response.status_code == 201
        assert data['code'] == 201
        assert data['data']['user']['username'] == 'newuser'
        assert data['data']['user']['role'] == 'student'

    def test_register_duplicate_username(self, client, student_user):
        """测试重复用户名"""
        response = client.post('/api/v1/auth/register', json={
            'username': 'student1',
            'password': '123456'
        })
        data = response.get_json()

        assert data['code'] == 400

    def test_register_short_password(self, client, db):
        """测试密码过短"""
        response = client.post('/api/v1/auth/register', json={
            'username': 'newuser2',
            'password': '123'
        })
        data = response.get_json()

        assert data['code'] == 400


class TestAuthProfile:
    """用户信息接口测试"""

    def test_get_profile(self, client, student_user, student_headers):
        """测试获取用户信息"""
        response = client.get('/api/v1/auth/profile',
                             headers=student_headers)
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['user']['username'] == 'student1'

    def test_update_profile(self, client, student_user, student_headers):
        """测试更新用户信息"""
        response = client.put('/api/v1/auth/profile',
                             headers=student_headers,
                             json={'real_name': '张三三', 'phone': '13800138000'})
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['user']['real_name'] == '张三三'
        assert data['data']['user']['phone'] == '13800138000'

    def test_get_profile_no_token(self, client, student_user):
        """测试未携带 Token 访问"""
        response = client.get('/api/v1/auth/profile')
        assert response.status_code == 401


class TestAuthChangePassword:
    """修改密码接口测试"""

    def test_change_password_success(self, client, student_user, student_headers):
        """测试正常修改密码"""
        response = client.put('/api/v1/auth/password',
                             headers=student_headers,
                             json={'old_password': '123456',
                                   'new_password': '654321'})
        data = response.get_json()

        assert data['code'] == 200

        # 验证新密码可以登录
        login_resp = client.post('/api/v1/auth/login', json={
            'username': 'student1',
            'password': '654321'
        })
        assert login_resp.get_json()['code'] == 200

    def test_change_password_wrong_old(self, client, student_user, student_headers):
        """测试旧密码错误"""
        response = client.put('/api/v1/auth/password',
                             headers=student_headers,
                             json={'old_password': 'wrong',
                                   'new_password': '654321'})
        data = response.get_json()

        assert data['code'] == 400
