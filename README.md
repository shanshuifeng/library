# 📚 大学图书管理系统

基于 **Flask + Vue 3** 的前后端分离图书管理系统，支持多角色权限控制、图书借阅流程、数据统计等功能。

---

## 📋 功能概览

### 管理员
- 用户管理（增删改查、角色分配、状态控制）
- 图书管理（增删改查、封面上传、库存预警）
- 分类管理（多级分类树、增删改）
- 借阅管理（借书、还书、续借、逾期罚款）
- 系统配置（运行时参数管理）
- 统计报表（系统概览、借阅趋势、热门图书）

### 教师 / 学生
- 图书检索（多条件搜索、分类筛选）
- 图书详情查看
- 借阅操作与记录查询
- 个人中心（信息修改、密码修改、续借）
- 借阅历史查看

---

## 🛠️ 技术栈

| 层级 | 技术 | 版本  |
|------|------|-------|
| 后端框架 | Flask | 3.x   |
| ORM | Flask-SQLAlchemy | 3.x   |
| 数据库迁移 | Flask-Migrate | 4.x   |
| 认证 | Flask-JWT-Extended | 4.x   |
| 跨域 | Flask-CORS | 4.x   |
| 数据校验 | Marshmallow | 3.x   |
| 数据库 | postgresql | 42.7+ |
| 前端框架 | Vue | 3.x   |
| UI 组件库 | Element Plus | 2.x   |
| 构建工具 | Vite | 8.x   |
| 状态管理 | Pinia | 4.x   |
| 路由 | Vue Router | 5.x   |
| HTTP 请求 | Axios | 1.x   |

---

## 📁 项目结构

```
book-manager/
├── backend/                        # 后端项目
│   ├── app/
│   │   ├── __init__.py             # Flask 应用工厂
│   │   ├── config.py               # 配置管理（开发/生产/测试）
│   │   ├── extensions.py           # 扩展初始化
│   │   ├── models/                 # 数据模型
│   │   │   ├── user.py             # 用户模型
│   │   │   ├── book.py             # 图书模型
│   │   │   ├── category.py         # 分类模型
│   │   │   ├── borrow.py           # 借阅记录模型
│   │   │   └── system_config.py    # 系统配置模型
│   │   ├── schemas/                # 数据校验与序列化
│   │   │   ├── user.py             # 用户 Schema
│   │   │   ├── book.py             # 图书 Schema
│   │   │   └── borrow.py           # 借阅 Schema
│   │   ├── routes/                 # 路由蓝图
│   │   │   ├── auth.py             # 认证路由
│   │   │   ├── book.py             # 图书路由
│   │   │   ├── borrow.py           # 借阅路由
│   │   │   ├── user.py             # 用户管理路由
│   │   │   └── stats.py            # 统计与系统配置路由
│   │   ├── services/               # 业务逻辑层
│   │   │   ├── auth_service.py     # 认证服务
│   │   │   ├── book_service.py     # 图书服务
│   │   │   ├── borrow_service.py   # 借阅服务
│   │   │   └── system_config_service.py  # 系统配置服务
│   │   └── utils/                  # 工具函数
│   │       ├── auth.py             # 权限装饰器
│   │       ├── response.py         # 统一响应格式
│   │       ├── validators.py       # 自定义校验器
│   │       └── logger.py           # 结构化日志
│   ├── tests/                      # 单元测试
│   ├── .env                        # 环境变量
│   ├── .env.example                # 环境变量示例
│   └── run.py                      # 启动入口 + CLI 命令
│
├── pyproject.toml                  # Python 依赖（uv 管理）
├── uv.lock                         # 依赖锁定文件
├── frontend/                       # 前端项目
│   ├── src/
│   │   ├── api/                    # API 请求封装
│   │   ├── layouts/                # 布局组件
│   │   ├── router/                 # 路由配置
│   │   ├── store/                  # Pinia 状态管理
│   │   ├── views/                  # 页面组件
│   │   │   ├── auth/               # 登录/注册
│   │   │   ├── dashboard/          # 首页概览
│   │   │   ├── book/               # 图书查询/详情
│   │   │   ├── borrow/             # 借阅管理
│   │   │   ├── admin/              # 管理后台
│   │   │   ├── profile/            # 个人中心
│   │   │   └── error/              # 错误页面
│   │   ├── utils/                  # 工具函数
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js              # Vite 配置（含 API 代理）
│
├── agents/                         # Agent 提示词配置
├── workflows/                      # 工作流定义
├── 大学图书管理系统-项目提示词.md     # 项目总需求文档
└── README.md
```

---

## 🚀 快速启动

### 环境要求

- **Python** 3.10+
- **Node.js** 18+
- **postgresql** 42.7+
- **uv**（推荐）或 pip

---

### 1️⃣ 数据库准备

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE book_manager DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

### 2️⃣ 后端启动

```bash
# 在项目根目录执行（pyproject.toml 位于根目录）
# 创建虚拟环境并安装依赖
uv sync

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，修改数据库连接信息和密钥
# DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/book_manager

# 初始化数据库（创建表 + 默认配置）
flask init-db

# 创建管理员账号
flask create-admin

# （可选）填充示例数据
flask seed-data

# 启动后端服务
python run.py
```

后端服务运行在 `http://localhost:5000`

---

### 3️⃣ 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务运行在 `http://localhost:5173`，会自动打开浏览器。

