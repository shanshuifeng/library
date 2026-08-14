# MCP Server - 大学图书管理系统

将所有 REST API 接口暴露为 MCP 工具，供 AI 模型调用。

## 工具列表（46个）

### 认证模块
| 工具 | 说明 | 需要Token |
|------|------|----------|
| `login` | 用户登录，获取访问令牌 | 否 |
| `register` | 用户注册 | 否 |
| `get_profile` | 获取当前用户信息 | 是 |
| `update_profile` | 更新个人信息 | 是 |
| `change_password` | 修改密码 | 是 |

### 图书模块
| 工具 | 说明 | 需要Token |
|------|------|----------|
| `get_books` | 获取图书列表（分页+搜索） | 否 |
| `get_book` | 获取图书详情 | 否 |
| `create_book` | 新增图书 | 管理员 |
| `update_book` | 更新图书 | 管理员 |
| `delete_book` | 删除图书 | 管理员 |
| `get_categories` | 获取分类树 | 否 |
| `create_category` | 新增分类 | 管理员 |
| `get_stock_warning` | 获取库存预警图书 | 管理员 |

### 借阅模块
| 工具 | 说明 | 需要Token |
|------|------|----------|
| `borrow_book` | 借书 | 是 |
| `return_book` | 还书 | 是 |
| `renew_book` | 续借图书 | 是 |
| `get_borrow_list` | 获取借阅记录列表 | 是 |
| `get_user_borrows` | 获取指定用户借阅记录 | 是 |

### 用户管理模块
| 工具 | 说明 | 需要Token |
|------|------|----------|
| `get_users` | 获取用户列表 | 管理员 |
| `create_user` | 创建用户 | 管理员 |
| `update_user` | 更新用户 | 管理员 |
| `delete_user` | 删除用户 | 管理员 |

### 预约模块
| 工具 | 说明 | 需要Token |
|------|------|----------|
| `create_reservation` | 创建预约 | 是 |
| `get_my_reservations` | 获取我的预约 | 是 |
| `cancel_reservation` | 取消预约 | 是 |
| `get_all_reservations` | 获取所有预约 | 管理员 |
| `mark_reservation_ready` | 标记预约就绪 | 管理员 |
| `pickup_reservation` | 取书确认 | 管理员 |

### 统计模块
| 工具 | 说明 | 需要Token |
|------|------|----------|
| `get_overview` | 系统概览统计 | 是 |
| `get_daily_trend` | 每日借阅/归还趋势 | 是 |
| `get_borrow_trend` | 借阅趋势 | 管理员 |
| `get_popular_books` | 热门图书TOP10 | 管理员 |

### 系统配置模块
| 工具 | 说明 | 需要Token |
|------|------|----------|
| `get_configs` | 获取所有系统配置 | 管理员 |
| `create_config` | 新增系统配置 | 管理员 |
| `update_config` | 更新系统配置 | 管理员 |
| `delete_config` | 删除系统配置 | 管理员 |
| `init_default_configs` | 初始化默认配置 | 管理员 |

### 权限管理模块
| 工具 | 说明 | 需要Token |
|------|------|----------|
| `get_permissions` | 获取所有权限 | 管理员 |
| `get_roles` | 获取所有角色 | 管理员 |
| `get_role_detail` | 获取角色详情 | 管理员 |
| `create_role` | 创建角色 | 管理员 |
| `update_role` | 更新角色 | 管理员 |
| `delete_role` | 删除角色 | 管理员 |
| `get_user_roles` | 获取用户的角色 | 管理员 |
| `set_user_roles` | 设置用户的角色 | 管理员 |
| `get_my_permissions` | 获取当前用户权限 | 是 |

## 启动方式

### 1. 启动后端服务
```bash
cd backend
python run.py
```

### 2. 启动 MCP Server（stdio 模式）
```bash
cd backend
python mcp_server.py
```

### 3. 配置 MCP Client

将以下配置添加到你的 MCP 客户端配置文件中：

```json
{
  "mcpServers": {
    "book-manager": {
      "command": "python",
      "args": ["backend/mcp_server.py"],
      "cwd": "D:\\PyCharmProject\\book-manager",
      "env": {
        "API_BASE_URL": "http://localhost:5000/api/v1"
      }
    }
  }
}
```

## 使用示例

```
# AI 模型调用示例
1. 调用 login 获取 token
2. 使用 token 调用 get_books 搜索图书
3. 调用 borrow_book 借书
4. 调用 get_borrow_list 查看借阅记录
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `API_BASE_URL` | 后端 API 地址 | `http://localhost:5000/api/v1` |
