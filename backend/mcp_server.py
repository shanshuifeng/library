"""
大学图书管理系统 MCP Server
将所有 REST API 接口暴露为 MCP 工具，供 AI 模型调用
"""
import os
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# 创建 MCP Server
mcp = FastMCP(
    name="大学图书管理系统",
    instructions="图书管理、借阅、用户管理等接口的 MCP 工具集。提供图书检索、借阅管理、用户管理、统计分析等功能。"
)

# 后端 API 基础地址
API_BASE = os.getenv("API_BASE_URL", "http://localhost:5000/api/v1")


async def _request(method: str, path: str, token: str = None, json: dict = None, params: dict = None) -> dict:
    """统一请求封装"""
    url = f"{API_BASE}{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(method, url, headers=headers, json=json, params=params)
        return resp.json()


# ==================== 认证模块 ====================

@mcp.tool()
async def login(username: str, password: str) -> dict:
    """
    用户登录，获取访问令牌

    Args:
        username: 用户名
        password: 密码

    Returns:
        包含 access_token、refresh_token 和用户信息
    """
    return await _request("POST", "/auth/login", json={"username": username, "password": password})


@mcp.tool()
async def register(username: str, password: str, email: str = None, phone: str = None,
                   real_name: str = None, student_id: str = None) -> dict:
    """
    用户注册

    Args:
        username: 用户名
        password: 密码
        email: 邮箱（可选）
        phone: 手机号（可选）
        real_name: 真实姓名（可选）
        student_id: 学号/工号（可选）

    Returns:
        注册结果
    """
    data = {"username": username, "password": password}
    if email:
        data["email"] = email
    if phone:
        data["phone"] = phone
    if real_name:
        data["real_name"] = real_name
    if student_id:
        data["student_id"] = student_id
    return await _request("POST", "/auth/register", json=data)


@mcp.tool()
async def get_profile(token: str) -> dict:
    """
    获取当前用户个人信息

    Args:
        token: 访问令牌（从 login 获取）

    Returns:
        用户详细信息
    """
    return await _request("GET", "/auth/profile", token=token)


@mcp.tool()
async def update_profile(token: str, email: str = None, phone: str = None, real_name: str = None) -> dict:
    """
    更新个人信息

    Args:
        token: 访问令牌
        email: 邮箱（可选）
        phone: 手机号（可选）
        real_name: 真实姓名（可选）

    Returns:
        更新结果
    """
    data = {}
    if email:
        data["email"] = email
    if phone:
        data["phone"] = phone
    if real_name:
        data["real_name"] = real_name
    return await _request("PUT", "/auth/profile", token=token, json=data)


@mcp.tool()
async def change_password(token: str, old_password: str, new_password: str) -> dict:
    """
    修改密码

    Args:
        token: 访问令牌
        old_password: 旧密码
        new_password: 新密码

    Returns:
        修改结果
    """
    return await _request("PUT", "/auth/password", token=token,
                          json={"old_password": old_password, "new_password": new_password})


# ==================== 图书模块 ====================

@mcp.tool()
async def get_books(page: int = 1, per_page: int = 20, keyword: str = None, category_id: int = None) -> dict:
    """
    获取图书列表（分页+搜索）

    Args:
        page: 页码（默认1）
        per_page: 每页数量（默认20）
        keyword: 搜索关键词（可选）
        category_id: 分类ID（可选）

    Returns:
        图书列表及分页信息
    """
    params = {"page": page, "per_page": per_page}
    if keyword:
        params["keyword"] = keyword
    if category_id:
        params["category_id"] = category_id
    return await _request("GET", "/books/", params=params)


@mcp.tool()
async def get_book(book_id: int) -> dict:
    """
    获取图书详情

    Args:
        book_id: 图书ID

    Returns:
        图书详细信息
    """
    return await _request("GET", f"/books/{book_id}")


