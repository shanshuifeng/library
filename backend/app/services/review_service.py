"""
图书评价服务层
"""
from datetime import datetime
from ..models.book import Book
from ..models.review import BookReview
from ..extensions import db

# 评价内容最大长度
MAX_CONTENT_LENGTH = 1000


def add_review(user_id, book_id, rating, content=None):
    """
    新增/更新图书评价（每用户每书仅保留一条，存在则覆盖）

    Args:
        user_id: 当前用户 ID
        book_id: 图书 ID
        rating:  评分（1~5 整数）
        content: 评价内容（可选，最长 1000 字）

    Returns:
        (BookReview, None) 成功
        (None, str)        失败返回错误信息
    """
    # 校验图书是否存在
    book = Book.query.get(book_id)
    if not book:
        return None, '图书不存在'

    # 校验评分
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return None, '评分必须是 1-5 的整数'
    if rating < 1 or rating > 5:
        return None, '评分必须在 1-5 之间'

    # 校验内容长度
    if content is not None:
        content = content.strip()
        if len(content) > MAX_CONTENT_LENGTH:
            return None, f'评价内容不能超过 {MAX_CONTENT_LENGTH} 字'

    # 每用户每书只保留一条评价：已存在则更新，否则新建
    review = BookReview.query.filter_by(user_id=user_id, book_id=book_id).first()
    if review:
        review.rating = rating
        review.content = content
        review.updated_at = datetime.now()
    else:
        review = BookReview(user_id=user_id, book_id=book_id, rating=rating, content=content)
        db.session.add(review)

    # 先 flush，使下方聚合查询能读到最新状态
    db.session.flush()

    # 维护图书聚合评分（应用层主逻辑；部署到 PostgreSQL/openGauss 时，
    # 同名触发器 trg_after_review_maintain_rating 也会再维护一次，结果一致——双保险）
    _recalculate(book_id)

    return review, None


def _recalculate(book_id):
    """
    重算并更新图书的平均评分与评价数量

    与应用层 add_review 配套，也作为 PG 触发器失效/直插 SQL 时的兜底。
    """
    agg = db.session.query(
        db.func.avg(BookReview.rating),
        db.func.count(BookReview.id)
    ).filter_by(book_id=book_id).first()

    avg = float(agg[0]) if agg[0] is not None else 0.0
    count = agg[1] or 0

    book = Book.query.get(book_id)
    if book:
        book.avg_rating = round(avg, 2)
        book.review_count = count
        db.session.commit()


def get_book_reviews(book_id, page=1, per_page=10):
    """
    获取某图书的评价列表（分页，按时间倒序）

    Returns:
        SQLAlchemy 分页对象（.items / .total / .pages）
    """
    query = BookReview.query.filter_by(book_id=book_id).order_by(BookReview.created_at.desc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_rating_distribution(book_id):
    """
    获取某图书的评分分布（1~5 星各多少条）

    Returns:
        dict: {1: x, 2: y, 3: z, 4: w, 5: v}
    """
    rows = db.session.query(
        BookReview.rating,
        db.func.count(BookReview.id)
    ).filter_by(book_id=book_id).group_by(BookReview.rating).all()

    dist = {i: 0 for i in range(1, 6)}
    for rating, cnt in rows:
        dist[int(rating)] = cnt
    return dist
