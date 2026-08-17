-- ============================================================
-- 图书管理系统 - 触发器 / 存储过程 / 工具函数 完整测试脚本
--
-- 数据库: book_manager (openGauss 6.x)
-- 字符集: UTF-8
--
-- 测试内容（共 39 项，正常应全部通过，数据不足或模块未部署时个别项显示 SKIP）:
--   Part 1: 对象存在性检查     18 项（10 函数/过程 + 5 触发器 + 3 评价模块可选项）
--   Part 2: 工具函数功能测试    9 项（期望值自动从 system_config / 业务表推导）
--   Part 3: 触发器功能测试      6 项（借阅校验 / 扣库存 / 还库存 / 审计 / 预约校验 / 评价聚合）
--   Part 4: 存储过程功能测试    6 项（借书 / 还书 / 续借 / 批量逾期 / 预约清理 / 评分重算）
--
-- 特点:
--   1. 全部测试运行在同一个事务中，脚本结尾统一 ROLLBACK，
--      不会修改任何真实数据（可反复执行）
--   2. 测试结果写入临时表 test_results，结尾统一输出明细与汇总
--   3. 期望值不写死，而是与 system_config 配置表 / 业务表实时对比，
--      修改配置后测试依然有效
--   4. 库存相关测试（3.1 / 3.2 / 4.1）会自动检测库存触发器的启用状态：
--      启用时校验库存增减，禁用时（应用层管理模式）自动跳过库存校验
--   5. 评价模块（book_reviews 的触发器/存储过程）为可选部署：
--      未部署时相关项显示 SKIP（不视为缺失），部署 review_triggers_procedures.sql 后自动参与测试
--
-- 用法:
--   虚拟机内:  gsql -d book_manager -p 5432 -U remote_user -f test_all_objects.sql
--   Windows :  python _run_test_all.py   （自动连接并执行本文件）
--
-- 查询优化说明:
--   · Part 3/4 选取测试数据不再使用 users×books 笛卡尔积，
--     改为"先选书、再选满足条件的用户"两步定位，数据量大时依然高效
--   · 4.1 按"在借数最少"排序改为聚合 JOIN 一次算好，替代逐行相关子查询
--   · 3.2 / 4.2 / 4.3 用单条 SELECT + IF NOT FOUND 取代"先 COUNT 再 SELECT"两步
--   · 2.5 / 2.6 为全库一致性核对（刻意保留）：逐行调用函数验证，
--     当前数据规模下开销可忽略；若藏书量增长到数千本可加 LIMIT 抽样
-- ============================================================


BEGIN;

-- 测试结果临时表（会话级，事务回滚后自动消失）
-- 注意: openGauss 临时表不支持 SERIAL/IDENTITY，改用事务内普通序列，
--       ROLLBACK 后序列与临时表一起消失，不在数据库中残留
DROP TABLE IF EXISTS test_results;
DROP SEQUENCE IF EXISTS test_results_seq;
CREATE SEQUENCE test_results_seq;
CREATE TEMP TABLE test_results (
    seq       INT DEFAULT nextval('test_results_seq'),
    test_name VARCHAR(120),
    result    VARCHAR(8),   -- PASS / FAIL / SKIP
    detail    TEXT
);


-- ============================================================
-- Part 1: 对象存在性检查（18 项）
-- ============================================================

-- 1.1 五个工具函数 + 五个存储过程是否已创建
INSERT INTO test_results (test_name, result, detail)
SELECT '存在: ' || e.obj || '（' || e.kind || '）',
       CASE WHEN p.oid IS NOT NULL THEN 'PASS' ELSE 'FAIL' END,
       CASE WHEN p.oid IS NOT NULL THEN '已创建' ELSE '数据库中未找到' END
FROM (VALUES
    ('fn_calculate_overdue_fine',      '函数'),
    ('fn_get_user_active_borrows',     '函数'),
    ('fn_get_available_stock',         '函数'),
    ('fn_get_reservation_position',    '函数'),
    ('fn_get_borrow_limit',            '函数'),
    ('sp_borrow_book',                 '存储过程'),
    ('sp_return_book',                 '存储过程'),
    ('sp_renew_book',                  '存储过程'),
    ('sp_batch_process_overdue',       '存储过程'),
    ('sp_cleanup_expired_reservations','存储过程')
) AS e(obj, kind)
LEFT JOIN pg_proc p
       ON p.proname = e.obj
      AND p.pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');

