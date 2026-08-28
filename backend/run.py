"""
应用启动入口
"""
import os
from dotenv import load_dotenv

# 使用绝对路径加载 .env，确保不受工作目录影响
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

from app import create_app, db
from app.models import User, Book, Category, BorrowRecord, SystemConfig, Reservation, Permission, Role, AuditLog, AccessLog

# 创建应用实例
app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.cli.command('init-db')
def init_db():
    """初始化数据库：创建所有表并插入默认数据"""
    db.create_all()

    # 初始化默认系统配置
    from app.services.system_config_service import init_default_configs
    created = init_default_configs()
    print(f'✅ 数据库初始化完成，创建了 {created} 项默认配置')


@app.cli.command('create-admin')
def create_admin():
    """创建管理员账号"""
    import getpass
    username = input('请输入管理员用户名: ').strip()
    if not username:
        print('❌ 用户名不能为空')
        return

    if User.query.filter_by(username=username).first():
        print('❌ 用户名已存在')
        return

    password = getpass.getpass('请输入管理员密码: ')
    if len(password) < 6:
        print('❌ 密码长度不能少于6位')
        return

    admin = User(
        username=username,
        role='admin',
        status=1
    )
    admin.set_password(password)

    db.session.add(admin)
    db.session.commit()
    print(f'✅ 管理员账号 {username} 创建成功')


