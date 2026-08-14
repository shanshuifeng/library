"""
图书服务层
"""
from ..models.book import Book
from ..models.category import Category
from ..extensions import db


def get_book_list(page=1, per_page=20, keyword=None, category_id=None):
    """
    获取图书列表（支持分页和搜索）

    Args:
        page: 页码
        per_page: 每页数量
        keyword: 搜索关键词（标题、作者、ISBN）
        category_id: 分类ID

    Returns:
        SQLAlchemy 分页查询对象
    """
    query = Book.query

    # 关键词搜索
    if keyword:
        search_term = f'%{keyword}%'
        query = query.filter(
            db.or_(
                Book.title.ilike(search_term),
                Book.author.ilike(search_term),
                Book.isbn.ilike(search_term)
            )
        )

    # 分类筛选
    if category_id:
        query = query.filter_by(category_id=category_id)

    # 按创建时间降序排列
    query = query.order_by(Book.created_at.desc())

    return query


def get_book_by_id(book_id):
    """
    根据ID获取图书

    Args:
        book_id: 图书ID

    Returns:
        Book 对象或 None
    """
    return Book.query.get(book_id)


def create_book(data):
    """
    创建图书

    Args:
        data: 图书数据字典

    Returns:
        (Book, None) 成功返回图书对象
        (None, str) 失败返回错误信息
    """
    # 检查ISBN是否已存在
    if data.get('isbn'):
        existing = Book.query.filter_by(isbn=data['isbn']).first()
        if existing:
            return None, 'ISBN已存在'

    book = Book(
        title=data['title'],
        author=data.get('author'),
        isbn=data.get('isbn'),
        publisher=data.get('publisher'),
        publish_date=data.get('publish_date'),
        category_id=data.get('category_id'),
        price=data.get('price'),
        stock=data.get('stock', 0),
        total_stock=data.get('total_stock', 0),
        description=data.get('description'),
        cover_image=data.get('cover_image'),
        location=data.get('location')
    )

    db.session.add(book)
    db.session.commit()

    return book, None


def update_book(book_id, data):
    """
    更新图书

    Args:
        book_id: 图书ID
        data: 更新数据字典

    Returns:
        (Book, None) 成功返回图书对象
        (None, str) 失败返回错误信息
    """
    book = Book.query.get(book_id)
    if not book:
        return None, '图书不存在'

    # 检查ISBN是否与其他图书冲突
    if data.get('isbn') and data['isbn'] != book.isbn:
        existing = Book.query.filter_by(isbn=data['isbn']).first()
        if existing:
            return None, 'ISBN已被其他图书使用'

    # 更新字段
    if 'title' in data:
        book.title = data['title']
    if 'author' in data:
        book.author = data['author']
    if 'isbn' in data:
        book.isbn = data['isbn']
    if 'publisher' in data:
        book.publisher = data['publisher']
    if 'publish_date' in data:
        book.publish_date = data['publish_date']
    if 'category_id' in data:
        book.category_id = data['category_id']
    if 'price' in data:
        book.price = data['price']
    if 'stock' in data:
        book.stock = data['stock']
    if 'total_stock' in data:
        book.total_stock = data['total_stock']
    if 'description' in data:
        book.description = data['description']
    if 'cover_image' in data:
        book.cover_image = data['cover_image']
    if 'location' in data:
        book.location = data['location']

    db.session.commit()

    return book, None


def delete_book(book_id):
    """
    删除图书

    Args:
        book_id: 图书ID

    Returns:
        (True, None) 成功
        (False, str) 失败返回错误信息
    """
    book = Book.query.get(book_id)
    if not book:
        return False, '图书不存在'

    # 检查是否有未归还的借阅记录
    from ..models.borrow import BorrowRecord
    active_borrows = BorrowRecord.query.filter_by(
        book_id=book_id, status='borrowed'
    ).count()
    if active_borrows > 0:
        return False, '该图书有未归还的借阅记录，无法删除'

    db.session.delete(book)
    db.session.commit()

    return True, None


def get_category_tree():
    """
    获取分类树

    Returns:
        分类树列表
    """
    # 获取所有顶级分类（parent_id 为 NULL）
    root_categories = Category.query.filter(
        Category.parent_id.is_(None)
    ).order_by(Category.sort_order).all()

    return [cat.to_dict() for cat in root_categories]


