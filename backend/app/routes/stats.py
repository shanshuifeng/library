"""
统计与系统管理路由
"""
from datetime import date, timedelta
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required

from ..utils.response import success_response, error_response
from ..utils.auth import admin_required
from ..models.user import User
from ..models.book import Book
from ..models.borrow import BorrowRecord
from ..models.system_config import SystemConfig
from ..extensions import db
from ..services import system_config_service

# 创建命名空间
ns = Namespace('stats', description='统计与系统配置相关接口')

# ===== 定义模型 =====

overview_model = ns.model('Overview', {
    'bookCount': fields.Integer(description='总图书数'),
    'borrowCount': fields.Integer(description='总借阅数'),
    'userCount': fields.Integer(description='总用户数'),
    'overdueCount': fields.Integer(description='逾期未还数'),
    'currentBorrowed': fields.Integer(description='当前借出数')
})

daily_trend_model = ns.model('DailyTrend', {
    'dates': fields.List(fields.String, description='日期列表'),
    'borrows': fields.List(fields.Integer, description='每日借阅数'),
    'returns': fields.List(fields.Integer, description='每日归还数')
})

trend_item_model = ns.model('TrendItem', {
    'date': fields.String(description='日期'),
    'count': fields.Integer(description='借阅数量')
})

popular_book_model = ns.model('PopularBook', {
    'id': fields.Integer(description='图书ID'),
    'title': fields.String(description='书名'),
    'author': fields.String(description='作者'),
    'isbn': fields.String(description='ISBN'),
    'cover_image': fields.String(description='封面图片'),
    'borrow_count': fields.Integer(description='借阅次数')
})

config_model = ns.model('SystemConfig', {
    'id': fields.Integer(description='配置ID'),
    'config_key': fields.String(description='配置键'),
    'config_value': fields.String(description='配置值'),
    'description': fields.String(description='描述'),
    'created_at': fields.String(description='创建时间'),
    'updated_at': fields.String(description='更新时间')
})

config_create_model = ns.model('ConfigCreate', {
    'config_key': fields.String(required=True, description='配置键', example='max_borrow_count'),
    'config_value': fields.String(required=True, description='配置值', example='10'),
    'description': fields.String(description='描述', example='最大借阅数量')
})

init_config_response = ns.model('InitConfigResponse', {
    'created_count': fields.Integer(description='创建的配置数量')
})


# ===== 统计接口 =====

@ns.route('/overview')
class Overview(Resource):
    """系统概览"""

    @ns.doc('系统概览统计', security='Bearer')
    @jwt_required()
    def get(self):
        """系统概览统计"""
        total_users = User.query.count()
        total_books = Book.query.count()
        total_borrows = BorrowRecord.query.count()
        current_borrowed = BorrowRecord.query.filter_by(status='borrowed').count()
        from datetime import date
        overdue = BorrowRecord.query.filter(
            BorrowRecord.status == 'borrowed',
            BorrowRecord.due_date < date.today()
        ).count()

        return success_response(data={
            'bookCount': total_books,
            'borrowCount': total_borrows,
            'userCount': total_users,
            'overdueCount': overdue,
            'currentBorrowed': current_borrowed
        })


@ns.route('/daily-trend')
class DailyTrend(Resource):
    """每日趋势"""

    @ns.doc('每日借阅/归还趋势（近30天）', security='Bearer')
    @jwt_required()
    def get(self):
        """每日借阅/归还趋势（近30天）"""
        today = date.today()
        start_date = today - timedelta(days=29)

        # 查询近30天每天的借阅数量
        borrow_counts = db.session.query(
            BorrowRecord.borrow_date,
            db.func.count(BorrowRecord.id)
        ).filter(
            BorrowRecord.borrow_date >= start_date
        ).group_by(
            BorrowRecord.borrow_date
        ).all()

        # 查询近30天每天的归还数量
        return_counts = db.session.query(
            BorrowRecord.return_date,
            db.func.count(BorrowRecord.id)
        ).filter(
            BorrowRecord.return_date >= start_date,
            BorrowRecord.status == 'returned'
        ).group_by(
            BorrowRecord.return_date
        ).all()

        borrow_dict = {str(row[0].date() if hasattr(row[0], 'date') else row[0]): row[1] for row in borrow_counts}
        return_dict = {str(row[0].date() if hasattr(row[0], 'date') else row[0]): row[1] for row in return_counts}

        dates = []
        borrows = []
        returns = []
        for i in range(30):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.isoformat()
            dates.append(date_str)
            borrows.append(borrow_dict.get(date_str, 0))
            returns.append(return_dict.get(date_str, 0))

        return success_response(data={
            'dates': dates,
            'borrows': borrows,
            'returns': returns
        })


