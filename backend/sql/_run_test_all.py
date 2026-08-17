"""
在 Windows 上远程执行 test_all_objects.sql 并输出测试结果
（与在虚拟机内执行 gsql -f test_all_objects.sql 等价）

用法:  python _run_test_all.py
"""
import psycopg

DB = ('host=192.168.116.142 port=5432 dbname=book_manager '
      'user=remote_user password=NewPassword@123 sslmode=prefer')
SQL_FILE = 'test_all_objects.sql'


def split_statements(sql_text):
    """按分号拆分语句，跳过 $$ ... $$ 内部的分号（DO 块）"""
    statements = []
    buf = []
    in_dollar = False
    for line in sql_text.splitlines():
        stripped = line.strip()
        # 纯注释行直接保留（不判断分号）
        buf.append(line)
        if stripped.startswith('--'):
            continue
        # 统计本行的 $$ 出现次数（成对切换 dollar-quote 状态）
        if not in_dollar and line.count('$$') % 2 == 1:
            in_dollar = True
        elif in_dollar and line.count('$$') % 2 == 1:
            in_dollar = False
        # 不在 $$ 块内且行以 ; 结尾 => 语句结束
        if not in_dollar and stripped.endswith(';'):
            stmt = '\n'.join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
    tail = '\n'.join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def main():
    with open(SQL_FILE, encoding='utf-8') as f:
        sql_text = f.read()

    stmts = split_statements(sql_text)
    # 过滤纯注释/空语句
    stmts = [s for s in stmts
             if any(not ln.strip().startswith('--') and ln.strip()
                    for ln in s.splitlines())]

    # autocommit 模式：让文件中的 BEGIN ... ROLLBACK 自行控制事务
    conn = psycopg.connect(DB, autocommit=True)
    cur = conn.cursor()
    print(f'已连接数据库，共 {len(stmts)} 条语句\n')

    for stmt in stmts:
        head = next(ln.strip() for ln in stmt.splitlines()
                    if ln.strip() and not ln.strip().startswith('--'))
        verb = head.split()[0].upper()
        try:
            cur.execute(stmt)
            if stmt.rstrip().upper().endswith(';') and verb == 'SELECT':
                cols = [d.name for d in cur.description]
                rows = cur.fetchall()
                print(f'--- {head[:70]}')
                print('    ' + ' | '.join(str(c) for c in cols))
                for r in rows:
                    print('    ' + ' | '.join(str(v) for v in r))
                print()
            elif verb in ('INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE'):
                print(f'[{verb:<6}] {head[:66]}  ({cur.rowcount} 行)')
            else:
                print(f'[{verb:<6}] {head[:66]}')
        except Exception as e:
            print(f'[错误  ] {head[:66]}')
            print(f'         {str(e).splitlines()[0]}')
            # 出错的语句直接跳过（本脚本所有可预期失败都在 DO 块内被捕获）

    cur.close()
    conn.close()
    print('\n执行完毕（所有测试写入已由脚本末尾的 ROLLBACK 回滚）')


if __name__ == '__main__':
    main()