def get_all_categories():
    """
    获取所有分类列表（扁平化）

    Returns:
        分类列表
    """
    categories = Category.query.order_by(Category.level, Category.sort_order).all()
    return [cat.to_simple_dict() for cat in categories]


def create_category(data):
    """
    创建图书分类

    Args:
        data: 分类数据字典
            name: 分类名称（必填）
            parent_id: 父分类ID（默认0，表示顶级分类）
            sort_order: 排序值（默认0）
            description: 分类描述

    Returns:
        (Category, None) 成功返回分类对象
        (None, str) 失败返回错误信息
    """
    name = data.get('name', '').strip()
    if not name:
        return None, '分类名称不能为空'

    parent_id = data.get('parent_id') or None

    # 检查父分类是否存在
    if parent_id:
        parent = Category.query.get(parent_id)
        if not parent:
            return None, '父分类不存在'
        level = parent.level + 1
    else:
        level = 1

    # 检查同级分类名是否重复
    existing = Category.query.filter_by(
        name=name, parent_id=parent_id
    ).first()
    if existing:
        return None, '同级下已存在同名分类'

    category = Category(
        name=name,
        parent_id=parent_id,
        level=level,
        sort_order=data.get('sort_order', 0),
        description=data.get('description')
    )

    db.session.add(category)
    db.session.commit()

    return category, None


def update_category(category_id, data):
    """
    更新图书分类

    Args:
        category_id: 分类ID
        data: 更新数据字典

    Returns:
        (Category, None) 成功返回分类对象
        (None, str) 失败返回错误信息
    """
    category = Category.query.get(category_id)
    if not category:
        return None, '分类不存在'

    # 如果修改了名称，检查同级是否重名
    if 'name' in data and data['name'] != category.name:
        name = data['name'].strip()
        if not name:
            return None, '分类名称不能为空'
        existing = Category.query.filter_by(
            name=name, parent_id=category.parent_id
        ).first()
        if existing:
            return None, '同级下已存在同名分类'
        category.name = name

    # 如果修改了父分类，需要重新计算层级
    if 'parent_id' in data and data['parent_id'] != category.parent_id:
        new_parent_id = data['parent_id'] or None
        if new_parent_id:
            # 不能将自己设为父分类
            if new_parent_id == category_id:
                return None, '不能将自己设为父分类'

            # 检查是否形成循环引用（子分类不能设为父分类）
            if _is_child_category(category_id, new_parent_id):
                return None, '不能将子分类设为父分类，会形成循环引用'

            parent = Category.query.get(new_parent_id)
            if not parent:
                return None, '父分类不存在'
            category.level = parent.level + 1
        else:
            category.level = 1
        category.parent_id = new_parent_id

    if 'sort_order' in data:
        category.sort_order = data['sort_order']
    if 'description' in data:
        category.description = data['description']

    db.session.commit()

    return category, None


def delete_category(category_id):
    """
    删除图书分类

    Args:
        category_id: 分类ID

    Returns:
        (True, None) 成功
        (False, str) 失败返回错误信息
    """
    category = Category.query.get(category_id)
    if not category:
        return False, '分类不存在'

    # 检查是否有子分类
    children = Category.query.filter_by(parent_id=category_id).count()
    if children > 0:
        return False, '该分类下有子分类，无法删除'

    # 检查是否有图书使用此分类
    book_count = Book.query.filter_by(category_id=category_id).count()
    if book_count > 0:
        return False, f'该分类下有{book_count}本图书，无法删除'

    db.session.delete(category)
    db.session.commit()

    return True, None


def _is_child_category(parent_id, target_id):
    """
    检查 target_id 是否是 parent_id 的子孙分类

    Args:
        parent_id: 父分类ID
        target_id: 目标分类ID

    Returns:
        True 如果是子孙分类
    """
    children = Category.query.filter_by(parent_id=parent_id).all()
    for child in children:
        if child.id == target_id:
            return True
        if _is_child_category(child.id, target_id):
            return True
    return False


def get_stock_warning(threshold=5):
    """
    获取库存预警图书列表

    Args:
        threshold: 库存预警阈值（默认5）

    Returns:
        库存低于阈值的图书列表
    """
    books = Book.query.filter(
        Book.stock <= threshold,
        Book.stock >= 0
    ).order_by(Book.stock.asc()).all()

    return [book.to_dict() for book in books]