@ns.route('/borrow-trend')
class BorrowTrend(Resource):
    """借阅趋势"""

    @ns.doc('借阅趋势（近30天）', security='Bearer')
    
    @admin_required
    def get(self):
        """借阅趋势（近30天）"""
        today = date.today()
        start_date = today - timedelta(days=29)

        # 查询近30天每天的借阅数量
        daily_counts = db.session.query(
            BorrowRecord.borrow_date,
            db.func.count(BorrowRecord.id)
        ).filter(
            BorrowRecord.borrow_date >= start_date
        ).group_by(
            BorrowRecord.borrow_date
        ).all()

        # 转换为字典
        count_dict = {str(row[0]): row[1] for row in daily_counts}

        # 生成30天的完整数据
        trend = []
        for i in range(30):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.isoformat()
            trend.append({
                'date': date_str,
                'count': count_dict.get(date_str, 0)
            })

        return success_response(data=trend)


@ns.route('/popular-books')
class PopularBooks(Resource):
    """热门图书"""

    @ns.doc('热门图书（借阅次数TOP10）', security='Bearer')
    
    @admin_required
    def get(self):
        """热门图书（借阅次数TOP10）"""
        # 查询借阅次数最多的10本书
        popular = db.session.query(
            BorrowRecord.book_id,
            db.func.count(BorrowRecord.id).label('borrow_count')
        ).group_by(
            BorrowRecord.book_id
        ).order_by(
            db.desc('borrow_count')
        ).limit(10).all()

        # 获取图书详情
        result = []
        for item in popular:
            book = Book.query.get(item[0])
            if book:
                result.append({
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'isbn': book.isbn,
                    'cover_image': book.cover_image,
                    'borrow_count': item[1]
                })

        return success_response(data=result)


# ===== 系统配置接口 =====

@ns.route('/config')
class ConfigList(Resource):
    """系统配置"""

    @ns.doc('获取所有系统配置', security='Bearer')
    
    @admin_required
    def get(self):
        """获取所有系统配置"""
        configs = system_config_service.get_all_configs()
        return success_response(data=configs)

    @ns.doc('新增系统配置', security='Bearer')
    @ns.expect(config_create_model)
    
    @ns.response(400, '参数错误')
    @admin_required
    def post(self):
        """新增系统配置"""
        data = request.get_json()

        if not data:
            ns.abort(400, '请求数据不能为空')

        config, error = system_config_service.create_config(data)

        if error:
            ns.abort(400, error)

        return success_response(data=config.to_dict(), message='配置创建成功', code=201)


@ns.route('/config/<int:config_id>')
class ConfigDetail(Resource):
    """配置详情"""

    @ns.doc('更新系统配置', security='Bearer')
    @ns.expect(config_create_model)
    
    @ns.response(404, '配置不存在')
    @admin_required
    def put(self, config_id):
        """更新系统配置"""
        data = request.get_json()

        if not data:
            ns.abort(400, '请求数据不能为空')

        config, error = system_config_service.update_config(config_id, data)

        if error:
            ns.abort(400, error)

        return success_response(data=config.to_dict(), message='配置更新成功')

    @ns.doc('删除系统配置', security='Bearer')
    @ns.response(200, '删除成功')
    @ns.response(404, '配置不存在')
    @admin_required
    def delete(self, config_id):
        """删除系统配置"""
        success, error = system_config_service.delete_config(config_id)

        if not success:
            ns.abort(400, error)

        return success_response(message='配置删除成功')


@ns.route('/config/init')
class InitConfigs(Resource):
    """初始化配置"""

    @ns.doc('初始化默认系统配置', security='Bearer')
    
    @admin_required
    def post(self):
        """初始化默认系统配置"""
        created = system_config_service.init_default_configs()

        return success_response(
            data={'created_count': created},
            message=f'初始化完成，创建了{created}项默认配置'
        )