-- 1.2 五个触发器是否已创建且处于启用状态
INSERT INTO test_results (test_name, result, detail)
SELECT '存在: ' || e.tg || ' ON ' || e.tbl,
       CASE WHEN t.oid IS NOT NULL THEN 'PASS' ELSE 'FAIL' END,
       CASE WHEN t.oid IS NULL     THEN '数据库中未找到'
            WHEN t.tgenabled = 'O' THEN '已创建且启用'
            ELSE '已创建但被禁用（状态 ' || t.tgenabled::text || '）'
       END
FROM (VALUES
    ('trg_before_borrow_validate',      'borrow_records'),
    ('trg_after_borrow_decrease_stock', 'borrow_records'),
    ('trg_after_return_increase_stock', 'borrow_records'),
    ('trg_audit_user_role_change',      'users'),
    ('trg_before_reservation_check',    'reservations')
) AS e(tg, tbl)
LEFT JOIN pg_trigger t
       ON t.tgname = e.tg
      AND NOT t.tgisinternal
      AND t.tgrelid = (SELECT c.oid
                         FROM pg_class c
                         JOIN pg_namespace n ON c.relnamespace = n.oid
                        WHERE c.relname = e.tbl
                          AND n.nspname = 'public');

-- 1.3 评价模块（可选部署）：未部署显示 SKIP，不视为缺失
INSERT INTO test_results (test_name, result, detail)
SELECT '存在: ' || e.obj || '（' || e.kind || '，评价模块）',
       CASE WHEN p.oid IS NOT NULL THEN 'PASS' ELSE 'SKIP' END,
       CASE WHEN p.oid IS NOT NULL THEN '已部署'
            ELSE '评价模块未部署（可选），部署 review_triggers_procedures.sql 后自动测试' END
FROM (VALUES
    ('fn_maintain_book_rating',    '函数'),
    ('sp_recalculate_book_rating', '存储过程')
) AS e(obj, kind)
LEFT JOIN pg_proc p
       ON p.proname = e.obj
      AND p.pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');

INSERT INTO test_results (test_name, result, detail)
SELECT '存在: trg_after_review_maintain_rating ON book_reviews（评价模块）',
       CASE WHEN t.oid IS NOT NULL THEN 'PASS' ELSE 'SKIP' END,
       CASE WHEN t.oid IS NOT NULL THEN '已部署'
            ELSE '评价模块未部署（可选），部署 review_triggers_procedures.sql 后自动测试' END
FROM (VALUES (1)) AS x(n)
LEFT JOIN pg_trigger t
       ON t.tgname = 'trg_after_review_maintain_rating'
      AND NOT t.tgisinternal
      AND t.tgrelid = (SELECT c.oid
                         FROM pg_class c
                         JOIN pg_namespace n ON c.relnamespace = n.oid
                        WHERE c.relname = 'book_reviews'
                          AND n.nspname = 'public');


-- ============================================================
-- Part 2: 工具函数功能测试（9 项）
--   期望值全部从 system_config / 业务表实时推导，不写死
-- ============================================================

-- 2.1 fn_get_borrow_limit：三种角色的返回值应与 system_config 一致
INSERT INTO test_results (test_name, result, detail)
SELECT '函数: fn_get_borrow_limit(' || k.role || ')',
       CASE WHEN fn_get_borrow_limit(k.role) = k.cfg THEN 'PASS' ELSE 'FAIL' END,
       '期望=' || k.cfg || ' 实际=' || fn_get_borrow_limit(k.role)
FROM (
    SELECT 'student' AS role, config_value::INT AS cfg
      FROM system_config WHERE config_key = 'max_borrow_student'
    UNION ALL
    SELECT 'teacher', config_value::INT
      FROM system_config WHERE config_key = 'max_borrow_teacher'
    UNION ALL
    SELECT 'admin', config_value::INT
      FROM system_config WHERE config_key = 'max_borrow_admin'
) k;

-- 2.2 fn_calculate_overdue_fine：逾期 14 天 = 14 x 每日罚款
INSERT INTO test_results (test_name, result, detail)
SELECT '函数: fn_calculate_overdue_fine（逾期14天）',
       CASE WHEN fn_calculate_overdue_fine(CURRENT_DATE - 14, CURRENT_DATE) = 14 * cfg.rate
            THEN 'PASS' ELSE 'FAIL' END,
       '期望=' || 14 * cfg.rate || ' 实际='
       || fn_calculate_overdue_fine(CURRENT_DATE - 14, CURRENT_DATE)
