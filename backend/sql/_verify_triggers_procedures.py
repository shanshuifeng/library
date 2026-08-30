"""
验证触发器、存储过程、工具函数是否正常工作
所有写操作都在事务中执行并回滚，不影响真实数据
"""
import psycopg

conn = psycopg.connect(
    'host=192.168.116.141 port=5432 dbname=book_manager '
    'user=remote_user password=NewPassword@123 sslmode=prefer'
)
cur = conn.cursor()

print('=' * 60)
print('一、对象清单验证')
print('=' * 60)

cur.execute("""
    SELECT proname, prokind FROM pg_proc
     WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
       AND proname IN ('fn_calculate_overdue_fine', 'fn_get_user_active_borrows',
                       'fn_get_available_stock', 'fn_get_reservation_position',
                       'fn_get_borrow_limit', 'sp_borrow_book', 'sp_return_book',
                       'sp_renew_book', 'sp_batch_process_overdue',
                       'sp_cleanup_expired_reservations')
     ORDER BY proname
""")
for name, kind in cur.fetchall():
    print(f'  [{"过程" if kind == "p" else "函数"}] {name}')

cur.execute("""
    SELECT trigger_name, event_object_table FROM information_schema.triggers
     WHERE trigger_schema = 'public' ORDER BY event_object_table, trigger_name
""")
print()
for name, table in cur.fetchall():
    print(f'  [触发器] {name} ON {table}')

print()
print('=' * 60)
print('二、工具函数测试')
print('=' * 60)

cur.execute("SELECT fn_get_borrow_limit('student'), fn_get_borrow_limit('teacher'), fn_get_borrow_limit('admin')")
r = cur.fetchone()
print(f'  fn_get_borrow_limit: student={r[0]}, teacher={r[1]}, admin={r[2]}')

cur.execute("SELECT fn_calculate_overdue_fine(DATE '2026-07-01', DATE '2026-07-15')")
print(f'  fn_calculate_overdue_fine(逾期14天): {cur.fetchone()[0]} 元')

cur.execute("SELECT fn_calculate_overdue_fine(DATE '2026-08-01', DATE '2026-07-15')")
print(f'  fn_calculate_overdue_fine(未逾期):   {cur.fetchone()[0]} 元')

cur.execute("SELECT id, title, stock FROM books ORDER BY id LIMIT 1")
book = cur.fetchone()
print(f'  测试用书: id={book[0]} 《{book[1]}》 stock={book[2]}')
cur.execute('SELECT fn_get_available_stock(%s)', (book[0],))
print(f'  fn_get_available_stock({book[0]}): {cur.fetchone()[0]}')

cur.execute("SELECT id, username, role FROM users WHERE status=1 ORDER BY id LIMIT 1")
user = cur.fetchone()
print(f'  测试用户: id={user[0]} {user[1]} ({user[2]})')
cur.execute('SELECT fn_get_user_active_borrows(%s)', (user[0],))
print(f'  fn_get_user_active_borrows({user[0]}): {cur.fetchone()[0]}')

cur.execute('SELECT fn_get_reservation_position(%s, %s)', (user[0], book[0]))
print(f'  fn_get_reservation_position: {cur.fetchone()[0]}')

print()
print('=' * 60)
print('三、存储过程测试（事务内执行，最后回滚）')
print('=' * 60)

# --- 3.1 借阅测试 ---
try:
    cur.execute('CALL sp_borrow_book(%s, %s, NULL, NULL, NULL, NULL, NULL)',
                (user[0], book[0]))
    r = cur.fetchone()
    print(f'  sp_borrow_book: code={r[3]}, msg={r[2]}, 记录ID={r[0]}, 应还={r[1]}')
except Exception as e:
    print(f'  sp_borrow_book 异常: {e}')
    conn.rollback()
    cur = conn.cursor()

# 验证触发器是否生效（库存应已扣减，但会回滚）
cur.execute('SELECT stock FROM books WHERE id = %s', (book[0],))
print(f'  借阅后库存(触发器效果): {cur.fetchone()[0]} (原 {book[2]})')

# --- 重复借阅应被触发器拦截 ---
try:
    cur.execute('CALL sp_borrow_book(%s, %s, NULL, NULL, NULL, NULL, NULL)',
                (user[0], book[0]))
    r = cur.fetchone()
    print(f'  重复借阅: code={r[3]}, msg={r[2]}')
except Exception as e:
    print(f'  重复借阅被拦截: {str(e).splitlines()[0][:80]}')
    conn.rollback()
    cur = conn.cursor()

conn.rollback()
cur = conn.cursor()

# --- 3.4 批量逾期测试 ---
try:
    cur.execute('CALL sp_batch_process_overdue(NULL, NULL, NULL, NULL)')
    r = cur.fetchone()
    print(f'  sp_batch_process_overdue: code={r[3]}, msg={r[2]}')
except Exception as e:
    print(f'  sp_batch_process_overdue 异常: {e}')
    conn.rollback()
    cur = conn.cursor()

conn.rollback()
cur = conn.cursor()

# --- 3.5 预约清理测试 ---
try:
    cur.execute('CALL sp_cleanup_expired_reservations(NULL, NULL, NULL, NULL)')
    r = cur.fetchone()
    print(f'  sp_cleanup_expired_reservations: code={r[3]}, msg={r[2]}')
except Exception as e:
    print(f'  sp_cleanup_expired_reservations 异常: {e}')
    conn.rollback()
    cur = conn.cursor()

conn.rollback()
cur = conn.cursor()

# --- 3.2 归还测试（选一条在借记录） ---
cur.execute("SELECT id FROM borrow_records WHERE status IN ('borrowed','overdue') LIMIT 1")
row = cur.fetchone()
if row:
    try:
        cur.execute('CALL sp_return_book(%s, NULL, NULL, NULL)', (row[0],))
        r = cur.fetchone()
        print(f'  sp_return_book(记录{row[0]}): code={r[2]}, msg={r[1]}, 罚款={r[0]}')
    except Exception as e:
        print(f'  sp_return_book 异常: {e}')
    conn.rollback()
    cur = conn.cursor()
else:
    print('  无在借记录，跳过 sp_return_book 测试')

# --- 3.3 续借测试 ---
cur.execute("SELECT id FROM borrow_records WHERE status = 'borrowed' LIMIT 1")
row = cur.fetchone()
if row:
    try:
        cur.execute('CALL sp_renew_book(%s, NULL, NULL, NULL, NULL)', (row[0],))
        r = cur.fetchone()
        # OUT 参数: r[0]=新应还日期, r[1]=msg, r[2]=code
        print(f'  sp_renew_book(记录{row[0]}): code={r[2]}, msg={r[1]}, 新应还={r[0]}')
    except Exception as e:
        print(f'  sp_renew_book 异常: {e}')
    conn.rollback()
    cur = conn.cursor()
else:
    print('  无 borrowed 状态记录，跳过 sp_renew_book 测试')

# --- 2.4 用户审计触发器测试 ---
try:
    cur.execute("UPDATE users SET status = 0 WHERE id = %s", (user[0],))
    cur.execute(
        "SELECT action, detail FROM audit_logs "
        "WHERE action = 'TRIGGER_USER_CHANGE' AND resource_id = %s",
        (user[0],))
    r = cur.fetchone()
    print(f'  审计触发器: {r[0]} - {r[1]}' if r else '  审计触发器: 未记录')
except Exception as e:
    print(f'  审计触发器异常: {e}')
conn.rollback()

print()
print('=' * 60)
print('全部验证完成（所有写操作已回滚，数据未受影响）')
print('=' * 60)

cur.close()
conn.close()