@app.cli.command('seed-data')
def seed_data():
    """填充丰富的示例数据（开发用）"""
    from random import SystemRandom as _SecureRandom; random = _SecureRandom()
    from datetime import date, timedelta
    from app.utils.logger import get_logger
    logger = get_logger()

    # ==================== 1. 创建分类 ====================
    root_categories = [
        {'name': '文学', 'description': '文学类图书'},
        {'name': '计算机', 'description': '计算机类图书'},
        {'name': '经济', 'description': '经济类图书'},
        {'name': '理学', 'description': '自然科学类图书'},
        {'name': '历史', 'description': '历史类图书'},
    ]
    child_categories = [
        {'name': '小说', 'parent_name': '文学'},
        {'name': '诗歌', 'parent_name': '文学'},
        {'name': '编程语言', 'parent_name': '计算机'},
        {'name': '数据库', 'parent_name': '计算机'},
        {'name': '算法', 'parent_name': '计算机'},
    ]

    cat_map = {}
    for cd in root_categories:
        existing = Category.query.filter_by(name=cd['name']).first()
        if not existing:
            cat = Category(name=cd['name'], parent_id=None, level=1, description=cd.get('description'))
            db.session.add(cat); db.session.flush()
            cat_map[cd['name']] = cat.id
        else:
            cat_map[cd['name']] = existing.id
    db.session.commit()

    for cd in child_categories:
        existing = Category.query.filter_by(name=cd['name']).first()
        if not existing:
            pid = cat_map.get(cd['parent_name'])
            cat = Category(name=cd['name'], parent_id=pid, level=2)
            db.session.add(cat); db.session.flush()
            cat_map[cd['name']] = cat.id
        else:
            cat_map[cd['name']] = existing.id
    db.session.commit()
    print('✅ 分类创建完成')

    # ==================== 2. 创建图书（25本） ====================
    books_data = [
        # 小说
        {'title': '三国演义', 'author': '罗贯中', 'isbn': '9787020008704', 'publisher': '人民文学出版社',
         'category_id': cat_map.get('小说'), 'stock': 10, 'total_stock': 10, 'price': 39.50, 'location': 'A区-1楼-01架'},
        {'title': '红楼梦', 'author': '曹雪芹', 'isbn': '9787020002207', 'publisher': '人民文学出版社',
         'category_id': cat_map.get('小说'), 'stock': 8, 'total_stock': 8, 'price': 59.70, 'location': 'A区-1楼-01架'},
        {'title': '百年孤独', 'author': '加西亚·马尔克斯', 'isbn': '9787544253994', 'publisher': '南海出版公司',
         'category_id': cat_map.get('小说'), 'stock': 5, 'total_stock': 5, 'price': 39.50, 'location': 'A区-1楼-02架'},
        {'title': '活着', 'author': '余华', 'isbn': '9787506365437', 'publisher': '作家出版社',
         'category_id': cat_map.get('小说'), 'stock': 7, 'total_stock': 7, 'price': 28.00, 'location': 'A区-1楼-02架'},
        {'title': '三体', 'author': '刘慈欣', 'isbn': '9787536692930', 'publisher': '重庆出版社',
         'category_id': cat_map.get('小说'), 'stock': 12, 'total_stock': 12, 'price': 93.00, 'location': 'A区-1楼-03架'},
        # 计算机
        {'title': 'Python编程：从入门到实践', 'author': 'Eric Matthes', 'isbn': '9787115428028', 'publisher': '人民邮电出版社',
         'category_id': cat_map.get('编程语言'), 'stock': 10, 'total_stock': 12, 'price': 89.00, 'location': 'B区-2楼-01架'},
        {'title': '流畅的Python', 'author': 'Luciano Ramalho', 'isbn': '9787115546082', 'publisher': '人民邮电出版社',
         'category_id': cat_map.get('编程语言'), 'stock': 6, 'total_stock': 8, 'price': 139.00, 'location': 'B区-2楼-01架'},
        {'title': 'JavaScript高级程序设计', 'author': 'Matt Frisbie', 'isbn': '9787115545382', 'publisher': '人民邮电出版社',
         'category_id': cat_map.get('编程语言'), 'stock': 4, 'total_stock': 6, 'price': 129.00, 'location': 'B区-2楼-02架'},
        {'title': 'Flask Web开发实战', 'author': '李辉', 'isbn': '9787115499548', 'publisher': '人民邮电出版社',
         'category_id': cat_map.get('编程语言'), 'stock': 5, 'total_stock': 5, 'price': 79.00, 'location': 'B区-2楼-02架'},
        {'title': 'Vue.js实战', 'author': '梁灏', 'isbn': '9787121335200', 'publisher': '电子工业出版社',
         'category_id': cat_map.get('编程语言'), 'stock': 3, 'total_stock': 5, 'price': 79.00, 'location': 'B区-2楼-03架'},
        # 数据库
        {'title': 'SQL必知必会', 'author': 'Ben Forta', 'isbn': '9787115538506', 'publisher': '人民邮电出版社',
         'category_id': cat_map.get('数据库'), 'stock': 8, 'total_stock': 10, 'price': 49.00, 'location': 'B区-2楼-04架'},
        {'title': '高性能MySQL', 'author': 'Baron Schwartz', 'isbn': '9787121130782', 'publisher': '电子工业出版社',
         'category_id': cat_map.get('数据库'), 'stock': 4, 'total_stock': 6, 'price': 128.00, 'location': 'B区-2楼-04架'},
        {'title': '数据库系统概论', 'author': '王珊', 'isbn': '9787040406641', 'publisher': '高等教育出版社',
         'category_id': cat_map.get('数据库'), 'stock': 15, 'total_stock': 15, 'price': 49.00, 'location': 'B区-2楼-05架'},
        # 算法
        {'title': '算法导论', 'author': 'Thomas H. Cormen', 'isbn': '9787111407010', 'publisher': '机械工业出版社',
         'category_id': cat_map.get('算法'), 'stock': 6, 'total_stock': 8, 'price': 128.00, 'location': 'B区-2楼-05架'},
        {'title': '数据结构与算法分析', 'author': 'Mark Allen Weiss', 'isbn': '9787111539244', 'publisher': '机械工业出版社',
         'category_id': cat_map.get('算法'), 'stock': 5, 'total_stock': 5, 'price': 79.00, 'location': 'B区-2楼-06架'},
        # 经济
        {'title': '经济学原理（微观）', 'author': '曼昆', 'isbn': '9787301171464', 'publisher': '北京大学出版社',
         'category_id': cat_map.get('经济'), 'stock': 15, 'total_stock': 18, 'price': 98.00, 'location': 'C区-1楼-01架'},
        {'title': '经济学原理（宏观）', 'author': '曼昆', 'isbn': '9787301171471', 'publisher': '北京大学出版社',
         'category_id': cat_map.get('经济'), 'stock': 12, 'total_stock': 15, 'price': 98.00, 'location': 'C区-1楼-01架'},
        {'title': '国富论', 'author': '亚当·斯密', 'isbn': '9787100017800', 'publisher': '商务印书馆',
         'category_id': cat_map.get('经济'), 'stock': 6, 'total_stock': 6, 'price': 75.00, 'location': 'C区-1楼-02架'},
        {'title': '穷查理宝典', 'author': '彼得·考夫曼', 'isbn': '9787508663322', 'publisher': '中信出版社',
         'category_id': cat_map.get('经济'), 'stock': 10, 'total_stock': 10, 'price': 168.00, 'location': 'C区-1楼-02架'},
        # 历史
        {'title': '人类简史', 'author': '尤瓦尔·赫拉利', 'isbn': '9787508660758', 'publisher': '中信出版社',
         'category_id': cat_map.get('历史'), 'stock': 9, 'total_stock': 10, 'price': 68.00, 'location': 'A区-2楼-01架'},
        {'title': '万历十五年', 'author': '黄仁宇', 'isbn': '9787108009821', 'publisher': '中华书局',
         'category_id': cat_map.get('历史'), 'stock': 7, 'total_stock': 7, 'price': 36.00, 'location': 'A区-2楼-01架'},
        {'title': '明朝那些事儿', 'author': '当年明月', 'isbn': '9787213040146', 'publisher': '浙江人民出版社',
         'category_id': cat_map.get('历史'), 'stock': 20, 'total_stock': 20, 'price': 198.00, 'location': 'A区-2楼-02架'},
    ]
    book_objs = {}
    for bd in books_data:
        existing = Book.query.filter_by(isbn=bd['isbn']).first()
        if not existing:
            book = Book(**bd)
            db.session.add(book)
            db.session.flush()
            book_objs[bd['isbn']] = book
        else:
            book_objs[bd['isbn']] = existing
    db.session.commit()
    print(f'✅ 图书创建完成（{len(books_data)}本）')

    # ==================== 3. 创建用户 ====================
    all_users_data = [
        {'username': 'admin', 'password': 'admin123', 'role': 'admin', 'real_name': '管理员'},
        {'username': 'student1', 'password': '123456', 'role': 'student', 'real_name': '张三', 'student_id': '2021001'},
        {'username': 'student2', 'password': '123456', 'role': 'student', 'real_name': '李四', 'student_id': '2021002'},
        {'username': 'student3', 'password': '123456', 'role': 'student', 'real_name': '王五', 'student_id': '2021003'},
        {'username': 'student4', 'password': '123456', 'role': 'student', 'real_name': '赵六', 'student_id': '2021004'},
        {'username': 'student5', 'password': '123456', 'role': 'student', 'real_name': '陈七', 'student_id': '2021005'},
        {'username': 'teacher1', 'password': '123456', 'role': 'teacher', 'real_name': '李老师', 'student_id': 'T001'},
        {'username': 'teacher2', 'password': '123456', 'role': 'teacher', 'real_name': '王教授', 'student_id': 'T002'},
    ]
    user_objs = {}
    for ud in all_users_data:
        existing = User.query.filter_by(username=ud['username']).first()
        if not existing:
            pwd = ud.pop('password')
            user = User(**ud, status=1)
            user.set_password(pwd)
            db.session.add(user); db.session.flush()
            user_objs[ud['username']] = user
        else:
            user_objs[ud['username']] = existing
    db.session.commit()
    print(f'✅ 用户创建完成（{len(all_users_data)}个）')

    # ==================== 4. 创建借阅记录 ====================
    today = date.today()
    # 清空已有借阅记录避免重复
    if BorrowRecord.query.first() is None:
        students = [u for u in user_objs.values() if u.role == 'student']
        all_books = list(book_objs.values())
        borrow_records = []

        for i in range(60):  # 生成60条借阅记录
            student = random.choice(students)
            book = random.choice(all_books)
            days_ago = random.randint(1, 35)
            borrow_date = today - timedelta(days=days_ago)
            borrow_days = random.choice([15, 30])
            due_date = borrow_date + timedelta(days=borrow_days)

            # 随机决定状态
            r = random.random()
            if r < 0.45:  # 45% 已归还
                return_date = due_date - timedelta(days=random.randint(0, 5))
                status = 'returned'
                fine = 0
            elif r < 0.75:  # 30% 借阅中
                return_date = None
                status = 'borrowed'
                fine = 0
            else:  # 25% 逾期
                return_date = None
                status = 'borrowed' if borrow_date <= today else 'borrowed'
                fine = 0

            # 避免重复借阅同本书
            existing_record = BorrowRecord.query.filter_by(
                user_id=student.id, book_id=book.id, status='borrowed'
            ).first()
            if existing_record:
                continue

            record = BorrowRecord(
                user_id=student.id,
                book_id=book.id,
                borrow_date=borrow_date,
                due_date=due_date,
                return_date=return_date,
                renew_count=0,
                fine=fine,
                status=status
            )
            db.session.add(record)
            # 更新图书库存
            if status == 'returned':
                pass  # 库存已恢复
            else:
                if book.stock > 0:
                    book.stock -= 1
            borrow_records.append(record)

        db.session.commit()
        print(f'✅ 借阅记录创建完成（{len(borrow_records)}条）')
    else:
        print('⏭️  借阅记录已存在，跳过')

    logger.info('示例数据填充完成')
    print('🎉 ✅ 所有示例数据填充完成！')