@mcp.tool()
async def create_book(token: str, title: str, author: str = None, isbn: str = None,
                      publisher: str = None, category_id: int = None, price: float = None,
                      stock: int = None, description: str = None, location: str = None) -> dict:
    """
    新增图书（需要管理员权限）

    Args:
        token: 访问令牌（管理员）
        title: 书名
        author: 作者（可选）
        isbn: ISBN（可选）
        publisher: 出版社（可选）
        category_id: 分类ID（可选）
        price: 价格（可选）
        stock: 库存（可选）
        description: 描述（可选）
        location: 馆藏位置（可选）

    Returns:
        创建结果
    """
    data = {"title": title}
    if author:
        data["author"] = author
    if isbn:
        data["isbn"] = isbn
    if publisher:
        data["publisher"] = publisher
    if category_id:
        data["category_id"] = category_id
    if price:
        data["price"] = price
    if stock:
        data["stock"] = stock
    if description:
        data["description"] = description
    if location:
        data["location"] = location
    return await _request("POST", "/books/", token=token, json=data)


@mcp.tool()
async def update_book(token: str, book_id: int, title: str = None, author: str = None,
                      isbn: str = None, stock: int = None, price: float = None) -> dict:
    """
    更新图书信息（需要管理员权限）

    Args:
        token: 访问令牌（管理员）
        book_id: 图书ID
        title: 书名（可选）
        author: 作者（可选）
        isbn: ISBN（可选）
        stock: 库存（可选）
        price: 价格（可选）

    Returns:
        更新结果
    """
    data = {}
    if title:
        data["title"] = title
    if author:
        data["author"] = author
    if isbn:
        data["isbn"] = isbn
    if stock is not None:
        data["stock"] = stock
    if price is not None:
        data["price"] = price
    return await _request("PUT", f"/books/{book_id}", token=token, json=data)


@mcp.tool()
async def delete_book(token: str, book_id: int) -> dict:
    """
    删除图书（需要管理员权限）

    Args:
        token: 访问令牌（管理员）
        book_id: 图书ID

    Returns:
        删除结果
    """
    return await _request("DELETE", f"/books/{book_id}", token=token)


@mcp.tool()
async def get_categories() -> dict:
    """
    获取分类树

    Returns:
        分类树形结构
    """
    return await _request("GET", "/books/categories")


@mcp.tool()
async def create_category(token: str, name: str, parent_id: int = None, description: str = None) -> dict:
    """
    新增分类（需要管理员权限）

    Args:
        token: 访问令牌（管理员）
        name: 分类名称
        parent_id: 父分类ID（可选，默认为顶级分类）
        description: 描述（可选）

    Returns:
        创建结果
    """
    data = {"name": name}
    if parent_id:
        data["parent_id"] = parent_id
    if description:
        data["description"] = description
    return await _request("POST", "/books/categories", token=token, json=data)


@mcp.tool()
async def get_stock_warning(token: str, threshold: int = 5) -> dict:
    """
    获取库存预警图书（需要管理员权限）

    Args:
        token: 访问令牌（管理员）
        threshold: 库存预警阈值（默认5）

    Returns:
        库存不足的图书列表
    """
    return await _request("GET", "/books/stock-warning", token=token, params={"threshold": threshold})


# ==================== 借阅模块 ====================

@mcp.tool()
async def borrow_book(token: str, book_id: int, borrow_days: int = None) -> dict:
    """
    借书

    Args:
        token: 访问令牌
        book_id: 图书ID
        borrow_days: 借阅天数（可选，默认从系统配置获取）

    Returns:
        借阅记录
    """
    data = {"book_id": book_id}
    if borrow_days:
        data["borrow_days"] = borrow_days
    return await _request("POST", "/borrows/", token=token, json=data)


@mcp.tool()
async def return_book(token: str, record_id: int) -> dict:
    """
    还书

    Args:
        token: 访问令牌
        record_id: 借阅记录ID

    Returns:
        归还结果（含罚款信息）
    """
    return await _request("PUT", f"/borrows/{record_id}/return", token=token)


@mcp.tool()
async def renew_book(token: str, record_id: int) -> dict:
    """
    续借图书

    Args:
        token: 访问令牌
        record_id: 借阅记录ID

    Returns:
        续借结果（更新后的到期日期）
    """
    return await _request("PUT", f"/borrows/{record_id}/renew", token=token)


