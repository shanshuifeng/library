"""
图书模块测试
"""
import pytest


class TestBookList:
    """图书列表接口测试"""

    def test_get_books_empty(self, client, db):
        """测试空图书列表"""
        response = client.get('/api/v1/books/')
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['items'] == []
        assert data['data']['total'] == 0

    def test_get_books_with_data(self, client, book):
        """测试有数据的图书列表"""
        response = client.get('/api/v1/books/')
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['total'] == 1
        assert data['data']['items'][0]['title'] == '测试图书'

    def test_get_books_search(self, client, book):
        """测试搜索图书"""
        response = client.get('/api/v1/books/?keyword=测试')
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['total'] == 1

    def test_get_books_search_no_result(self, client, book):
        """测试搜索无结果"""
        response = client.get('/api/v1/books/?keyword=不存在的书')
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['total'] == 0

    def test_get_books_pagination(self, client, book):
        """测试分页"""
        response = client.get('/api/v1/books/?page=1&per_page=10')
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['page'] == 1
        assert data['data']['per_page'] == 10


class TestBookDetail:
    """图书详情接口测试"""

    def test_get_book_detail(self, client, book):
        """测试获取图书详情"""
        response = client.get(f'/api/v1/books/{book.id}')
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['title'] == '测试图书'
        assert data['data']['author'] == '测试作者'

    def test_get_book_not_found(self, client, db):
        """测试获取不存在的图书"""
        response = client.get('/api/v1/books/999')
        data = response.get_json()

        assert data['code'] == 404


class TestBookCRUD:
    """图书增删改接口测试"""

    def test_create_book(self, client, category, auth_headers):
        """测试创建图书"""
        response = client.post('/api/v1/books/',
                              headers=auth_headers,
                              json={
                                  'title': '新书',
                                  'author': '新作者',
                                  'isbn': '9787020008797',
                                  'publisher': '新出版社',
                                  'category_id': category.id,
                                  'stock': 5,
                                  'total_stock': 5,
                                  'price': 35.00
                              })
        data = response.get_json()

        assert response.status_code == 201
        assert data['code'] == 201
        assert data['data']['title'] == '新书'

    def test_create_book_no_title(self, client, auth_headers):
        """测试创建图书缺少书名"""
        response = client.post('/api/v1/books/',
                              headers=auth_headers,
                              json={'author': '作者'})
        data = response.get_json()

        assert data['code'] == 400

    def test_create_book_not_admin(self, client, student_user, student_headers):
        """测试非管理员创建图书"""
        response = client.post('/api/v1/books/',
                              headers=student_headers,
                              json={'title': '新书'})
        data = response.get_json()

        assert data['code'] == 403

    def test_update_book(self, client, book, auth_headers):
        """测试更新图书"""
        response = client.put(f'/api/v1/books/{book.id}',
                             headers=auth_headers,
                             json={'title': '更新后书名', 'stock': 20})
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['title'] == '更新后书名'
        assert data['data']['stock'] == 20

    def test_delete_book(self, client, book, auth_headers):
        """测试删除图书"""
        response = client.delete(f'/api/v1/books/{book.id}',
                                headers=auth_headers)
        data = response.get_json()

        assert data['code'] == 200

        # 验证已删除
        get_resp = client.get(f'/api/v1/books/{book.id}')
        assert get_resp.get_json()['code'] == 404


class TestCategory:
    """分类接口测试"""

    def test_get_categories(self, client, category):
        """测试获取分类树"""
        response = client.get('/api/v1/books/categories')
        data = response.get_json()

        assert data['code'] == 200
        assert len(data['data']) > 0

    def test_create_category(self, client, auth_headers):
        """测试创建分类"""
        response = client.post('/api/v1/books/categories',
                              headers=auth_headers,
                              json={'name': '计算机', 'description': '计算机类图书'})
        data = response.get_json()

        assert response.status_code == 201
        assert data['data']['name'] == '计算机'

    def test_update_category(self, client, category, auth_headers):
        """测试更新分类"""
        response = client.put(f'/api/v1/books/categories/{category.id}',
                             headers=auth_headers,
                             json={'name': '文学艺术', 'description': '文学与艺术类图书'})
        data = response.get_json()

        assert data['code'] == 200
        assert data['data']['name'] == '文学艺术'

    def test_delete_category(self, client, db, auth_headers):
        """测试删除空分类"""
        # 创建一个空分类
        from app.models import Category
        cat = Category(name='待删除', parent_id=0, level=1)
        db.session.add(cat)
        db.session.commit()

        response = client.delete(f'/api/v1/books/categories/{cat.id}',
                                headers=auth_headers)
        data = response.get_json()

        assert data['code'] == 200

    def test_delete_category_with_books(self, client, book, auth_headers):
        """测试删除有图书的分类"""
        response = client.delete(f'/api/v1/books/categories/{book.category_id}',
                                headers=auth_headers)
        data = response.get_json()

        assert data['code'] == 400


class TestStockWarning:
    """库存预警接口测试"""

    def test_stock_warning(self, client, book, auth_headers):
        """测试获取库存预警"""
        response = client.get('/api/v1/books/stock-warning?threshold=5',
                             headers=auth_headers)
        data = response.get_json()

        assert data['code'] == 200
        assert isinstance(data['data'], list)