FROM (SELECT config_value::NUMERIC(10,2) AS rate
        FROM system_config WHERE config_key = 'fine_per_day') cfg;

-- 2.3 fn_calculate_overdue_fine：未逾期应为 0
INSERT INTO test_results (test_name, result, detail)
SELECT '函数: fn_calculate_overdue_fine（未逾期）',
       CASE WHEN fn_calculate_overdue_fine(CURRENT_DATE + 5, CURRENT_DATE) = 0
            THEN 'PASS' ELSE 'FAIL' END,
       '实际=' || fn_calculate_overdue_fine(CURRENT_DATE + 5, CURRENT_DATE);

-- 2.4 fn_calculate_overdue_fine：归还日期缺省（取今天），逾期 3 天
INSERT INTO test_results (test_name, result, detail)
SELECT '函数: fn_calculate_overdue_fine（缺省归还日）',
       CASE WHEN fn_calculate_overdue_fine(CURRENT_DATE - 3) = 3 * cfg.rate
            THEN 'PASS' ELSE 'FAIL' END,
       '期望=' || 3 * cfg.rate || ' 实际=' || fn_calculate_overdue_fine(CURRENT_DATE - 3)
FROM (SELECT config_value::NUMERIC(10,2) AS rate
        FROM system_config WHERE config_key = 'fine_per_day') cfg;

-- 2.5 fn_get_available_stock：应等于 books.stock（全库核对，逐本调用函数）
INSERT INTO test_results (test_name, result, detail)
SELECT '函数: fn_get_available_stock（全库核对）',
       CASE WHEN SUM(CASE WHEN fn_get_available_stock(b.id) <> b.stock THEN 1 ELSE 0 END) = 0
             AND COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END,
       '核对了 ' || COUNT(*) || ' 本图书的 stock 字段'
FROM books b;

-- 2.6 fn_get_user_active_borrows：应等于在借记录数（全库核对，逐用户调用函数）
INSERT INTO test_results (test_name, result, detail)
SELECT '函数: fn_get_user_active_borrows（全库核对）',
       CASE WHEN SUM(CASE WHEN fn_get_user_active_borrows(u.id) <> COALESCE(c.cnt, 0)
                          THEN 1 ELSE 0 END) = 0
             AND COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END,
       '核对了 ' || COUNT(*) || ' 个用户的在借计数'
FROM users u
LEFT JOIN (
    SELECT user_id, COUNT(*) AS cnt
      FROM borrow_records
     WHERE status IN ('borrowed', 'overdue')
     GROUP BY user_id
) c ON c.user_id = u.id;

-- 2.7 fn_get_reservation_position：未排队用户应返回 0
--     （先取第一本书，再找一位未预约它的用户，避免 users×books 笛卡尔积）
INSERT INTO test_results (test_name, result, detail)
SELECT '函数: fn_get_reservation_position（未排队=0）',
       CASE WHEN fn_get_reservation_position(p.uid, p.bid) = 0 THEN 'PASS' ELSE 'FAIL' END,
       'user=' || p.uid || ' book=' || p.bid || ' 实际='
       || fn_get_reservation_position(p.uid, p.bid)
FROM (
    SELECT u.id AS uid, b.id AS bid
      FROM (SELECT id FROM books ORDER BY id LIMIT 1) b
      JOIN users u
        ON NOT EXISTS (SELECT 1 FROM reservations r
                        WHERE r.user_id = u.id AND r.book_id = b.id
                          AND r.status IN ('pending', 'ready'))
     ORDER BY u.id
     LIMIT 1
) p;


-- ============================================================
-- Part 3: 触发器功能测试（6 项）
-- ============================================================

-- 3.1 借阅触发器：
--     a) 正常 INSERT 借阅记录后，trg_after_borrow_decrease_stock 库存自动 -1
--        （若该触发器被禁用——应用层管理模式——则 SKIP）
--     b) 同一用户重复借同一本书，trg_before_borrow_validate 应拦截
DO $$
DECLARE
    v_user_id       INT;
    v_book_id       INT;
    v_stock_before  INT;
    v_stock_after   INT;
    v_blocked       BOOLEAN := FALSE;
    v_tg_enabled    BOOLEAN;