@mcp.tool()
async def get_borrow_list(token: str, page: int = 1, per_page: int = 20, status: str = None) -> dict:
    """
    获取借阅记录列表

    Args:
        token: 访问令牌
        page: 页码（默认1）
        per_page: 每页数量（默认20）
        status: 筛选状态（borrowed/returned/overdue，可选）

    Returns:
        借阅记录列表
    """
    params = {"page": page, "per_page": per_page}
    if status:
        params["status"] = status
    return await _request("GET", "/borrows/", token=token, params=params)


@mcp.tool()
async def get_user_borrows(token: str, user_id: int, page: int = 1, status: str = None) -> dict:
    """
    获取指定用户的借阅记录

    Args:
        token: 访问令牌
        user_id: 用户ID
        page: 页码（默认1）
        status: 筛选状态（可选）

    Returns:
        该用户的借阅记录列表
    """
    params = {"page": page}
    if status:
        params["status"] = status
    return await _request("GET", f"/borrows/user/{user_id}", token=token, params=params)


# ==================== 用户管理模块（管理员） ====================

@mcp.tool()
async def get_users(token: str, page: int = 1, per_page: int = 20,
                    keyword: str = None, role: str = None) -> dict:
    """
    获取用户列表（需要管理员权限）

    Args:
        token: 访问令牌（管理员）
        page: 页码（默认1）
        per_page: 每页数量（默认20）
        keyword: 搜索关键词（可选）
        role: 角色筛选（admin/teacher/student，可选）

    Returns:
        用户列表
    """
    params = {"page": page, "per_page": per_page}
    if keyword:
        params["keyword"] = keyword
    if role:
        params["role"] = role
    return await _request("GET", "/users/", token=token, params=params)


@mcp.tool()
async def create_user(token: str, username: str, password: str, email: str = None,
                      phone: str = None, real_name: str = None, student_id: str = None,
                      role: str = "student") -> dict:
    """
    创建用户（需要管理员权限）

    Args:
        token: 访问令牌（管理员）
        username: 用户名
        password: 密码
        email: 邮箱（可选）
        phone: 手机号（可选）
        real_name: 真实姓名（可选）
        student_id: 学号/工号（可选）
        role: 角色（admin/teacher/student，默认student）

    Returns:
        创建结果
    """
    data = {"username": username, "password": password, "role": role}
    if email:
        data["email"] = email
    if phone:
        data["phone"] = phone
    if real_name:
        data["real_name"] = real_name
    if student_id:
        data["student_id"] = student_id
    return await _request("POST", "/users/", token=token, json=data)


@mcp.tool()
async def update_user(token: str, user_id: int, email: str = None, phone: str = None,
                      real_name: str = None, role: str = None, status: int = None,
                      password: str = None) -> dict:
    """
    更新用户信息（需要管理员权限）

    Args:
        token: 访问令牌（管理员）
        user_id: 用户ID
        email: 邮箱（可选）
        phone: 手机号（可选）
        real_name: 真实姓名（可选）
        role: 角色（可选）
        status: 状态（1启用/0禁用，可选）
        password: 新密码（可选）

    Returns:
        更新结果
    """
    data = {}
    if email:
        data["email"] = email
    if phone:
        data["phone"] = phone
    if real_name:
        data["real_name"] = real_name
    if role:
        data["role"] = role
    if status is not None:
        data["status"] = status
    if password:
        data["password"] = password
    return await _request("PUT", f"/users/{user_id}", token=token, json=data)


@mcp.tool()
async def delete_user(token: str, user_id: int) -> dict:
    """
    删除用户（需要管理员权限）

    Args:
        token: 访问令牌（管理员）
        user_id: 用户ID

    Returns:
        删除结果
    """
    return await _request("DELETE", f"/users/{user_id}", token=token)


# ==================== 预约模块 ====================

@mcp.tool()
async def create_reservation(token: str, book_id: int) -> dict:
    """
    创建图书预约

    Args:
        token: 访问令牌
        book_id: 图书ID

    Returns:
        预约记录
    """
    return await _request("POST", "/reservations/", token=token, json={"book_id": book_id})


@mcp.tool()
async def get_my_reservations(token: str, page: int = 1, per_page: int = 20) -> dict:
    """
    获取我的预约列表

    Args:
        token: 访问令牌
        page: 页码（默认1）
        per_page: 每页数量（默认20）

    Returns:
        我的预约列表
    """
    return await _request("GET", "/reservations/my", token=token, params={"page": page, "per_page": per_page})