> Vite 已配置开发代理，`/api` 请求会自动转发到后端 `http://localhost:5000`。

---

### 4️⃣ 构建生产版本

```bash
# 前端构建
cd frontend
npm run build

# 构建产物在 frontend/dist/ 目录
```

---

## 示例
![img.png](img.png)
![img_1.png](img_1.png)
![img_2.png](img_2.png)
![img_3.png](img_3.png)
## 🔌 API 接口

### 基础路径

```
/api/v1
```

### 统一响应格式

```json
{
  "code": 200,
  "message": "成功",
  "data": {}
}
```

### 接口列表

| 模块 | 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|------|
| **认证** | POST | /auth/login | 登录 | 公开 |
| | POST | /auth/register | 注册 | 公开 |
| | POST | /auth/logout | 退出 | 登录 |
| | GET | /auth/profile | 获取当前用户信息 | 登录 |
| | PUT | /auth/profile | 更新个人信息 | 登录 |
| | PUT | /auth/password | 修改密码 | 登录 |
| | POST | /auth/refresh | 刷新 Token | Refresh Token |
| **图书** | GET | /books/ | 图书列表（分页+搜索） | 公开 |
| | GET | /books/:id | 图书详情 | 公开 |
| | POST | /books/ | 新增图书 | 管理员 |
| | PUT | /books/:id | 更新图书 | 管理员 |
| | DELETE | /books/:id | 删除图书 | 管理员 |
| | GET | /books/categories | 获取分类树 | 公开 |
| | POST | /books/categories | 新增分类 | 管理员 |
| | PUT | /books/categories/:id | 更新分类 | 管理员 |
| | DELETE | /books/categories/:id | 删除分类 | 管理员 |
| | GET | /books/stock-warning | 库存预警图书 | 管理员 |
| | POST | /books/upload-cover | 上传封面图片 | 管理员 |
| **借阅** | POST | /borrows/ | 借书 | 登录 |
| | PUT | /borrows/:id/return | 还书 | 登录 |
| | PUT | /borrows/:id/renew | 续借 | 登录 |
| | GET | /borrows/ | 借阅记录列表 | 登录 |
| | GET | /borrows/user/:id | 指定用户借阅记录 | 登录 |
| **用户** | GET | /users/ | 用户列表 | 管理员 |
| | POST | /users/ | 创建用户 | 管理员 |
| | PUT | /users/:id | 更新用户 | 管理员 |
| | DELETE | /users/:id | 删除用户 | 管理员 |
| **统计** | GET | /stats/overview | 系统概览 | 管理员 |
| | GET | /stats/borrow-trend | 借阅趋势 | 管理员 |
| | GET | /stats/popular-books | 热门图书 | 管理员 |
| | GET | /stats/config | 获取系统配置 | 管理员 |
| | POST | /stats/config | 新增配置 | 管理员 |
| | PUT | /stats/config/:id | 更新配置 | 管理员 |
| | DELETE | /stats/config/:id | 删除配置 | 管理员 |
| | POST | /stats/config/init | 初始化默认配置 | 管理员 |

---

## 📊 业务规则

### 借阅规则

| 角色 | 最大借阅数 | 借阅天数 | 最大续借次数 | 续借天数 |
|------|-----------|---------|------------|---------|
| 学生 | 5 本 | 30 天 | 2 次 | 15 天 |
| 教师 | 10 本 | 30 天 | 2 次 | 15 天 |
| 管理员 | 20 本 | 30 天 | 2 次 | 15 天 |

### 罚款规则

- 逾期罚款：**0.1 元/天**
- 逾期未还不能续借
- 罚款未缴不能借书

### 其他规则

- 同一本书不能重复借阅（需先归还）
- 有借阅记录的用户不能删除
- 有图书的分类不能删除
- 有子分类的分类不能删除

> 以上参数均可在系统配置中运行时修改。

---

## 🧪 运行测试

```bash
cd backend

# 激活虚拟环境
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# 运行全部测试
pytest

# 运行指定模块测试
pytest tests/test_auth.py
pytest tests/test_book.py
pytest tests/test_borrow.py

# 显示详细输出
pytest -v

# 查看测试覆盖率
pytest --cov=app
```

> 测试使用 SQLite 内存数据库，无需配置数据库。

---

## 📝 开发规范

### Git 提交规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

### 代码规范

- 后端遵循 **PEP 8**，使用类型注解，函数/类必须有 docstring
- 前端遵循 **Vue 3 风格指南**，使用 Composition API（setup 语法糖）
- 中文注释

---

## 📄 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| FLASK_ENV | 运行环境 | development |
| FLASK_HOST | 监听地址 | 0.0.0.0 |
| FLASK_PORT | 监听端口 | 5000 |
| SECRET_KEY | Flask 密钥 | - |
| JWT_SECRET_KEY | JWT 密钥 | - |
| DATABASE_URL | 数据库连接串 | postgresql+psycopg://root:password@localhost:5432/book_manager |
| CORS_ORIGINS | 允许的跨域来源 | http://localhost:5173,http://localhost:3000 |

---

## 📚 参考资料

- [Flask 官方文档](https://flask.palletsprojects.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Flask-JWT-Extended 文档](https://flask-jwt-extended.readthedocs.io/)
- [Marshmallow 文档](https://marshmallow.readthedocs.io/)
- [Vue 3 官方文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [Vite 文档](https://vite.dev/)
