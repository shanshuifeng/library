"""
解析并执行 triggers_and_procedures.sql 到 openGauss 6 数据库
自动将 CREATE PROCEDURE 的 $$ 语法转换为 openGauss 兼容格式
用法: python _execute_triggers_procedures.py
"""
import psycopg
import sys
import re
import os

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '192.168.116.141'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'dbname': os.getenv('DB_NAME', 'book_manager'),
    'user': os.getenv('DB_USER', 'remote_user'),
    'password': os.getenv('DB_PASSWORD', ''),
    'sslmode': 'prefer',
    'connect_timeout': 10,
}

SQL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'triggers_and_procedures.sql')


def adapt_procedure_for_opengauss(stmt: str) -> str:
    """
    将标准 PL/pgSQL 的 CREATE PROCEDURE 语法转换为 openGauss 6 兼容格式。
    openGauss 6 的 CREATE PROCEDURE 不支持 $$ 美元引用和 LANGUAGE plpgsql。

    转换规则:
      - AS $$  →  AS
      - END;\\n$$ LANGUAGE plpgsql;  →  END;
    """
    if not re.search(r'CREATE\s+OR\s+REPLACE\s+PROCEDURE\b', stmt, re.IGNORECASE):
        return stmt

    # 移除 AS 后的 $$
    stmt = re.sub(r'(\)\s*)AS\s*\$\$', r'\1AS', stmt, count=1)

    # 移除结尾的 $$ LANGUAGE plpgsql;
    stmt = re.sub(r'\$\$\s*LANGUAGE\s+plpgsql\s*;', ';', stmt)

    return stmt


def split_sql_statements(sql_text: str) -> list[str]:
    """
    将 SQL 文本拆分为独立语句，正确处理:
      - $$ ... $$ PL/pgSQL 块 (函数和触发器函数)
      - CREATE PROCEDURE ... END; 块 (openGauss 语法，无 $$)
    """
    statements = []
    current: list[str] = []
    in_dollar_quote = False
    in_procedure = False

    for line in sql_text.splitlines():
        stripped = line.strip()
        current.append(line)

        # 空行和纯注释行加入 current 但不触发分割
        if not stripped or stripped.startswith('--'):
            continue

        # 追踪存储过程模式 (必须在 $$ 追踪之前，因为过程的 $$ 需要被忽略)
        if re.match(r'CREATE\s+OR\s+REPLACE\s+PROCEDURE\b', stripped, re.IGNORECASE):
            in_procedure = True

        # 追踪 $$ 状态 (仅对函数和触发器函数生效，存储过程的 $$ 会被 adapt 转换)
        if not in_procedure:
            dollar_count = stripped.count('$$')
            for _ in range(dollar_count):
                in_dollar_quote = not in_dollar_quote

        # 语句结束判定
        if not in_dollar_quote and stripped.endswith(';'):
            if in_procedure:
                # 存储过程只在 END; 时结束 (不含 END IF; / END LOOP;)
                if stripped == 'END;':
                    in_procedure = False
                    stmt = '\n'.join(current).strip()
                    if stmt:
                        statements.append(stmt)
                    current = []
                # 过程体内的其他分号不触发分割
            else:
                stmt = '\n'.join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []

    # 处理末尾残余
    if current:
        stmt = '\n'.join(current).strip()
        if stmt:
            statements.append(stmt)

    return statements


def is_executable(stmt: str) -> bool:
    """判断语句是否需要执行"""
    upper = stmt.upper().strip()
    return not upper.startswith('ALTER TABLE')


def get_object_name(stmt: str) -> str:
    """提取对象名称用于显示"""
    m = re.search(
        r'(?:FUNCTION|PROCEDURE|TRIGGER)\s+(\S+)',
        stmt, re.IGNORECASE
    )
    if m:
        return m.group(1)
    return stmt[:60] + '...'


def get_object_type(stmt: str) -> str:
    """提取对象类型"""
    if re.search(r'CREATE\s+OR\s+REPLACE\s+PROCEDURE\b', stmt, re.IGNORECASE):
        return 'PROCEDURE'
    elif re.search(r'CREATE\s+OR\s+REPLACE\s+FUNCTION\b', stmt, re.IGNORECASE):
        return 'FUNCTION'
    elif re.search(r'CREATE\s+TRIGGER\b', stmt, re.IGNORECASE):
        return 'TRIGGER'
    elif re.search(r'COMMENT\s+ON\b', stmt, re.IGNORECASE):
        return 'COMMENT'
    return 'OTHER'


def main():
    print(f'读取 SQL 文件: {SQL_FILE}')
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql_text = f.read()

    statements = split_sql_statements(sql_text)
    print(f'共解析出 {len(statements)} 条语句\n')

    conn = psycopg.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    success = []
    failed = []

    for i, stmt in enumerate(statements, 1):
        if not is_executable(stmt):
            continue

        name = get_object_name(stmt)
        obj_type = get_object_type(stmt)

        # openGauss 存储过程语法适配
        if obj_type == 'PROCEDURE':
            stmt = adapt_procedure_for_opengauss(stmt)

        try:
            cur.execute(stmt)
            success.append((obj_type, name))
            print(f'  [{i:2d}] OK  [{obj_type:9s}] {name}')
        except Exception as e:
            err_msg = str(e).split('\n')[0][:120]
            failed.append((obj_type, name, err_msg))
            print(f'  [{i:2d}] FAIL [{obj_type:9s}] {name}')
            print(f'         {err_msg}')

    cur.close()
    conn.close()

    # 汇总
    print(f'\n{"="*60}')
    print(f'成功: {len(success)}  失败: {len(failed)}')

    if failed:
        print(f'\n失败详情:')
        for obj_type, name, err in failed:
            print(f'  - [{obj_type}] {name}: {err}')
        sys.exit(1)
    else:
        print('所有对象创建成功!')


if __name__ == '__main__':
    main()
