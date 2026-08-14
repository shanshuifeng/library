# MCP Server 使用说明

## 快速开始

### 1. 启动后端服务
```bash
cd backend
python run.py
```

### 2. 测试 MCP Server
```bash
cd backend
python mcp_client_test.py
```

### 3. 在 AI 客户端中使用

将以下配置添加到你的 MCP 客户端（如 Claude Desktop、Cursor 等）：

```json
{
  "mcpServers": {
    "book-manager": {
      "command": "python",
      "args": ["D:\\PyCharmProject\\book-manager\\backend\\mcp_server.py"],
      "env": {
        "API_BASE_URL": "http://localhost:5000/api/v1"
      }
    }
  }
}
```

## 工具调用示例

### 登录获取 Token
```
调用工具: login
参数: {"username": "admin", "password": "admin123"}
```

### 搜索图书
```
调用工具: get_books
参数: {"token": "<your_token>", "keyword": "Python", "page": 1, "per_page": 10}
```

### 借书
```
调用工具: borrow_book
参数: {"token": "<your_token>", "book_id": 1}
```

### 查看借阅记录
```
调用工具: get_borrow_list
参数: {"token": "<your_token>", "page": 1}
```

### 系统概览（管理员）
```
调用工具: get_overview
参数: {"token": "<admin_token>"}
```

## 完整工具列表（46个）

### 认证（5个）
- `login` - 用户登录
- `register` - 用户注册
- `get_profile` - 获取个人信息
- `update_profile` - 更新个人信息
- `change_password` - 修改密码

### 图书（8个）
- `get_books` - 获取图书列表
- `get_book` - 获取图书详情
- `create_book` - 新增图书（管理员）
- `update_book` - 更新图书（管理员）
- `delete_book` - 删除图书（管理员）
- `get_categories` - 获取分类树
- `create_category` - 新增分类（管理员）
- `get_stock_warning` - 库存预警（管理员）

### 借阅（5个）
- `borrow_book` - 借书
- `return_book` - 还书
- `renew_book` - 续借
- `get_borrow_list` - 借阅记录列表
- `get_user_borrows` - 用户借阅记录

### 用户管理（4个）
- `get_users` - 用户列表（管理员）
- `create_user` - 创建用户（管理员）
- `update_user` - 更新用户（管理员）
- `delete_user` - 删除用户（管理员）

### 预约（6个）
- `create_reservation` - 创建预约
- `get_my_reservations` - 我的预约
- `cancel_reservation` - 取消预约
- `get_all_reservations` - 所有预约（管理员）
- `mark_reservation_ready` - 标记就绪（管理员）
- `pickup_reservation` - 取书确认（管理员）

### 统计（4个）
- `get_overview` - 系统概览
- `get_daily_trend` - 每日趋势
- `get_borrow_trend` - 借阅趋势（管理员）
- `get_popular_books` - 热门图书（管理员）

### 配置（5个）
- `get_configs` - 系统配置（管理员）
- `create_config` - 新增配置（管理员）
- `update_config` - 更新配置（管理员）
- `delete_config` - 删除配置（管理员）
- `init_default_configs` - 初始化默认配置（管理员）

### 权限（9个）
- `get_permissions` - 权限列表（管理员）
- `get_roles` - 角色列表（管理员）
- `get_role_detail` - 角色详情（管理员）
- `create_role` - 创建角色（管理员）
- `update_role` - 更新角色（管理员）
- `delete_role` - 删除角色（管理员）
- `get_user_roles` - 用户角色（管理员）
- `set_user_roles` - 设置用户角色（管理员）
- `get_my_permissions` - 我的权限

## 注意事项

1. 除登录和注册外，所有接口都需要 token
2. 管理员接口需要 admin 角色
3. Token 有效期为 1 小时
4. 确保后端服务已启动（默认端口 5000）
