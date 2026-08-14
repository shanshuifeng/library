"""
测试配置和 fixtures
"""
import pytest
from app import create_app
from app.extensions import db as _db
from app.models import User, Book, Category, BorrowRecord


@pytest.fixture(scope='session')
def app():
    """创建测试用的 Flask 应用"""
    app = create_app('testing')
    return app


@pytest.fixture(scope='function')
def db(app):
    """创建测试数据库，每个测试函数后清理"""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture(scope='function')
def admin_user(db):
    """创建管理员用户"""
    user = User(
        username='admin',
        email='admin@test.com',
        role='admin',
        status=1,
        real_name='管理员'
    )
    user.set_password('admin123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def student_user(db):
    """创建学生用户"""
    user = User(
        username='student1',
        email='student1@test.com',
        role='student',
        status=1,
        real_name='张三',
        student_id='2021001'
    )
    user.set_password('123456')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def teacher_user(db):
    """创建教师用户"""
    user = User(
        username='teacher1',
        email='teacher1@test.com',
        role='teacher',
        status=1,
        real_name='李老师',
        student_id='T001'
    )
    user.set_password('123456')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def category(db):
    """创建测试分类"""
    cat = Category(
        name='文学',
        parent_id=0,
        level=1,
        sort_order=0,
        description='文学类图书'
    )
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture(scope='function')
def book(db, category):
    """创建测试图书"""
    book = Book(
        title='测试图书',
        author='测试作者',
        isbn='9787020008704',
        publisher='测试出版社',
        category_id=category.id,
        price=50.00,
        stock=10,
        total_stock=10,
        description='这是一本测试用的图书'
    )
    db.session.add(book)
    db.session.commit()
    return book


@pytest.fixture(scope='function')
def admin_token(client, admin_user):
    """获取管理员 Token"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    data = response.get_json()
    return data['data']['access_token']


@pytest.fixture(scope='function')
def student_token(client, student_user):
    """获取学生 Token"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'student1',
        'password': '123456'
    })
    data = response.get_json()
    return data['data']['access_token']


@pytest.fixture(scope='function')
def auth_headers(admin_token):
    """生成带 Token 的请求头"""
    return {'Authorization': f'Bearer {admin_token}'}


@pytest.fixture(scope='function')
def student_headers(student_token):
    """生成带学生 Token 的请求头"""
    return {'Authorization': f'Bearer {student_token}'}
