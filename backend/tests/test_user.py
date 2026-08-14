"""
用户管理模块测试
"""
import pytest


class TestUserList:
    """用户列表接口测试"""

    def test_get_users_admin(self, client, admin_user, auth_headers):
        """测试管理员获取用户列表"""
        response = client.get('/api/v1/users/',
                             headers=auth_headers)
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['total'] >= 1

    def test_get_users_search(self, client, admin_user, auth_headers):
        """测试搜索用户"""
        response = client.get('/api/v1/users/?keyword=admin',
                             headers=auth_headers)
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['total'] >= 1

    def test_get_users_not_admin(self, client, student_user, student_headers):
        """测试非管理员获取用户列表"""
        response = client.get('/api/v1/users/',
                             headers=student_headers)
        data = response.get_json()

        assert data['code'] == 403


class TestUserCRUD:
    """用户增删改接口测试"""

    def test_create_user(self, client, auth_headers):
        """测试创建用户"""
        response = client.post('/api/v1/users/',
                              headers=auth_headers,
                              json={
                                  'username': 'newstudent',
                                  'password': '123456',
                                  'real_name': '新学生',
                                  'role': 'student'
                              })
        data = response.get_json()

        assert response.status_code == 201
        assert data['data']['username'] == 'newstudent'

    def test_create_user_duplicate(self, client, admin_user, auth_headers):
        """测试创建重复用户名"""
        response = client.post('/api/v1/users/',
                              headers=auth_headers,
                              json={
                                  'username': 'admin',
                                  'password': '123456'
                              })
        data = response.get_json()

        assert data['code'] == 400

    def test_update_user(self, client, admin_user, auth_headers, student_user):
        """测试更新用户"""
        response = client.put(f'/api/v1/users/{student_user.id}',
                             headers=auth_headers,
                             json={'real_name': '张三三', 'phone': '13800138000'})
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['real_name'] == '张三三'

    def test_update_user_role(self, client, admin_user, auth_headers, student_user):
        """测试更新用户角色"""
        response = client.put(f'/api/v1/users/{student_user.id}',
                             headers=auth_headers,
                             json={'role': 'teacher'})
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['role'] == 'teacher'

    def test_delete_user(self, client, admin_user, auth_headers, db):
        """测试删除用户"""
        from app.models import User
        user = User(username='todelete', role='student', status=1)
        user.set_password('123456')
        db.session.add(user)
        db.session.commit()

        response = client.delete(f'/api/v1/users/{user.id}',
                                headers=auth_headers)
        data = response.get_json()

        assert data['code'] == 200

    def test_delete_user_with_borrows(self, client, admin_user, auth_headers,
                                       student_user, book, student_headers):
        """测试删除有借阅记录的用户"""
        # 先借书
        client.post('/api/v1/borrows/',
                   headers=student_headers,
                   json={'book_id': book.id})

        # 尝试删除
        response = client.delete(f'/api/v1/users/{student_user.id}',
                                headers=auth_headers)
        data = response.get_json()

        assert data['code'] == 400
