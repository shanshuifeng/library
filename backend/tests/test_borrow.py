"""
借阅模块测试
"""
import pytest


class TestBorrowBook:
    """借书接口测试"""

    def test_borrow_success(self, client, student_user, book, student_headers):
        """测试正常借书"""
        response = client.post('/api/v1/borrows/',
                              headers=student_headers,
                              json={'book_id': book.id})
        data = response.get_json()

        assert response.status_code == 201
        assert data['code'] == 201
        assert data['data']['status'] == 'borrowed'
        assert data['data']['book_id'] == book.id

    def test_borrow_no_stock(self, client, student_user, db, student_headers):
        """测试库存不足借书"""
        from app.models import Book, Category
        cat = Category(name='test_cat', parent_id=0, level=1)
        db.session.add(cat)
        db.session.flush()

        book = Book(title='无库存书', stock=0, total_stock=0, category_id=cat.id)
        db.session.add(book)
        db.session.commit()

        response = client.post('/api/v1/borrows/',
                              headers=student_headers,
                              json={'book_id': book.id})
        data = response.get_json()

        assert data['code'] == 400

    def test_borrow_duplicate(self, client, student_user, book, student_headers):
        """测试重复借书"""
        # 第一次借书
        client.post('/api/v1/borrows/',
                   headers=student_headers,
                   json={'book_id': book.id})

        # 第二次借同一本书
        response = client.post('/api/v1/borrows/',
                              headers=student_headers,
                              json={'book_id': book.id})
        data = response.get_json()

        assert data['code'] == 400

    def test_borrow_no_token(self, client, book):
        """测试未登录借书"""
        response = client.post('/api/v1/borrows/',
                              json={'book_id': book.id})
        assert response.status_code == 401


class TestReturnBook:
    """还书接口测试"""

    def test_return_success(self, client, student_user, book, student_headers):
        """测试正常还书"""
        # 先借书
        client.post('/api/v1/borrows/',
                   headers=student_headers,
                   json={'book_id': book.id})

        # 获取借阅记录
        list_resp = client.get('/api/v1/borrows/',
                              headers=student_headers)
        record_id = list_resp.get_json()['data']['items'][0]['id']

        # 还书
        response = client.put(f'/api/v1/borrows/{record_id}/return',
                             headers=student_headers)
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['status'] == 'returned'

    def test_return_already_returned(self, client, student_user, book, student_headers):
        """测试重复还书"""
        # 先借书
        client.post('/api/v1/borrows/',
                   headers=student_headers,
                   json={'book_id': book.id})

        list_resp = client.get('/api/v1/borrows/',
                              headers=student_headers)
        record_id = list_resp.get_json()['data']['items'][0]['id']

        # 第一次还书
        client.put(f'/api/v1/borrows/{record_id}/return',
                  headers=student_headers)

        # 第二次还书
        response = client.put(f'/api/v1/borrows/{record_id}/return',
                             headers=student_headers)
        data = response.get_json()

        assert data['code'] == 400


class TestRenewBook:
    """续借接口测试"""

    def test_renew_success(self, client, student_user, book, student_headers):
        """测试正常续借"""
        # 先借书
        client.post('/api/v1/borrows/',
                   headers=student_headers,
                   json={'book_id': book.id})

        list_resp = client.get('/api/v1/borrows/',
                              headers=student_headers)
        record_id = list_resp.get_json()['data']['items'][0]['id']

        # 续借
        response = client.put(f'/api/v1/borrows/{record_id}/renew',
                             headers=student_headers)
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['renew_count'] == 1


class TestBorrowList:
    """借阅记录列表接口测试"""

    def test_get_borrow_list(self, client, student_user, book, student_headers):
        """测试获取借阅记录"""
        # 先借书
        client.post('/api/v1/borrows/',
                   headers=student_headers,
                   json={'book_id': book.id})

        response = client.get('/api/v1/borrows/',
                             headers=student_headers)
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['total'] == 1

    def test_get_user_borrows(self, client, student_user, book, student_headers):
        """测试获取指定用户的借阅记录"""
        # 先借书
        client.post('/api/v1/borrows/',
                   headers=student_headers,
                   json={'book_id': book.id})

        response = client.get(f'/api/v1/borrows/user/{student_user.id}',
                             headers=student_headers)
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['total'] == 1

    def test_get_other_user_borrows_forbidden(self, client, student_user, db, student_headers):
        """测试普通用户查看他人借阅记录被拒"""
        # 创建另一个用户
        from app.models import User
        other_user = User(username='other', role='student', status=1)
        other_user.set_password('123456')
        db.session.add(other_user)
        db.session.commit()

        response = client.get(f'/api/v1/borrows/user/{other_user.id}',
                             headers=student_headers)
        data = response.get_json()

        assert data['code'] == 403