BEGIN
    -- 检查库存触发器是否启用（缺失时按禁用处理）
    SELECT COALESCE(tgenabled = 'O', FALSE) INTO v_tg_enabled
      FROM pg_trigger WHERE tgname = 'trg_after_borrow_decrease_stock';

    -- 选一本有库存（>=2，保证重复借阅测试命中的是"重复"而非"库存不足"）、
    -- 且至少一名正常用户未在借的书
    SELECT b.id INTO v_book_id
      FROM books b
     WHERE b.stock >= 2
       AND EXISTS (SELECT 1 FROM users u
                    WHERE u.status = 1
                      AND NOT EXISTS (SELECT 1 FROM borrow_records r
                                       WHERE r.user_id = u.id AND r.book_id = b.id
                                         AND r.status IN ('borrowed', 'overdue')))
     ORDER BY b.id
     LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: 借阅校验+扣库存', 'SKIP', '无满足条件的图书');
        RETURN;
    END IF;

    -- 选一名状态正常、未借过该书、在借数最少的用户（避免触发额度限制）
    SELECT u.id INTO v_user_id
      FROM users u
      LEFT JOIN (SELECT user_id, COUNT(*) AS cnt
                   FROM borrow_records
                  WHERE status IN ('borrowed', 'overdue')
                  GROUP BY user_id) c ON c.user_id = u.id
     WHERE u.status = 1
       AND NOT EXISTS (SELECT 1 FROM borrow_records r
                        WHERE r.user_id = u.id AND r.book_id = v_book_id
                          AND r.status IN ('borrowed', 'overdue'))
     ORDER BY COALESCE(c.cnt, 0), u.id
     LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: 借阅校验+扣库存', 'SKIP', '无满足条件的用户');
        RETURN;
    END IF;

    SELECT stock INTO v_stock_before FROM books WHERE id = v_book_id;

    INSERT INTO borrow_records (user_id, book_id, borrow_date, due_date, status)
    VALUES (v_user_id, v_book_id, CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP + INTERVAL '30 day', 'borrowed');

    SELECT stock INTO v_stock_after FROM books WHERE id = v_book_id;

    IF v_tg_enabled THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_after_borrow_decrease_stock',
                CASE WHEN v_stock_after = v_stock_before - 1 THEN 'PASS' ELSE 'FAIL' END,
                '借阅后库存 ' || v_stock_before || ' -> ' || v_stock_after || '（期望 -1）');
    ELSE
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_after_borrow_decrease_stock', 'SKIP',
                '触发器已禁用（应用层管理模式），借阅后库存 ' || v_stock_before
                || ' -> ' || v_stock_after || '（期望不变）');
    END IF;

    -- 重复借阅应被拦截（触发器抛出异常即视为生效）
    BEGIN
        INSERT INTO borrow_records (user_id, book_id, borrow_date, due_date, status)
        VALUES (v_user_id, v_book_id, CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP + INTERVAL '30 day', 'borrowed');
    EXCEPTION WHEN OTHERS THEN
        v_blocked := TRUE;
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_before_borrow_validate（重复借阅拦截）',
                CASE WHEN SQLERRM LIKE '%已借阅%' THEN 'PASS' ELSE 'FAIL' END,
                '拦截消息: ' || SQLERRM);
    END;

    IF NOT v_blocked THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_before_borrow_validate（重复借阅拦截）',
                'FAIL', '重复借阅未被拦截');
    END IF;
END $$;

-- 3.2 归还触发器：把在借记录改为 returned 后，trg_after_return_increase_stock 库存自动 +1
--     （若该触发器被禁用——应用层管理模式——则 SKIP）
DO $$
DECLARE
    v_rec_id      INT;
    v_book_id     INT;
    v_before      INT;
    v_after       INT;
    v_tg_enabled  BOOLEAN;
