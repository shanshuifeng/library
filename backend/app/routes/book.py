"""
图书路由
"""
import os
import uuid
from flask import request, current_app
from flask_restx import Namespace, Resource, fields, reqparse, inputs
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from ..utils.response import success_response, error_response, paginate_response
from ..utils.auth import admin_required
from ..utils.audit import log_audit
from ..services import book_service
from ..services import review_service


def check_image_type(file_data):
    """
    通过文件头魔数判断图片类型

    Args:
        file_data: 文件前几个字节的数据

    Returns:
        图片类型或 None
    """
    # JPEG: FF D8 FF
    if file_data[:3] == b'\xff\xd8\xff':
        return 'jpeg'
    # PNG: 89 50 4E 47
    if file_data[:4] == b'\x89PNG':
        return 'png'
    # GIF: 47 49 46 38
    if file_data[:4] == b'GIF8':
        return 'gif'
    # WebP: 52 49 46 46 ... 57 45 42 50
    if file_data[:4] == b'RIFF' and file_data[8:12] == b'WEBP':
        return 'webp'
    # BMP: 42 4D
    if file_data[:2] == b'BM':
        return 'bmp'
    return None

# 创建命名空间
ns = Namespace('books', description='图书管理相关接口')

# ===== 定义模型 =====

book_model = ns.model('Book', {
    'id': fields.Integer(description='图书ID'),
    'title': fields.String(description='书名'),
    'author': fields.String(description='作者'),
    'isbn': fields.String(description='ISBN'),
    'publisher': fields.String(description='出版社'),
    'publish_date': fields.String(description='出版日期'),
    'category_id': fields.Integer(description='分类ID'),
    'price': fields.Float(description='价格'),
    'stock': fields.Integer(description='当前库存'),
    'total_stock': fields.Integer(description='总库存'),
    'description': fields.String(description='描述'),
    'cover_image': fields.String(description='封面图片URL'),
    'location': fields.String(description='馆藏位置'),
    'created_at': fields.String(description='创建时间'),
    'updated_at': fields.String(description='更新时间')
})

book_create_model = ns.model('BookCreate', {
    'title': fields.String(required=True, description='书名', example='数据结构'),
    'author': fields.String(description='作者', example='严蔚敏'),
    'isbn': fields.String(description='ISBN', example='9787302330646'),
    'publisher': fields.String(description='出版社', example='清华大学出版社'),
    'publish_date': fields.String(description='出版日期', example='2012-08-01'),
    'category_id': fields.Integer(description='分类ID'),
    'price': fields.Float(description='价格', example=39.00),
    'stock': fields.Integer(description='库存', example=10),
    'description': fields.String(description='描述'),
    'cover_image': fields.String(description='封面图片URL'),
    'location': fields.String(description='馆藏位置', example='A区3楼')
})

book_update_model = ns.model('BookUpdate', {
    'title': fields.String(description='书名'),
    'author': fields.String(description='作者'),
    'isbn': fields.String(description='ISBN'),
    'publisher': fields.String(description='出版社'),
    'category_id': fields.Integer(description='分类ID'),
    'price': fields.Float(description='价格'),
    'stock': fields.Integer(description='库存'),
    'description': fields.String(description='描述'),
    'cover_image': fields.String(description='封面图片URL'),
    'location': fields.String(description='馆藏位置')
})

category_model = ns.model('Category', {
    'id': fields.Integer(description='分类ID'),
    'name': fields.String(description='分类名称'),
    'parent_id': fields.Integer(description='父分类ID'),
    'sort_order': fields.Integer(description='排序'),
    'description': fields.String(description='描述')
})

category_create_model = ns.model('CategoryCreate', {
    'name': fields.String(required=True, description='分类名称', example='计算机'),
    'parent_id': fields.Integer(description='父分类ID（默认0）', example=0),
    'sort_order': fields.Integer(description='排序（默认0）', example=0),
    'description': fields.String(description='描述')
})

upload_response_model = ns.model('UploadResponse', {
    'cover_image': fields.String(description='图片URL')
})

stock_warning_model = ns.model('StockWarning', {
    'id': fields.Integer(description='图书ID'),
    'title': fields.String(description='书名'),
    'stock': fields.Integer(description='当前库存')
})

review_create_model = ns.model('BookReviewCreate', {
    'rating': fields.Integer(required=True, description='评分（1~5 星）', example=5),
    'content': fields.String(description='评价内容（可选，最长 1000 字）', example='内容详实，受益匪浅')
})