@mcp.tool()
async def cancel_reservation(token: str, reservation_id: int) -> dict:
    """
    取消预约

    Args:
        token: 访问令牌
        reservation_id: 预约ID

    Returns:
        取消结果
    """
    return await _request("PUT", f"/reservations/{reservation_id}/cancel", token=token)


@mcp.tool()
async def get_all_reservations(token: str, page: int = 1, per_page: int = 20, status: str = None) -> dict:
    """
    获取所有预约列表（需要管理员权限）

    Args:
        token: 访问令牌（管理员）
        page: 页码（默认1）
        per_page: 每页数量（默认20）
        status: 筛选状态（pending/ready/cancelled/completed，可选）

    Returns:
        所有预约列表
    """
    params = {"page": page, "per_page": per_page}
    if status:
        params["status"] = status
    return await _request("GET", "/reservations/", token=token, params=params)


@mcp.tool()
async def mark_reservation_ready(token: str, reservation_id: int) -> dict:
    """
    标记预约就绪（管理员将书准备好，通知用户取书）

    Args:
        token: 访问令牌（管理员）
        reservation_id: 预约ID

    Returns:
        标记结果
    """
    return await _request("PUT", f"/reservations/{reservation_id}/ready", token=token)


@mcp.tool()
async def pickup_reservation(token: str, reservation_id: int) -> dict:
    """
    取书确认（管理员确认取书，自动转为借阅记录）

    Args:
        token: 访问令牌（管理员）
        reservation_id: 预约ID

    Returns:
        借阅记录
    """
    return await _request("PUT", f"/reservations/{reservation_id}/pickup", token=token)


# ==================== 统计模块 ====================

@mcp.tool()
async def get_overview(token: str) -> dict:
    """
    获取系统概览统计

    Args:
        token: 访问令牌

    Returns:
        系统统计数据（图书数、借阅数、用户数、逾期数等）
    """
    return await _request("GET", "/stats/overview", token=token)


@mcp.tool()
async def get_daily_trend(token: str) -> dict:
    """
    获取每日借阅/归还趋势（近30天）

    Args:
        token: 访问令牌

    Returns:
        近30天的借阅和归还趋势数据
    """
    return await _request("GET", "/stats/daily-trend", token=token)


@mcp.tool()
async def get_borrow_trend(token: str) -> dict:
    """
    获取借阅趋势（近30天，管理员）

    Args:
        token: 访问令牌（管理员）

    Returns:
        近30天借阅趋势
    """
    return await _request("GET", "/stats/borrow-trend", token=token)


@mcp.tool()
async def get_popular_books(token: str) -> dict:
    """
    获取热门图书（借阅次数TOP10，管理员）

    Args:
        token: 访问令牌（管理员）

    Returns:
        借阅次数最多的10本图书
    """
    return await _request("GET", "/stats/popular-books", token=token)


# ==================== 系统配置模块（管理员） ====================

@mcp.tool()
async def get_configs(token: str) -> dict:
    """
    获取所有系统配置

    Args:
        token: 访问令牌（管理员）

    Returns:
        系统配置列表
    """
    return await _request("GET", "/stats/config", token=token)


@mcp.tool()
async def create_config(token: str, config_key: str, config_value: str, description: str = None) -> dict:
    """
    新增系统配置

    Args:
        token: 访问令牌（管理员）
        config_key: 配置键
        config_value: 配置值
        description: 描述（可选）

    Returns:
        创建结果
    """
    data = {"config_key": config_key, "config_value": config_value}
    if description:
        data["description"] = description
    return await _request("POST", "/stats/config", token=token, json=data)


@mcp.tool()
async def update_config(token: str, config_id: int, config_key: str = None,
                        config_value: str = None, description: str = None) -> dict:
    """
    更新系统配置

    Args:
        token: 访问令牌（管理员）
        config_id: 配置ID
        config_key: 配置键（可选）
        config_value: 配置值（可选）
        description: 描述（可选）

    Returns:
        更新结果
    """
    data = {}
    if config_key:
        data["config_key"] = config_key
    if config_value:
        data["config_value"] = config_value
    if description:
        data["description"] = description
    return await _request("PUT", f"/stats/config/{config_id}", token=token, json=data)