BEGIN
    SELECT COALESCE(tgenabled = 'O', FALSE) INTO v_tg_enabled
      FROM pg_trigger WHERE tgname = 'trg_after_return_increase_stock';

    SELECT id, book_id INTO v_rec_id, v_book_id
      FROM borrow_records
     WHERE status IN ('borrowed', 'overdue')
     ORDER BY id LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_after_return_increase_stock', 'SKIP', '无在借记录');
        RETURN;
    END IF;

    SELECT stock INTO v_before FROM books WHERE id = v_book_id;

    UPDATE borrow_records
       SET status = 'returned', return_date = CURRENT_TIMESTAMP
     WHERE id = v_rec_id;

    SELECT stock INTO v_after FROM books WHERE id = v_book_id;

    IF v_tg_enabled THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_after_return_increase_stock',
                CASE WHEN v_after = v_before + 1 THEN 'PASS' ELSE 'FAIL' END,
                '记录' || v_rec_id || ' 归还后库存 ' || v_before || ' -> ' || v_after || '（期望 +1）');
    ELSE
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_after_return_increase_stock', 'SKIP',
                '触发器已禁用（应用层管理模式），归还后库存 ' || v_before
                || ' -> ' || v_after || '（期望不变）');
    END IF;
END $$;

-- 3.3 审计触发器：变更用户状态后，trg_audit_user_role_change 应写入 audit_logs
DO $$
DECLARE
    v_user_id INT;
    v_before  INT;
    v_after   INT;
BEGIN
    SELECT id INTO v_user_id FROM users ORDER BY id LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_audit_user_role_change', 'SKIP', '无用户');
        RETURN;
    END IF;

    SELECT COUNT(*) INTO v_before
      FROM audit_logs WHERE action = 'TRIGGER_USER_CHANGE';

    UPDATE users SET status = 1 - status WHERE id = v_user_id;

    SELECT COUNT(*) INTO v_after
      FROM audit_logs WHERE action = 'TRIGGER_USER_CHANGE';

    INSERT INTO test_results (test_name, result, detail)
    VALUES ('触发器: trg_audit_user_role_change',
            CASE WHEN v_after = v_before + 1 THEN 'PASS' ELSE 'FAIL' END,
            '变更用户' || v_user_id || ' 状态后审计日志 ' || v_before || ' -> ' || v_after || '（期望 +1）');
END $$;

-- 3.4 预约触发器：同一用户重复预约同一本书，trg_before_reservation_check 应拦截
DO $$
DECLARE
    v_user_id  INT;
    v_book_id  INT;
    v_blocked  BOOLEAN := FALSE;
BEGIN
    -- 先取第一本书，再找一位未预约它的用户（避免笛卡尔积）
    SELECT id INTO v_book_id FROM books ORDER BY id LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_before_reservation_check（重复预约拦截）', 'SKIP', '无图书');
        RETURN;
    END IF;

    SELECT u.id INTO v_user_id
      FROM users u
     WHERE NOT EXISTS (SELECT 1 FROM reservations r
                        WHERE r.user_id = u.id AND r.book_id = v_book_id
                          AND r.status IN ('pending', 'ready'))
     ORDER BY u.id
     LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_before_reservation_check（重复预约拦截）', 'SKIP', '无未预约该书用户');
        RETURN;
    END IF;

    -- 第一次预约（应成功）
    INSERT INTO reservations (user_id, book_id, status, created_at, expiry_date)
    VALUES (v_user_id, v_book_id, 'pending', CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP + INTERVAL '3 day');

    -- 第二次预约同一本书（应被触发器拦截）
    BEGIN
        INSERT INTO reservations (user_id, book_id, status, created_at, expiry_date)
        VALUES (v_user_id, v_book_id, 'pending', CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP + INTERVAL '3 day');
    EXCEPTION WHEN OTHERS THEN
        v_blocked := TRUE;
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_before_reservation_check（重复预约拦截）',
                CASE WHEN SQLERRM LIKE '%预约%' THEN 'PASS' ELSE 'FAIL' END,
                '拦截消息: ' || SQLERRM);
    END;

    IF NOT v_blocked THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_before_reservation_check（重复预约拦截）',
                'FAIL', '重复预约未被拦截');
    END IF;
END $$;

-- 3.5 评价聚合触发器：写入评价后 books.avg_rating / review_count 应同步更新
--     （评价模块未部署时 SKIP）
DO $$
DECLARE
    v_tg_exists  INT;
    v_bid        INT;
    v_uid        INT;
    v_exp_avg    NUMERIC(3,2);
    v_exp_cnt    INT;
    v_avg        NUMERIC(3,2);
    v_cnt        INT;