# ===== 图书路由 =====

@ns.route('/')
class BookList(Resource):
    """图书列表"""

    @ns.doc('获取图书列表（分页+搜索）', security='Bearer')
    @ns.expect(ns.parser()
        .add_argument('page', type=int, help='页码（默认1）', location='args')
        .add_argument('per_page', type=int, help='每页数量（默认20）', location='args')
        .add_argument('keyword', type=str, help='搜索关键词', location='args')
        .add_argument('category_id', type=int, help='分类ID', location='args')
    )
    @ns.response(200, '获取成功')
    @jwt_required()
    def get(self):
        """获取图书列表（分页+搜索）"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        keyword = request.args.get('keyword', '').strip()
        category_id = request.args.get('category_id', type=int)

        query = book_service.get_book_list(
            page=page,
            per_page=per_page,
            keyword=keyword if keyword else None,
            category_id=category_id
        )

        return paginate_response(
            query=query,
            schema=SimpleBookSchema(),
            page=page,
            per_page=per_page
        )

    @ns.doc('新增图书（管理员）', security='Bearer')
    @ns.expect(book_create_model)
    
    @ns.response(400, '参数错误')
    @admin_required
    def post(self):
        """新增图书（管理员）"""
        data = request.get_json()

        if not data:
            ns.abort(400, '请求数据不能为空')

        title = data.get('title', '').strip()
        if not title:
            ns.abort(400, '书名不能为空')

        book, error = book_service.create_book(data)

        if error:
            # 记录失败审计日志
            log_audit(
                action='create',
                resource_type='book',
                detail=f'新增图书失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='create',
            resource_type='book',
            resource_id=book.id,
            detail=f'新增图书: {book.title}',
            new_value=book.to_dict()
        )

        return success_response(data=book.to_dict(), message='图书创建成功', code=201)


@ns.route('/<int:book_id>')
class BookDetail(Resource):
    """图书详情"""

    @ns.doc('获取图书详情', security='Bearer')
    @ns.response(404, '图书不存在')
    @jwt_required()
    def get(self, book_id):
        """获取图书详情"""
        book = book_service.get_book_by_id(book_id)

        if not book:
            ns.abort(404, '图书不存在')

        return success_response(data=book.to_dict())

    @ns.doc('更新图书（管理员）', security='Bearer')
    @ns.expect(book_update_model)
    
    @ns.response(404, '图书不存在')
    @admin_required
    def put(self, book_id):
        """更新图书（管理员）"""
        data = request.get_json()

        if not data:
            ns.abort(400, '请求数据不能为空')

        # 获取变更前的数据
        old_book = book_service.get_book_by_id(book_id)
        old_value = old_book.to_dict() if old_book else None

        book, error = book_service.update_book(book_id, data)

        if error:
            # 记录失败审计日志
            log_audit(
                action='update',
                resource_type='book',
                resource_id=book_id,
                detail=f'更新图书失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='update',
            resource_type='book',
            resource_id=book_id,
            detail=f'更新图书: {book.title}',
            old_value=old_value,
            new_value=book.to_dict()
        )

        return success_response(data=book.to_dict(), message='图书更新成功')

    @ns.doc('删除图书（管理员）', security='Bearer')
    @ns.response(200, '删除成功')
    @ns.response(404, '图书不存在')
    @admin_required
    def delete(self, book_id):
        """删除图书（管理员）"""
        # 获取变更前的数据
        old_book = book_service.get_book_by_id(book_id)
        old_value = old_book.to_dict() if old_book else None
        book_title = old_book.title if old_book else f'#{book_id}'

        success, error = book_service.delete_book(book_id)

        if not success:
            # 记录失败审计日志
            log_audit(
                action='delete',
                resource_type='book',
                resource_id=book_id,
                detail=f'删除图书失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='delete',
            resource_type='book',
            resource_id=book_id,
            detail=f'删除图书: {book_title}',
            old_value=old_value
        )

        return success_response(message='图书删除成功')


# ===== 图书评价路由 =====

@ns.route('/<int:book_id>/reviews')
class BookReviewList(Resource):
    """图书评价"""

    @ns.doc('获取图书评价列表', security='Bearer')
    @ns.expect(ns.parser()
        .add_argument('page', type=int, help='页码（默认1）', location='args')
        .add_argument('per_page', type=int, help='每页数量（默认10）', location='args')
    )
    @ns.response(404, '图书不存在')
    def get(self, book_id):
        """获取某图书的评价列表（分页，按时间倒序）"""
        book = book_service.get_book_by_id(book_id)
        if not book:
            ns.abort(404, '图书不存在')

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        pagination = review_service.get_book_reviews(book_id, page=page, per_page=per_page)

        return success_response(data={
            'items': [r.to_dict() for r in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })

    @ns.doc('提交图书评价', security='Bearer')
    @ns.expect(review_create_model)
    @ns.response(400, '参数错误')
    @ns.response(404, '图书不存在')
    @jwt_required()
    def post(self, book_id):
        """提交/更新对图书的评价（每用户每书仅一条）"""
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}

        rating = data.get('rating')
        content = data.get('content')

        review, error = review_service.add_review(
            user_id=user_id,
            book_id=book_id,
            rating=rating,
            content=content
        )

        if error:
            ns.abort(400, error)

        return success_response(data=review.to_dict(), message='评价成功', code=201)


@ns.route('/<int:book_id>/rating')
class BookRating(Resource):
    """图书评分汇总"""

    @ns.doc('获取图书评分汇总', security='Bearer')
    @ns.response(404, '图书不存在')
    def get(self, book_id):
        """获取图书的平均评分、评价数量与评分分布"""
        book = book_service.get_book_by_id(book_id)
        if not book:
            ns.abort(404, '图书不存在')

        distribution = review_service.get_rating_distribution(book_id)

        return success_response(data={
            'avg_rating': float(book.avg_rating) if book.avg_rating else 0,
            'review_count': book.review_count or 0,
            'distribution': distribution
        })


# ===== 分类路由 =====

@ns.route('/categories')
class CategoryList(Resource):
    """分类管理"""

    @ns.doc('获取分类树', security='Bearer')
    @ns.response(500, '服务器错误')
    @jwt_required()
    def get(self):
        """获取分类树"""
        import traceback
        try:
            categories = book_service.get_category_tree()
            return success_response(data=categories)
        except Exception as e:
            traceback.print_exc()
            ns.abort(500, f'获取分类树失败: {str(e)}')

    @ns.doc('新增分类（管理员）', security='Bearer')
    @ns.expect(category_create_model)
    
    @ns.response(400, '参数错误')
    @admin_required
    def post(self):
        """新增分类（管理员）"""
        data = request.get_json()

        if not data:
            ns.abort(400, '请求数据不能为空')

        category, error = book_service.create_category(data)

        if error:
            # 记录失败审计日志
            log_audit(
                action='create',
                resource_type='category',
                detail=f'新增分类失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='create',
            resource_type='category',
            resource_id=category.id,
            detail=f'新增分类: {category.name}',
            new_value=category.to_dict()
        )

        return success_response(data=category.to_dict(), message='分类创建成功', code=201)


@ns.route('/categories/<int:category_id>')
class CategoryDetail(Resource):
    """分类详情"""

    @ns.doc('更新分类（管理员）', security='Bearer')
    @ns.expect(category_create_model)
    
    @ns.response(404, '分类不存在')
    @admin_required
    def put(self, category_id):
        """更新分类（管理员）"""
        data = request.get_json()

        if not data:
            ns.abort(400, '请求数据不能为空')

        # 获取变更前的数据
        from ..models.book import Category
        old_category = Category.query.get(category_id)
        old_value = old_category.to_dict() if old_category else None

        category, error = book_service.update_category(category_id, data)

        if error:
            # 记录失败审计日志
            log_audit(
                action='update',
                resource_type='category',
                resource_id=category_id,
                detail=f'更新分类失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='update',
            resource_type='category',
            resource_id=category_id,
            detail=f'更新分类: {category.name}',
            old_value=old_value,
            new_value=category.to_dict()
        )

        return success_response(data=category.to_dict(), message='分类更新成功')

    @ns.doc('删除分类（管理员）', security='Bearer')
    @ns.response(200, '删除成功')
    @ns.response(404, '分类不存在')
    @admin_required
    def delete(self, category_id):
        """删除分类（管理员）"""
        # 获取变更前的数据
        from ..models.book import Category
        old_category = Category.query.get(category_id)
        old_value = old_category.to_dict() if old_category else None
        category_name = old_category.name if old_category else f'#{category_id}'

        success, error = book_service.delete_category(category_id)

        if not success:
            # 记录失败审计日志
            log_audit(
                action='delete',
                resource_type='category',
                resource_id=category_id,
                detail=f'删除分类失败: {error}',
                status='failed',
                error_message=error
            )
            ns.abort(400, error)

        # 记录成功审计日志
        log_audit(
            action='delete',
            resource_type='category',
            resource_id=category_id,
            detail=f'删除分类: {category_name}',
            old_value=old_value
        )

        return success_response(message='分类删除成功')


# ===== 其他路由 =====

@ns.route('/stock-warning')
class StockWarning(Resource):
    """库存预警"""

    @ns.doc('获取库存预警图书（管理员）', security='Bearer')
    @ns.expect(ns.parser().add_argument('threshold', type=int, help='库存预警阈值（默认5）', location='args'))
    @ns.response(200, '获取成功')
    @admin_required
    def get(self):
        """获取库存预警图书（管理员）"""
        threshold = request.args.get('threshold', 5, type=int)
        books = book_service.get_stock_warning(threshold)

        return success_response(data=books)


@ns.route('/upload-cover')
class UploadCover(Resource):
    """上传封面"""

    @ns.doc('上传图书封面图片（管理员）', security='Bearer',
            consumes=['multipart/form-data'])
    @ns.expect(ns.parser()
        .add_argument('file', type=str, help='图片文件', location='files', required=True)
    )
    
    @ns.response(400, '文件格式错误')
    @admin_required
    def post(self):
        """上传图书封面图片（管理员）"""
        # 检查是否有文件
        if 'file' not in request.files:
            log_audit(
                action='upload',
                resource_type='cover',
                detail='上传封面失败: 未上传文件',
                status='failed',
                error_message='未上传文件'
            )
            ns.abort(400, '未上传文件')

        file = request.files['file']

        # 检查文件名
        if file.filename == '':
            log_audit(
                action='upload',
                resource_type='cover',
                detail='上传封面失败: 未选择文件',
                status='failed',
                error_message='未选择文件'
            )
            ns.abort(400, '未选择文件')

        # 检查文件类型（扩展名）
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        filename = secure_filename(file.filename)
        if not filename:
            filename = 'upload'

        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in allowed_extensions:
            log_audit(
                action='upload',
                resource_type='cover',
                detail=f'上传封面失败: 不支持的文件类型 {ext}',
                status='failed',
                error_message=f'不支持的文件类型'
            )
            ns.abort(400, f'不支持的文件类型，仅支持 {", ".join(allowed_extensions)}')

        # 校验文件头（魔数），防止恶意文件伪装
        file_data = file.read(12)  # 读取前12字节
        file.seek(0)  # 重置文件指针

        # 检查真实文件类型
        file_type = check_image_type(file_data)
        if file_type and file_type not in ('jpeg', 'png', 'gif', 'webp'):
            log_audit(
                action='upload',
                resource_type='cover',
                detail=f'上传封面失败: 文件内容与扩展名不匹配',
                status='failed',
                error_message='文件内容与扩展名不匹配'
            )
            ns.abort(400, '文件内容与扩展名不匹配')

        # 检查文件大小（限制 5MB）
        file.seek(0, 2)  # 移到文件末尾
        file_size = file.tell()
        file.seek(0)  # 重置
        if file_size > 5 * 1024 * 1024:
            log_audit(
                action='upload',
                resource_type='cover',
                detail=f'上传封面失败: 文件大小超过5MB',
                status='failed',
                error_message='文件大小不能超过 5MB'
            )
            ns.abort(400, '文件大小不能超过 5MB')

        # 生成唯一文件名
        new_filename = f'{uuid.uuid4().hex}.{ext}'

        # 保存文件
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        # 使用 cover 子目录
        cover_folder = os.path.join(upload_folder, 'covers')
        os.makedirs(cover_folder, exist_ok=True)

        file_path = os.path.join(cover_folder, new_filename)
        file.save(file_path)

        # 返回访问 URL
        cover_url = f'/uploads/covers/{new_filename}'

        # 记录成功审计日志
        log_audit(
            action='upload',
            resource_type='cover',
            detail=f'上传封面: {filename} -> {new_filename}',
            new_value={'cover_image': cover_url, 'original_name': filename, 'file_size': file_size}
        )

        return success_response(data={'cover_image': cover_url}, message='封面上传成功')


class SimpleBookSchema:
    """简单的图书序列化器（用于分页列表）"""

    def dump(self, books):
        """序列化图书列表"""
        return [book.to_dict() for book in books]