@mcp.tool()
async def delete_config(token: str, config_id: int) -> dict:
    """
    删除系统配置

    Args:
        token: 访问令牌（管理员）
        config_id: 配置ID

    Returns:
        删除结果
    """
    return await _request("DELETE", f"/stats/config/{config_id}", token=token)


@mcp.tool()
async def init_default_configs(token: str) -> dict:
    """
    初始化默认系统配置

    Args:
        token: 访问令牌（管理员）

    Returns:
        初始化结果（创建的配置数量）
    """
    return await _request("POST", "/stats/config/init", token=token)


# ==================== 权限管理模块（管理员） ====================

@mcp.tool()
async def get_permissions(token: str) -> dict:
    """
    获取所有权限（按分组）

    Args:
        token: 访问令牌（管理员）

    Returns:
        权限列表（按分组组织）
    """
    return await _request("GET", "/permissions/", token=token)


@mcp.tool()
async def get_roles(token: str) -> dict:
    """
    获取所有角色

    Args:
        token: 访问令牌（管理员）

    Returns:
        角色列表
    """
    return await _request("GET", "/permissions/roles", token=token)


@mcp.tool()
async def get_role_detail(token: str, role_id: int) -> dict:
    """
    获取角色详情（含权限列表）

    Args:
        token: 访问令牌（管理员）
        role_id: 角色ID

    Returns:
        角色详情及关联权限
    """
    return await _request("GET", f"/permissions/roles/{role_id}", token=token)


@mcp.tool()
async def create_role(token: str, name: str, description: str = None, permission_ids: list = None) -> dict:
    """
    创建角色

    Args:
        token: 访问令牌（管理员）
        name: 角色名称
        description: 描述（可选）
        permission_ids: 权限ID列表（可选）

    Returns:
        创建结果
    """
    data = {"name": name}
    if description:
        data["description"] = description
    if permission_ids:
        data["permission_ids"] = permission_ids
    return await _request("POST", "/permissions/roles", token=token, json=data)


@mcp.tool()
async def update_role(token: str, role_id: int, name: str = None,
                      description: str = None, permission_ids: list = None) -> dict:
    """
    更新角色

    Args:
        token: 访问令牌（管理员）
        role_id: 角色ID
        name: 角色名称（可选）
        description: 描述（可选）
        permission_ids: 权限ID列表（可选）

    Returns:
        更新结果
    """
    data = {}
    if name:
        data["name"] = name
    if description:
        data["description"] = description
    if permission_ids:
        data["permission_ids"] = permission_ids
    return await _request("PUT", f"/permissions/roles/{role_id}", token=token, json=data)


@mcp.tool()
async def delete_role(token: str, role_id: int) -> dict:
    """
    删除角色

    Args:
        token: 访问令牌（管理员）
        role_id: 角色ID

    Returns:
        删除结果
    """
    return await _request("DELETE", f"/permissions/roles/{role_id}", token=token)


@mcp.tool()
async def get_user_roles(token: str, user_id: int) -> dict:
    """
    获取用户的角色列表

    Args:
        token: 访问令牌（管理员）
        user_id: 用户ID

    Returns:
        用户的角色列表
    """
    return await _request("GET", f"/permissions/users/{user_id}/roles", token=token)


@mcp.tool()
async def set_user_roles(token: str, user_id: int, role_ids: list) -> dict:
    """
    设置用户的角色

    Args:
        token: 访问令牌（管理员）
        user_id: 用户ID
        role_ids: 角色ID列表

    Returns:
        设置结果
    """
    return await _request("PUT", f"/permissions/users/{user_id}/roles", token=token,
                          json={"role_ids": role_ids})


@mcp.tool()
async def get_my_permissions(token: str) -> dict:
    """
    获取当前用户的权限代码列表

    Args:
        token: 访问令牌

    Returns:
        当前用户的权限代码列表
    """
    return await _request("GET", "/permissions/mine", token=token)


if __name__ == "__main__":
    mcp.run(transport="stdio")