BEGIN
    SELECT COUNT(*) INTO v_tg_exists
      FROM pg_trigger t
      JOIN pg_class c ON t.tgrelid = c.oid
      JOIN pg_namespace n ON c.relnamespace = n.oid
     WHERE t.tgname = 'trg_after_review_maintain_rating'
       AND NOT t.tgisinternal
       AND t.tgenabled = 'O'
       AND n.nspname = 'public'
       AND c.relname = 'book_reviews';

    IF v_tg_exists = 0 THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_after_review_maintain_rating', 'SKIP',
                '评价模块未部署（可选），部署后自动测试');
        RETURN;
    END IF;

    SELECT id INTO v_bid FROM books ORDER BY id LIMIT 1;
    IF NOT FOUND THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_after_review_maintain_rating', 'SKIP', '无图书');
        RETURN;
    END IF;

    -- 找一位未评价过该书的用户（受 idx_review_book_user 唯一约束保护）
    SELECT u.id INTO v_uid
      FROM users u
     WHERE NOT EXISTS (SELECT 1 FROM book_reviews v
                        WHERE v.book_id = v_bid AND v.user_id = u.id)
     ORDER BY u.id LIMIT 1;
    IF NOT FOUND THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('触发器: trg_after_review_maintain_rating', 'SKIP', '所有用户均已评价该书');
        RETURN;
    END IF;

    INSERT INTO book_reviews (user_id, book_id, rating, content, created_at, updated_at)
    VALUES (v_uid, v_bid, 5, '测试评价（事务内回滚）', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

    SELECT COALESCE(ROUND(AVG(rating)::numeric, 2), 0), COUNT(*)
      INTO v_exp_avg, v_exp_cnt
      FROM book_reviews WHERE book_id = v_bid;
    SELECT avg_rating, review_count INTO v_avg, v_cnt
      FROM books WHERE id = v_bid;

    INSERT INTO test_results (test_name, result, detail)
    VALUES ('触发器: trg_after_review_maintain_rating',
            CASE WHEN v_avg = v_exp_avg AND v_cnt = v_exp_cnt THEN 'PASS' ELSE 'FAIL' END,
            '写入评价后 avg_rating=' || v_avg || '（期望 ' || v_exp_avg
            || '） review_count=' || v_cnt || '（期望 ' || v_exp_cnt || '）');
END $$;


-- ============================================================
-- Part 4: 存储过程功能测试（6 项）
--   注意: openGauss 的 DO 块内不能用 CALL 关键字传递 OUT 变量
--   （会报 query has no destination for result data），
--   应直接用过程名调用（Oracle 风格），OUT 参数自动写入变量
-- ============================================================

-- 4.1 sp_borrow_book：完整借书（校验 + 建档 + 触发器扣库存）
--     库存触发器禁用时只校验 code=0 和记录创建，不校验库存变化
DO $$
DECLARE
    v_user_id      INT;
    v_book_id      INT;
    v_before       INT;
    v_after        INT;
    v_record_id    INT;
    v_due_date     DATE;
    v_msg          TEXT;
    v_code         INT;
    v_tg_enabled   BOOLEAN;
BEGIN
    SELECT COALESCE(tgenabled = 'O', FALSE) INTO v_tg_enabled
      FROM pg_trigger WHERE tgname = 'trg_after_borrow_decrease_stock';

    -- 先选一本有库存、且至少一名正常用户可借的书
    SELECT b.id INTO v_book_id
      FROM books b
     WHERE b.stock > 0
       AND EXISTS (SELECT 1 FROM users u
                    WHERE u.status = 1
                      AND NOT EXISTS (SELECT 1 FROM borrow_records r
                                       WHERE r.user_id = u.id AND r.book_id = b.id
                                         AND r.status IN ('borrowed', 'overdue')))
     ORDER BY b.id
     LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('过程: sp_borrow_book', 'SKIP', '无满足条件的图书');
        RETURN;
    END IF;

    -- 再选一名状态正常、未借过该书、在借数最少的用户，避免触发额度限制
    -- （在借数用聚合 JOIN 一次算好，替代逐行相关子查询）
    SELECT u.id INTO v_user_id
      FROM users u
      LEFT JOIN (SELECT user_id, COUNT(*) AS cnt
                   FROM borrow_records
                  WHERE status IN ('borrowed', 'overdue')
                  GROUP BY user_id) c ON c.user_id = u.id
     WHERE u.status = 1
       AND NOT EXISTS (SELECT 1 FROM borrow_records r
                        WHERE r.user_id = u.id AND r.book_id = v_book_id
                          AND r.status IN ('borrowed', 'overdue'))
     ORDER BY COALESCE(c.cnt, 0), u.id
     LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('过程: sp_borrow_book', 'SKIP', '无满足条件的用户');
        RETURN;
    END IF;

    SELECT stock INTO v_before FROM books WHERE id = v_book_id;

    sp_borrow_book(v_user_id, v_book_id, NULL,
                   v_record_id, v_due_date, v_msg, v_code);

    SELECT stock INTO v_after FROM books WHERE id = v_book_id;

    INSERT INTO test_results (test_name, result, detail)
    VALUES ('过程: sp_borrow_book',
            CASE WHEN v_code = 0 AND v_record_id IS NOT NULL
                  AND (NOT v_tg_enabled OR v_after = v_before - 1)
                 THEN 'PASS' ELSE 'FAIL' END,
            'code=' || v_code || ' 记录ID=' || COALESCE(v_record_id::TEXT, '无')
            || ' 库存 ' || v_before || '->' || v_after
            || CASE WHEN v_tg_enabled THEN '' ELSE '（库存触发器已禁用，不校验）' END
            || ' msg=' || v_msg);
END $$;

-- 4.2 sp_return_book：完整还书（校验 + 罚款 + 触发器恢复库存）
DO $$
DECLARE
    v_rec_id  INT;
    v_fine    NUMERIC(10,2);
    v_msg     TEXT;
    v_code    INT;
BEGIN
    SELECT id INTO v_rec_id
      FROM borrow_records
     WHERE status IN ('borrowed', 'overdue')
     ORDER BY id LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('过程: sp_return_book', 'SKIP', '无在借记录');
        RETURN;
    END IF;

    sp_return_book(v_rec_id, v_fine, v_msg, v_code);

    INSERT INTO test_results (test_name, result, detail)
    VALUES ('过程: sp_return_book',
            CASE WHEN v_code = 0 THEN 'PASS' ELSE 'FAIL' END,
            'code=' || v_code || ' 记录' || v_rec_id
            || ' 罚款=' || COALESCE(v_fine::TEXT, '?') || ' msg=' || v_msg);
END $$;

-- 4.3 sp_renew_book：续借（校验后延长应还日期）
DO $$
DECLARE
    v_rec_id   INT;
    v_old_due  TIMESTAMP;
    v_new_due  DATE;
    v_msg      TEXT;
    v_code     INT;
BEGIN
    -- 选取可续借的记录：在借、未被预约排队、续借次数未达上限
    SELECT id, due_date INTO v_rec_id, v_old_due
      FROM borrow_records r
     WHERE r.status = 'borrowed'
       AND r.renew_count < 2
       AND NOT EXISTS (SELECT 1 FROM reservations v
                        WHERE v.book_id = r.book_id
                          AND v.status IN ('pending', 'ready'))
     ORDER BY id LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('过程: sp_renew_book', 'SKIP', '无可续借的在借记录');
        RETURN;
    END IF;

    sp_renew_book(v_rec_id, NULL, v_new_due, v_msg, v_code);

    INSERT INTO test_results (test_name, result, detail)
    VALUES ('过程: sp_renew_book',
            CASE WHEN v_code = 0 AND v_new_due > v_old_due THEN 'PASS' ELSE 'FAIL' END,
            'code=' || v_code || ' 记录' || v_rec_id
            || ' 应还 ' || v_old_due || ' -> ' || COALESCE(v_new_due::TEXT, '?') || ' msg=' || v_msg);
END $$;

-- 4.4 sp_batch_process_overdue：批量标记逾期并累计罚款
DO $$
DECLARE
    v_processed  INT;
    v_total_fine NUMERIC(10,2);
    v_msg        TEXT;
    v_code       INT;
BEGIN
    sp_batch_process_overdue(v_processed, v_total_fine, v_msg, v_code);

    INSERT INTO test_results (test_name, result, detail)
    VALUES ('过程: sp_batch_process_overdue',
            CASE WHEN v_code = 0 THEN 'PASS' ELSE 'FAIL' END,
            'code=' || v_code || ' 标记 ' || v_processed
            || ' 条逾期，累计罚款 ' || v_total_fine || ' 元');
END $$;

-- 4.5 sp_cleanup_expired_reservations：清理过期预约并推进排队
DO $$
DECLARE
    v_cleaned  INT;
    v_promoted INT;
    v_msg      TEXT;
    v_code     INT;
BEGIN
    sp_cleanup_expired_reservations(v_cleaned, v_promoted, v_msg, v_code);

    INSERT INTO test_results (test_name, result, detail)
    VALUES ('过程: sp_cleanup_expired_reservations',
            CASE WHEN v_code = 0 THEN 'PASS' ELSE 'FAIL' END,
            'code=' || v_code || ' 清理 ' || v_cleaned
            || ' 条，推进队列 ' || v_promoted || ' 位');
END $$;

-- 4.6 sp_recalculate_book_rating：制造脏数据后重算，应恢复聚合评分
--     （评价模块未部署时 SKIP）
DO $$
DECLARE
    v_exists  INT;
    v_bid     INT;
    v_exp_avg NUMERIC(3,2);
    v_exp_cnt INT;
    v_avg     NUMERIC(3,2);
    v_cnt     INT;
BEGIN
    SELECT COUNT(*) INTO v_exists
      FROM pg_proc p
      JOIN pg_namespace n ON p.pronamespace = n.oid
     WHERE n.nspname = 'public'
       AND p.proname = 'sp_recalculate_book_rating';

    IF v_exists = 0 THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('过程: sp_recalculate_book_rating', 'SKIP',
                '评价模块未部署（可选），部署后自动测试');
        RETURN;
    END IF;

    SELECT id INTO v_bid FROM books ORDER BY id LIMIT 1;
    IF NOT FOUND THEN
        INSERT INTO test_results (test_name, result, detail)
        VALUES ('过程: sp_recalculate_book_rating', 'SKIP', '无图书');
        RETURN;
    END IF;

    -- 先制造"脏数据"，再让过程修复
    UPDATE books SET avg_rating = 0, review_count = 0 WHERE id = v_bid;

    -- 用动态 EXECUTE 调用：plpgsql 编译期就会解析静态函数名，
    -- 模块未部署时静态调用会在编译期报错，动态调用则在运行时才解析，
    -- 由上面的存在性判断保证到达此处时函数一定存在
    EXECUTE 'CALL sp_recalculate_book_rating(' || v_bid || ')';

    SELECT COALESCE(ROUND(AVG(rating)::numeric, 2), 0), COUNT(*)
      INTO v_exp_avg, v_exp_cnt
      FROM book_reviews WHERE book_id = v_bid;
    SELECT avg_rating, review_count INTO v_avg, v_cnt
      FROM books WHERE id = v_bid;

    INSERT INTO test_results (test_name, result, detail)
    VALUES ('过程: sp_recalculate_book_rating',
            CASE WHEN v_avg = v_exp_avg AND v_cnt = v_exp_cnt THEN 'PASS' ELSE 'FAIL' END,
            '重算后 avg_rating=' || v_avg || '（期望 ' || v_exp_avg
            || '） review_count=' || v_cnt || '（期望 ' || v_exp_cnt || '）');
END $$;


-- ============================================================
-- Part 5: 测试结果汇总
-- ============================================================

-- 5.1 明细
SELECT seq       AS "序号",
       test_name AS "测试项",
       result    AS "结果",
       detail    AS "说明"
  FROM test_results
 ORDER BY seq;

-- 5.2 汇总（失败数应为 0）
SELECT COUNT(*) AS "总项数",
       SUM(CASE WHEN result = 'PASS' THEN 1 ELSE 0 END) AS "通过",
       SUM(CASE WHEN result = 'FAIL' THEN 1 ELSE 0 END) AS "失败",
       SUM(CASE WHEN result = 'SKIP' THEN 1 ELSE 0 END) AS "跳过",
       CASE WHEN SUM(CASE WHEN result = 'FAIL' THEN 1 ELSE 0 END) = 0
            THEN '全部通过' ELSE '存在失败项，请检查' END AS "结论"
  FROM test_results;

-- ============================================================
-- 回滚全部测试写入，真实数据不受任何影响
-- ============================================================
ROLLBACK;

-- 回滚后校验（borrow_records 行数应与测试前一致）
SELECT COUNT(*) AS "回滚校验: borrow_records 总行数（应与执行前一致）"
  FROM borrow_records;
