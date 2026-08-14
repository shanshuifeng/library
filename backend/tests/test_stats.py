"""
统计与系统配置模块测试
"""
import pytest


class TestStatsOverview:
    """统计概览接口测试"""

    def test_get_overview(self, client, admin_user, book, auth_headers):
        """测试获取统计概览"""
        response = client.get('/api/v1/stats/overview',
                             headers=auth_headers)
        data = response.get_json()

        assert data['code'] == 200
        assert 'total_users' in data['data']
        assert 'total_books' in data['data']
        assert 'total_borrows' in data['data']
        assert 'current_borrowed' in data['data']

    def test_get_overview_not_admin(self, client, student_user, student_headers):
        """测试非管理员访问统计"""
        response = client.get('/api/v1/stats/overview',
                             headers=student_headers)
        data = response.get_json()

        assert data['code'] == 403


class TestBorrowTrend:
    """借阅趋势接口测试"""

    def test_get_borrow_trend(self, client, admin_user, auth_headers):
        """测试获取借阅趋势"""
        response = client.get('/api/v1/stats/borrow-trend',
                             headers=auth_headers)
        data = response.get_json()

        assert data['code'] == 200
        assert isinstance(data['data'], list)
        assert len(data['data']) == 30


class TestPopularBooks:
    """热门图书接口测试"""

    def test_get_popular_books(self, client, admin_user, auth_headers):
        """测试获取热门图书"""
        response = client.get('/api/v1/stats/popular-books',
                             headers=auth_headers)
        data = response.get_json()

        assert data['code'] == 200
        assert isinstance(data['data'], list)


class TestSystemConfig:
    """系统配置接口测试"""

    def test_get_configs(self, client, admin_user, auth_headers):
        """测试获取系统配置"""
        response = client.get('/api/v1/stats/config',
                             headers=auth_headers)
        data = response.get_json()

        assert data['code'] == 200

    def test_create_config(self, client, admin_user, auth_headers):
        """测试创建系统配置"""
        response = client.post('/api/v1/stats/config',
                              headers=auth_headers,
                              json={
                                  'config_key': 'test_key',
                                  'config_value': 'test_value',
                                  'description': '测试配置'
                              })
        data = response.get_json()

        assert response.status_code == 201
        assert data['data']['config_key'] == 'test_key'

    def test_update_config(self, client, admin_user, db, auth_headers):
        """测试更新系统配置"""
        from app.models import SystemConfig
        config = SystemConfig(config_key='update_test', config_value='old_value')
        db.session.add(config)
        db.session.commit()

        response = client.put(f'/api/v1/stats/config/{config.id}',
                             headers=auth_headers,
                             json={'config_value': 'new_value'})
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['config_value'] == 'new_value'

    def test_init_configs(self, client, admin_user, auth_headers):
        """测试初始化默认配置"""
        response = client.post('/api/v1/stats/config/init',
                              headers=auth_headers)
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['created_count'] >= 0