@app.cli.command('seed-permissions')
def seed_permissions():
    """初始化权限和角色"""
    # ===== 定义所有权限 =====
    all_permissions = [
        # 图书管理
        {'code': 'book:list', 'name': '查询图书', 'group': '图书管理'},
        {'code': 'book:view', 'name': '查看详情', 'group': '图书管理'},
        {'code': 'book:create', 'name': '新增图书', 'group': '图书管理'},
        {'code': 'book:update', 'name': '编辑图书', 'group': '图书管理'},
        {'code': 'book:delete', 'name': '删除图书', 'group': '图书管理'},
        {'code': 'book:upload-cover', 'name': '上传封面', 'group': '图书管理'},
        # 分类管理
        {'code': 'category:list', 'name': '查询分类', 'group': '分类管理'},
        {'code': 'category:create', 'name': '新增分类', 'group': '分类管理'},
        {'code': 'category:update', 'name': '编辑分类', 'group': '分类管理'},
        {'code': 'category:delete', 'name': '删除分类', 'group': '分类管理'},
        # 借阅管理
        {'code': 'borrow:create', 'name': '借书', 'group': '借阅管理'},
        {'code': 'borrow:return', 'name': '还书', 'group': '借阅管理'},
        {'code': 'borrow:renew', 'name': '续借', 'group': '借阅管理'},
        {'code': 'borrow:list', 'name': '查看借阅记录', 'group': '借阅管理'},
        {'code': 'borrow:list-all', 'name': '查看所有借阅', 'group': '借阅管理'},
        # 用户管理
        {'code': 'user:list', 'name': '查看用户', 'group': '用户管理'},
        {'code': 'user:create', 'name': '新增用户', 'group': '用户管理'},
        {'code': 'user:update', 'name': '编辑用户', 'group': '用户管理'},
        {'code': 'user:delete', 'name': '删除用户', 'group': '用户管理'},
        # 预约管理
        {'code': 'reservation:create', 'name': '创建预约', 'group': '预约管理'},
        {'code': 'reservation:list-my', 'name': '我的预约', 'group': '预约管理'},
        {'code': 'reservation:list-all', 'name': '查看所有预约', 'group': '预约管理'},
        {'code': 'reservation:manage', 'name': '处理预约', 'group': '预约管理'},
        # 统计分析
        {'code': 'stats:overview', 'name': '首页概览', 'group': '统计分析'},
        {'code': 'stats:trend', 'name': '查看趋势', 'group': '统计分析'},
        # 系统管理
        {'code': 'system:config', 'name': '系统配置', 'group': '系统管理'},
        {'code': 'system:role-manage', 'name': '角色管理', 'group': '系统管理'},
    ]

    # 创建权限（已存在则跳过）
    perm_map = {}
    for pd in all_permissions:
        existing = Permission.query.filter_by(code=pd['code']).first()
        if not existing:
            p = Permission(**pd)
            db.session.add(p)
            db.session.flush()
            perm_map[pd['code']] = p
        else:
            perm_map[pd['code']] = existing
    db.session.commit()
    print(f'✅ 权限创建完成（{len(all_permissions)}个）')

    # ===== 创建默认角色 =====
    roles_data = [
        {
            'name': 'admin', 'is_system': True, 'description': '系统管理员，拥有所有权限',
            'permissions': [p.code for p in Permission.query.all()]
        },
        {
            'name': 'teacher', 'is_system': True, 'description': '教师，可借阅、查看信息',
            'permissions': [
                'book:list', 'book:view', 'category:list',
                'borrow:create', 'borrow:return', 'borrow:renew', 'borrow:list',
                'stats:overview', 'stats:trend',
                'reservation:create', 'reservation:list-my',
            ]
        },
        {
            'name': 'student', 'is_system': True, 'description': '学生，可借阅、预约',
            'permissions': [
                'book:list', 'book:view', 'category:list',
                'borrow:create', 'borrow:list',
                'stats:overview', 'stats:trend',
                'reservation:create', 'reservation:list-my',
            ]
        },
    ]
    role_objs = {}
    for rd in roles_data:
        existing = Role.query.filter_by(name=rd['name']).first()
        if not existing:
            role = Role(name=rd['name'], description=rd['description'], is_system=rd['is_system'])
            perms = [perm_map[c] for c in rd['permissions'] if c in perm_map]
            role.permissions = perms
            db.session.add(role)
            db.session.flush()
            role_objs[rd['name']] = role
        else:
            # 更新已有角色的权限
            perms = [perm_map[c] for c in rd['permissions'] if c in perm_map]
            existing.permissions = perms
            role_objs[rd['name']] = existing
    db.session.commit()
    print(f'✅ 角色创建完成（{len(roles_data)}个）')

    # ===== 为已有用户分配默认角色 =====
    admin_role = role_objs.get('admin') or Role.query.filter_by(name='admin').first()
    student_role = role_objs.get('student') or Role.query.filter_by(name='student').first()
    teacher_role = role_objs.get('teacher') or Role.query.filter_by(name='teacher').first()

    for user in User.query.all():
        if user.role == 'admin' and admin_role and admin_role not in user.roles.all():
            user.roles.append(admin_role)
        elif user.role == 'teacher' and teacher_role and teacher_role not in user.roles.all():
            user.roles.append(teacher_role)
        elif user.role == 'student' and student_role and student_role not in user.roles.all():
            user.roles.append(student_role)
    db.session.commit()
    print('✅ 用户角色分配完成')
    print('🎉 权限系统初始化完成！')


if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )
