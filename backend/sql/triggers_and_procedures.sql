-- ============================================================
-- 图书管理系统 - openGauss 6 触发器、存储过程与工具函数
--
-- 数据库: book_manager (openGauss 6.x / PostgreSQL 兼容)
-- 字符集: UTF-8
--
-- 目录
-- ============================================================
--  Part 1: 工具函数 (Utility Functions)
--    1.1 fn_calculate_overdue_fine       计算逾期罚款
--    1.2 fn_get_user_active_borrows       获取用户当前在借数量
--    1.3 fn_get_available_stock           获取图书可借库存
--    1.4 fn_get_reservation_position      获取用户预约排队位置
--    1.5 fn_get_borrow_limit              根据用户角色获取借阅上限
--
--  Part 2: 触发器 (Triggers)
--    2.1 trg_before_borrow_validate       借阅前校验（额度 + 库存 + 状态）
--    2.2 trg_after_borrow_decrease_stock  借阅后自动扣减库存
--    2.3 trg_after_return_increase_stock  归还后自动恢复库存
--    2.4 trg_audit_user_role_change      用户角色/状态变更自动审计
--    2.5 trg_before_reservation_check     预约前校验（重复 + 上限）
--
--  Part 3: 存储过程 (Stored Procedures)
--    3.1 sp_borrow_book                   完整借阅流程（校验 + 建档 + 扣库存）
--    3.2 sp_return_book                   完整归还流程（校验 + 罚款 + 恢复库存）
--    3.3 sp_renew_book                    图书续借（校验 + 延期）
--    3.4 sp_batch_process_overdue         批量标记逾期记录
--    3.5 sp_cleanup_expired_reservations  清理过期预约并通知排队读者
--
--  Part 4: 附注
--    - 启用/禁用指南
--    - 与应用层冲突说明
--    - 依赖的系统配置键说明
--    - 调用示例
-- ============================================================


-- ============================================================
-- Part 1: 工具函数
-- ============================================================

-- -------------------------------------------------------
-- 1.1 fn_calculate_overdue_fine
--      根据应还日期和实际归还日期计算逾期罚款
--      罚款标准从 system_config.fine_per_day 读取
--      与 BorrowRecord.calculate_fine() 逻辑一致
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_calculate_overdue_fine(
    p_due_date    DATE,
    p_return_date DATE DEFAULT NULL  -- 为 NULL 时取当前日期
) RETURNS NUMERIC(10,2)
AS $$
DECLARE
    v_return_date  DATE;
    v_overdue_days INT;
    v_fine_per_day NUMERIC(10,2);
BEGIN
    -- 归还日期为空则取今天
    v_return_date := COALESCE(p_return_date, CURRENT_DATE);

    -- 未逾期，罚款为 0
    IF v_return_date <= p_due_date THEN
        RETURN 0.00;
    END IF;

    -- openGauss 中 DATE 相减返回文本(如 '14 days')，用 DATE_PART 取天数
    v_overdue_days := DATE_PART('day', v_return_date::timestamp - p_due_date::timestamp)::INT;

    -- 从 system_config 读取每日罚款金额，默认 0.10
    -- （openGauss 的 SELECT INTO 无行时抛 NO_DATA_FOUND，需捕获后走默认值）
    v_fine_per_day := NULL;
    BEGIN
        SELECT config_value::NUMERIC(10,2)
          INTO v_fine_per_day
          FROM system_config
         WHERE config_key = 'fine_per_day';
    EXCEPTION WHEN NO_DATA_FOUND THEN
        v_fine_per_day := NULL;
    END;

    IF v_fine_per_day IS NULL THEN
        v_fine_per_day := 0.10;
    END IF;

    RETURN (v_overdue_days * v_fine_per_day);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_calculate_overdue_fine(DATE, DATE) IS '计算逾期罚款（元），从 system_config 读取罚款标准';


-- -------------------------------------------------------
-- 1.2 fn_get_user_active_borrows
--      获取用户当前在借数量（borrowed + overdue 状态）
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_get_user_active_borrows(
    p_user_id INT
) RETURNS INT
AS $$
DECLARE
    v_count INT;
BEGIN
    SELECT COUNT(*)
      INTO v_count
      FROM borrow_records
     WHERE user_id = p_user_id
       AND status IN ('borrowed', 'overdue');

    RETURN COALESCE(v_count, 0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_get_user_active_borrows(INT) IS '获取用户当前在借图书数量';


-- -------------------------------------------------------
-- 1.3 fn_get_available_stock
--      获取图书可借库存
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_get_available_stock(
    p_book_id INT
) RETURNS INT
AS $$
DECLARE
    v_stock INT;
BEGIN
    SELECT stock INTO v_stock FROM books WHERE id = p_book_id;
    RETURN COALESCE(v_stock, 0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_get_available_stock(INT) IS '获取图书可借库存数量';


-- -------------------------------------------------------
-- 1.4 fn_get_reservation_position
--      获取用户在某图书预约队列中的排队位置
--      返回 0 表示未预约或不在有效队列中
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_get_reservation_position(
    p_user_id INT,
    p_book_id INT
) RETURNS INT
AS $$
DECLARE
    v_position INT;
BEGIN
    SELECT position INTO v_position FROM (
        SELECT user_id,
               ROW_NUMBER() OVER (ORDER BY created_at ASC) AS position
          FROM reservations
         WHERE book_id = p_book_id
           AND status IN ('pending', 'ready')
    ) ranked
    WHERE user_id = p_user_id;

    RETURN COALESCE(v_position, 0);

-- openGauss 的 SELECT INTO 无行时抛 NO_DATA_FOUND，捕获后视为未排队
EXCEPTION WHEN NO_DATA_FOUND THEN
    RETURN 0;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_get_reservation_position(INT, INT) IS '获取用户在图书预约队列中的位置（0 表示未排队）';


-- -------------------------------------------------------
-- 1.5 fn_get_borrow_limit
--      根据用户角色返回最大借阅数量
--      角色映射: admin -> max_borrow_admin
--               teacher -> max_borrow_teacher
--               student -> max_borrow_student
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_get_borrow_limit(
    p_user_role VARCHAR(10)
) RETURNS INT
AS $$
DECLARE
    v_limit   INT;
    v_key_map CONSTANT VARCHAR(50) := CASE p_user_role
        WHEN 'admin'   THEN 'max_borrow_admin'
        WHEN 'teacher' THEN 'max_borrow_teacher'
        ELSE                'max_borrow_student'
    END;
BEGIN
    -- openGauss 的 SELECT INTO 无行时抛 NO_DATA_FOUND，需捕获后走默认值
    v_limit := NULL;
    BEGIN
        SELECT config_value::INT INTO v_limit
          FROM system_config
         WHERE config_key = v_key_map;
    EXCEPTION WHEN NO_DATA_FOUND THEN
        v_limit := NULL;
    END;

    RETURN COALESCE(v_limit, 5);  -- 默认 5 本
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_get_borrow_limit(VARCHAR) IS '根据用户角色获取最大借阅数量';


-- ============================================================
-- Part 2: 触发器
-- ============================================================
-- 注意：触发器与现有 ORM 服务层可能存在功能重叠。
-- 启用前请阅读 Part 4 的冲突说明，酌情调整应用层代码。
-- ============================================================

-- -------------------------------------------------------
-- 2.1 trg_before_borrow_validate
--      BEFORE INSERT on borrow_records
--      校验：用户状态、借阅额度、图书库存
--      违规时抛出异常阻止插入
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_before_borrow_validate()
RETURNS TRIGGER
AS $$
DECLARE
    v_user_status    SMALLINT;
    v_borrow_limit   INT;
    v_current_count INT;
    v_stock          INT;
    v_user_role      VARCHAR(10);
BEGIN
    -- 1) 检查用户状态（1=启用, 0=禁用）
    SELECT status, role
      INTO v_user_status, v_user_role
      FROM users
     WHERE id = NEW.user_id;

    IF v_user_status IS NULL THEN
        RAISE EXCEPTION '用户 ID % 不存在', NEW.user_id;
    END IF;

    IF v_user_status != 1 THEN
        RAISE EXCEPTION '用户 %（ID:%）已被禁用，无法借阅',
            (SELECT real_name FROM users WHERE id = NEW.user_id), NEW.user_id;
    END IF;

    -- 2) 检查是否已借阅同一本书（在借或逾期）
    IF EXISTS (
        SELECT 1 FROM borrow_records
         WHERE user_id = NEW.user_id
           AND book_id = NEW.book_id
           AND status IN ('borrowed', 'overdue')
    ) THEN
        RAISE EXCEPTION '该用户已借阅此图书，请先归还后再次借阅';
    END IF;

    -- 3) 检查借阅额度
    v_borrow_limit := fn_get_borrow_limit(v_user_role);
    v_current_count := fn_get_user_active_borrows(NEW.user_id);

    IF v_current_count >= v_borrow_limit THEN
        RAISE EXCEPTION '借阅数量已达上限（当前在借: %, 上限: %）',
            v_current_count, v_borrow_limit;
    END IF;

    -- 4) 检查库存
    v_stock := fn_get_available_stock(NEW.book_id);
    IF v_stock <= 0 THEN
        RAISE EXCEPTION '图书库存不足，当前可借: 0';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_before_borrow_validate
    BEFORE INSERT ON borrow_records
    FOR EACH ROW
    EXECUTE PROCEDURE fn_before_borrow_validate();

COMMENT ON TRIGGER trg_before_borrow_validate ON borrow_records
    IS '借阅前校验：用户状态、额度、库存';


-- -------------------------------------------------------
-- 2.2 trg_after_borrow_decrease_stock
--      AFTER INSERT on borrow_records
--      借阅成功后自动将图书 stock - 1
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_after_borrow_decrease_stock()
RETURNS TRIGGER
AS $$
BEGIN
    UPDATE books
       SET stock = GREATEST(stock - 1, 0),
           updated_at = CURRENT_TIMESTAMP
     WHERE id = NEW.book_id;

    -- 库存预警检查
    PERFORM 1 FROM system_config
     WHERE config_key = 'stock_warning_threshold'
       AND config_value::INT > 0;
    IF FOUND THEN
        -- 仅当日志记录，不阻断业务
        INSERT INTO audit_logs (
            action, resource_type, resource_id, detail,
            user_id, username, status, created_at
        ) VALUES (
            'TRIGGER_STOCK_CHECK', 'book', NEW.book_id,
            '借阅后库存检查：库存余量 ' ||
            (SELECT stock FROM books WHERE id = NEW.book_id),
            NEW.user_id,
            (SELECT username FROM users WHERE id = NEW.user_id),
            'success', CURRENT_TIMESTAMP
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_after_borrow_decrease_stock
    AFTER INSERT ON borrow_records
    FOR EACH ROW
    EXECUTE PROCEDURE fn_after_borrow_decrease_stock();

COMMENT ON TRIGGER trg_after_borrow_decrease_stock ON borrow_records
    IS '借阅后自动扣减库存，并记录库存预警审计';


-- -------------------------------------------------------
-- 2.3 trg_after_return_increase_stock
--      AFTER UPDATE on borrow_records
--      状态变更为 'returned' 时自动恢复库存 stock + 1
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_after_return_increase_stock()
RETURNS TRIGGER
AS $$
BEGIN
    -- 仅在状态首次变为 returned 时触发
    IF NEW.status = 'returned'
       AND (OLD.status IS NULL OR OLD.status != 'returned') THEN
        UPDATE books
           SET stock = stock + 1,
               updated_at = CURRENT_TIMESTAMP
         WHERE id = NEW.book_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_after_return_increase_stock
    AFTER UPDATE ON borrow_records
    FOR EACH ROW
    EXECUTE PROCEDURE fn_after_return_increase_stock();

COMMENT ON TRIGGER trg_after_return_increase_stock ON borrow_records
    IS '归还后自动恢复库存（仅在 status 变为 returned 时生效）';


-- -------------------------------------------------------
-- 2.4 trg_audit_user_role_change
--      AFTER UPDATE on users
--      自动记录角色和状态变更到审计日志
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_audit_user_role_change()
RETURNS TRIGGER
AS $$
DECLARE
    v_changes TEXT := NULL;
    v_old_json JSON;
    v_new_json JSON;
BEGIN
    -- 检测状态变更
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        v_changes := COALESCE(v_changes, '') || '状态: ' || OLD.status::text || ' -> ' || NEW.status::text || '; ';
    END IF;

    -- 检测角色变更
    IF OLD.role IS DISTINCT FROM NEW.role THEN
        v_changes := COALESCE(v_changes, '') || '角色: ' || OLD.role || ' -> ' || NEW.role || '; ';
    END IF;

    -- 有变更才记录
    IF v_changes IS NOT NULL THEN
        v_old_json := json_build_object('status', OLD.status, 'role', OLD.role);
        v_new_json := json_build_object('status', NEW.status, 'role', NEW.role);

        INSERT INTO audit_logs (
            action, resource_type, resource_id, detail,
            user_id, username, old_value, new_value,
            status, created_at
        ) VALUES (
            'TRIGGER_USER_CHANGE', 'user', NEW.id,
            RTRIM(v_changes, '; '),
            NEW.id, NEW.username,
            v_old_json, v_new_json,
            'success', CURRENT_TIMESTAMP
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_user_role_change
    AFTER UPDATE ON users
    FOR EACH ROW
    EXECUTE PROCEDURE fn_audit_user_role_change();

COMMENT ON TRIGGER trg_audit_user_role_change ON users
    IS '用户角色或状态变更时自动写入审计日志';


-- -------------------------------------------------------
-- 2.5 trg_before_reservation_check
--      BEFORE INSERT on reservations
--      校验：同一用户不可重复预约同一本书
--            预约数量不能超过上限（默认 5）
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_before_reservation_check()
RETURNS TRIGGER
AS $$
DECLARE
    v_duplicate INT;
    v_active_count INT;
    v_max_reserve INT;
BEGIN
    -- 1) 检查是否已有该书的活跃预约
    SELECT COUNT(*)
      INTO v_duplicate
      FROM reservations
     WHERE user_id = NEW.user_id
       AND book_id = NEW.book_id
       AND status IN ('pending', 'ready');

    IF v_duplicate > 0 THEN
        RAISE EXCEPTION '您已预约了该图书（ID:%），请勿重复预约', NEW.book_id;
    END IF;

    -- 2) 检查用户活跃预约总数上限
    --    （openGauss 的 SELECT INTO 无行时抛 NO_DATA_FOUND，需捕获后走默认值）
    v_max_reserve := 5;  -- 默认上限
    BEGIN
        SELECT config_value::INT INTO v_max_reserve
          FROM system_config
         WHERE config_key = 'max_reserve_count';
    EXCEPTION WHEN NO_DATA_FOUND THEN
        v_max_reserve := 5;  -- 配置缺失时使用默认值
    END;

    SELECT COUNT(*)
      INTO v_active_count
      FROM reservations
     WHERE user_id = NEW.user_id
       AND status IN ('pending', 'ready');

    IF v_active_count >= v_max_reserve THEN
        RAISE EXCEPTION '预约数量已达上限（当前: %, 上限: %）',
            v_active_count, v_max_reserve;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_before_reservation_check
    BEFORE INSERT ON reservations
    FOR EACH ROW
    EXECUTE PROCEDURE fn_before_reservation_check();

COMMENT ON TRIGGER trg_before_reservation_check ON reservations
    IS '预约前校验：重复预约检查、预约数量上限检查';


-- ============================================================
-- Part 3: 存储过程
-- ============================================================
-- 注意：
--   - 存储过程中的库存操作代码默认被注释，避免与触发器双重执行。
--   - 若不启用库存相关触发器（2.2 / 2.3），请取消对应注释。
-- ============================================================


-- -------------------------------------------------------
-- 3.1 sp_borrow_book
--      完整的借阅流程：
--        1. 校验用户状态、借阅额度、逾期罚款
--        2. 校验图书库存
--        3. 创建借阅记录
--        4. 扣减图书库存（可选，见上方说明）
--        5. 记录审计日志
--
--  参数:
--    IN  p_user_id     用户 ID
--    IN  p_book_id     图书 ID
--    IN  p_borrow_days 借阅天数（NULL 则从配置读取默认值）
--    OUT p_record_id   新建的借阅记录 ID
--    OUT p_due_date    应还日期
--    OUT p_msg         结果消息
--    OUT p_code        返回码：0=成功, -1~N=业务错误, -99=系统异常
-- -------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_borrow_book(
    p_user_id     INT,
    p_book_id     INT,
    p_borrow_days INT DEFAULT NULL,
    OUT p_record_id INT,
    OUT p_due_date  DATE,
    OUT p_msg       TEXT,
    OUT p_code      INT
)
AS
DECLARE
    v_user_status    SMALLINT;
    v_user_role      VARCHAR(10);
    v_borrow_limit   INT;
    v_current_count  INT;
    v_stock          INT;
    v_default_days   INT;
    v_unpaid_fine    NUMERIC(10,2);
    v_username       VARCHAR(50);
BEGIN
    p_code      := 0;
    p_msg       := '借阅成功';
    p_record_id := NULL;
    p_due_date  := NULL;

    -- ---- 1. 校验用户 ----
    SELECT status, role, username
      INTO v_user_status, v_user_role, v_username
      FROM users WHERE id = p_user_id;

    IF NOT FOUND THEN
        p_code := -1;
        p_msg  := '用户不存在（ID: ' || p_user_id || '）';
        RETURN;
    END IF;

    IF v_user_status != 1 THEN
        p_code := -2;
        p_msg  := '用户已被禁用，无法借阅';
        RETURN;
    END IF;

    -- ---- 2. 校验借阅额度 ----
    v_borrow_limit  := fn_get_borrow_limit(v_user_role);
    v_current_count := fn_get_user_active_borrows(p_user_id);

    IF v_current_count >= v_borrow_limit THEN
        p_code := -3;
        p_msg  := '借阅数量已达上限（当前: ' || v_current_count
                  || ', 上限: ' || v_borrow_limit || '）';
        RETURN;
    END IF;

    -- ---- 3. 校验逾期罚款（有未缴纳罚款则拒绝） ----
    SELECT COALESCE(SUM(fine), 0)
      INTO v_unpaid_fine
      FROM borrow_records
     WHERE user_id = p_user_id
       AND status IN ('borrowed', 'overdue')
       AND due_date < CURRENT_DATE;

    IF v_unpaid_fine > 0 THEN
        p_code := -4;
        p_msg  := '存在未缴纳逾期罚款（￥' || v_unpaid_fine || '），请先处理';
        RETURN;
    END IF;

    -- ---- 4. 校验图书库存 ----
    v_stock := fn_get_available_stock(p_book_id);
    IF v_stock <= 0 THEN
        p_code := -5;
        p_msg  := '图书库存不足';
        RETURN;
    END IF;

    -- ---- 5. 确定借阅天数 ----
    IF p_borrow_days IS NOT NULL THEN
        v_default_days := p_borrow_days;
    ELSE
        SELECT config_value::INT INTO v_default_days
          FROM system_config WHERE config_key = 'borrow_days';
        IF v_default_days IS NULL THEN v_default_days := 30; END IF;
    END IF;

    p_due_date := CURRENT_DATE + v_default_days;

    -- ---- 6. 创建借阅记录 ----
    INSERT INTO borrow_records (
        user_id, book_id, borrow_date, due_date, status, created_at
    ) VALUES (
        p_user_id, p_book_id, CURRENT_DATE, p_due_date, 'borrowed', CURRENT_TIMESTAMP
    ) RETURNING id INTO p_record_id;

    -- ---- 7. 扣减库存（如未启用触发器 2.2，请取消注释） ----
    -- UPDATE books
    --    SET stock = GREATEST(stock - 1, 0),
    --        updated_at = CURRENT_TIMESTAMP
    --  WHERE id = p_book_id;

    -- ---- 8. 审计日志 ----
    INSERT INTO audit_logs (
        action, resource_type, resource_id, detail,
        user_id, username, status, created_at
    ) VALUES (
        'SP_BORROW', 'borrow_record', p_record_id,
        '用户 ' || v_username || ' 借阅图书 ID ' || p_book_id
        || '，应还日期 ' || p_due_date,
        p_user_id, v_username, 'success', CURRENT_TIMESTAMP
    );

    p_msg := '借阅成功，应还日期: ' || p_due_date;

EXCEPTION WHEN OTHERS THEN
    p_code      := -99;
    p_msg       := '借阅失败: ' || SQLERRM;
    p_record_id := NULL;
    p_due_date  := NULL;
END;


-- -------------------------------------------------------
-- 3.2 sp_return_book
--      完整的归还流程：
--        1. 校验借阅记录存在性与状态
--        2. 计算逾期罚款
--        3. 更新借阅记录状态和罚款
--        4. 恢复图书库存（可选）
--        5. 记录审计日志
--
--  参数:
--    IN  p_record_id  借阅记录 ID
--    OUT p_fine        逾期罚款金额
--    OUT p_msg         结果消息
--    OUT p_code        返回码
-- -------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_return_book(
    p_record_id INT,
    OUT p_fine NUMERIC(10,2),
    OUT p_msg  TEXT,
    OUT p_code INT
)
AS
DECLARE
    v_record    RECORD;
    v_book_id   INT;
    v_book_title VARCHAR(200);
    v_username  VARCHAR(50);
BEGIN
    p_code := 0;
    p_msg  := '归还成功';
    p_fine := 0.00;

    -- ---- 1. 查询借阅记录 ----
    SELECT br.*, u.username, b.title AS book_title, b.id AS bid
      INTO v_record
      FROM borrow_records br
      JOIN users u  ON u.id  = br.user_id
      JOIN books b  ON b.id  = br.book_id
     WHERE br.id = p_record_id;

    IF NOT FOUND THEN
        p_code := -1;
        p_msg  := '借阅记录不存在（ID: ' || p_record_id || '）';
        RETURN;
    END IF;

    -- ---- 2. 状态校验 ----
    IF v_record.status NOT IN ('borrowed', 'overdue') THEN
        p_code := -2;
        p_msg  := '当前状态（' || v_record.status || '）不允许归还操作';
        RETURN;
    END IF;

    -- ---- 3. 计算罚款 ----
    p_fine := fn_calculate_overdue_fine(v_record.due_date, CURRENT_DATE);

    -- ---- 4. 更新借阅记录 ----
    v_book_id    := v_record.bid;
    v_book_title := v_record.book_title;
    v_username   := v_record.username;

    UPDATE borrow_records
       SET status     = 'returned',
           return_date = CURRENT_DATE,
           fine       = p_fine,
           created_at = created_at  -- created_at 不变
     WHERE id = p_record_id;

    -- ---- 5. 恢复库存（如未启用触发器 2.3，请取消注释） ----
    -- UPDATE books
    --    SET stock = stock + 1,
    --        updated_at = CURRENT_TIMESTAMP
    --  WHERE id = v_book_id;

    -- ---- 6. 审计日志 ----
    INSERT INTO audit_logs (
        action, resource_type, resource_id, detail,
        user_id, username, status, created_at
    ) VALUES (
        'SP_RETURN', 'borrow_record', p_record_id,
        '用户 ' || v_username || ' 归还《' || v_book_title
        || '》，罚款 ￥' || p_fine,
        v_record.user_id, v_username, 'success', CURRENT_TIMESTAMP
    );

    IF p_fine > 0 THEN
        p_msg := '归还成功，逾期罚款: ￥' || p_fine;
    ELSE
        p_msg := '归还成功，无逾期罚款';
    END IF;

EXCEPTION WHEN OTHERS THEN
    p_code := -99;
    p_msg  := '归还失败: ' || SQLERRM;
    p_fine := 0.00;
END;


-- -------------------------------------------------------
-- 3.3 sp_renew_book
--      图书续借流程：
--        1. 校验记录状态（必须为 borrowed）
--        2. 校验未逾期
--        3. 校验续借次数上限
--        4. 校验无其他用户排队预约该书
--        5. 延长应还日期
--
--  参数:
--    IN  p_record_id    借阅记录 ID
--    IN  p_renew_days   续借天数（NULL 则从配置读取）
--    OUT p_new_due_date 新应还日期
--    OUT p_msg          结果消息
--    OUT p_code         返回码
-- -------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_renew_book(
    p_record_id    INT,
    p_renew_days   INT DEFAULT NULL,
    OUT p_new_due_date DATE,
    OUT p_msg          TEXT,
    OUT p_code         INT
)
AS
DECLARE
    v_record          RECORD;
    v_max_renew       INT;
    v_default_days    INT;
    v_reserve_count   INT;
    v_book_title      VARCHAR(200);
    v_username        VARCHAR(50);
BEGIN
    p_code          := 0;
    p_msg           := '续借成功';
    p_new_due_date  := NULL;

    -- ---- 1. 查询记录 ----
    SELECT br.*, u.username, b.title AS book_title
      INTO v_record
      FROM borrow_records br
      JOIN users u ON u.id = br.user_id
      JOIN books b ON b.id = br.book_id
     WHERE br.id = p_record_id;

    IF NOT FOUND THEN
        p_code := -1;
        p_msg  := '借阅记录不存在（ID: ' || p_record_id || '）';
        RETURN;
    END IF;

    v_book_title := v_record.book_title;
    v_username   := v_record.username;

    -- ---- 2. 状态校验 ----
    IF v_record.status != 'borrowed' THEN
        p_code := -2;
        p_msg  := '当前状态（' || v_record.status || '）不允许续借';
        RETURN;
    END IF;

    -- ---- 3. 逾期不可续借 ----
    IF v_record.due_date < CURRENT_DATE THEN
        p_code := -3;
        p_msg  := '图书已逾期，请先归还后重新借阅';
        RETURN;
    END IF;

    -- ---- 4. 续借次数校验 ----
    SELECT config_value::INT INTO v_max_renew
      FROM system_config WHERE config_key = 'max_renew_count';
    IF v_max_renew IS NULL THEN v_max_renew := 2; END IF;

    IF v_record.renew_count >= v_max_renew THEN
        p_code := -4;
        p_msg  := '续借次数已达上限（' || v_max_renew || '次）';
        RETURN;
    END IF;

    -- ---- 5. 排队预约检查 ----
    SELECT COUNT(*)
      INTO v_reserve_count
      FROM reservations
     WHERE book_id = v_record.book_id
       AND status IN ('pending', 'ready');

    IF v_reserve_count > 0 THEN
        p_code := -5;
        p_msg  := '该图书有其他读者在排队预约，无法续借';
        RETURN;
    END IF;

    -- ---- 6. 计算续借天数 ----
    IF p_renew_days IS NOT NULL THEN
        v_default_days := p_renew_days;
    ELSE
        SELECT config_value::INT INTO v_default_days
          FROM system_config WHERE config_key = 'renew_days';
        IF v_default_days IS NULL THEN v_default_days := 30; END IF;
    END IF;

    p_new_due_date := v_record.due_date + v_default_days;

    -- ---- 7. 更新记录 ----
    UPDATE borrow_records
       SET due_date     = p_new_due_date,
           renew_count  = renew_count + 1,
           created_at   = created_at  -- created_at 不变
     WHERE id = p_record_id;

    -- ---- 8. 审计日志 ----
    INSERT INTO audit_logs (
        action, resource_type, resource_id, detail,
        user_id, username, status, created_at
    ) VALUES (
        'SP_RENEW', 'borrow_record', p_record_id,
        '用户 ' || v_username || ' 续借《' || v_book_title
        || '》，第 ' || (v_record.renew_count + 1)
        || ' 次续借，新到期日 ' || p_new_due_date,
        v_record.user_id, v_username, 'success', CURRENT_TIMESTAMP
    );

    p_msg := '续借成功，新应还日期: ' || p_new_due_date
             || '（第 ' || (v_record.renew_count + 1) || ' 次续借）';

EXCEPTION WHEN OTHERS THEN
    p_code         := -99;
    p_msg          := '续借失败: ' || SQLERRM;
    p_new_due_date := NULL;
END;


-- -------------------------------------------------------
-- 3.4 sp_batch_process_overdue
--      批量逾期处理（建议由定时任务调用）：
--        1. 将所有 status='borrowed' 且 due_date < 当前日期
--           的记录标记为 'overdue'
--        2. 计算并更新每条记录的罚款金额
--
--  参数:
--    OUT p_processed_count 标记为逾期的记录数
--    OUT p_total_fine      所有逾期记录的罚款总额
--    OUT p_msg             结果消息
--    OUT p_code            返回码
-- -------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_batch_process_overdue(
    OUT p_processed_count INT,
    OUT p_total_fine      NUMERIC(10,2),
    OUT p_msg             TEXT,
    OUT p_code            INT
)
AS
BEGIN
    p_code            := 0;
    p_processed_count := 0;
    p_total_fine      := 0.00;
    p_msg             := '批量逾期处理完成';

    -- 批量更新逾期状态和罚款
    UPDATE borrow_records
       SET status     = 'overdue',
           fine       = fn_calculate_overdue_fine(due_date, CURRENT_DATE)
     WHERE status = 'borrowed'
       AND due_date < CURRENT_DATE;

    GET DIAGNOSTICS p_processed_count = ROW_COUNT;

    -- 统计所有逾期记录的罚款总额
    SELECT COALESCE(SUM(fine), 0.00)
      INTO p_total_fine
      FROM borrow_records
     WHERE status = 'overdue';

    p_msg := '处理完成：标记 ' || p_processed_count || ' 条逾期记录'
             || '，累计罚款 ￥' || p_total_fine;

EXCEPTION WHEN OTHERS THEN
    p_code            := -99;
    p_msg             := '批量逾期处理失败: ' || SQLERRM;
    p_processed_count := 0;
    p_total_fine      := 0.00;
END;


-- -------------------------------------------------------
-- 3.5 sp_cleanup_expired_reservations
--      清理过期预约并通知排队读者：
--        1. 将 expiry_date < 当前日期 的 pending/ready 预约
--           标记为 expired
--        2. 对库存恢复的图书，按排队顺序将下一位预约者
--           标记为 ready（可取书）
--        3. 统计处理结果
--
--  参数:
--    OUT p_cleaned_count    过期清理数量
--    OUT p_promoted_count   推进队列数量（pending -> ready）
--    OUT p_msg              结果消息
--    OUT p_code             返回码
-- -------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_cleanup_expired_reservations(
    OUT p_cleaned_count  INT,
    OUT p_promoted_count INT,
    OUT p_msg            TEXT,
    OUT p_code           INT
)
AS
DECLARE
    v_next RECORD;
BEGIN
    p_code           := 0;
    p_cleaned_count  := 0;
    p_promoted_count := 0;
    p_msg            := '清理完成';

    -- ---- 1. 过期预约标记为 expired ----
    UPDATE reservations
       SET status       = 'expired',
           processed_at = CURRENT_TIMESTAMP
     WHERE status IN ('pending', 'ready')
       AND expiry_date IS NOT NULL
       AND expiry_date < CURRENT_TIMESTAMP;

    GET DIAGNOSTICS p_cleaned_count = ROW_COUNT;

    -- ---- 2. 检查恢复库存的图书，推进排队 ----
    FOR v_next IN
        SELECT DISTINCT ON (r.book_id)
               r.id       AS reservation_id,
               r.user_id,
               r.book_id,
               b.title    AS book_title,
               r.created_at
          FROM reservations r
          JOIN books b ON b.id = r.book_id
         WHERE r.status = 'pending'
           AND b.stock  > 0
         ORDER BY r.book_id, r.created_at ASC
    LOOP
        UPDATE reservations
           SET status       = 'ready',
               expiry_date  = CURRENT_TIMESTAMP + INTERVAL '3 days',
               processed_at = CURRENT_TIMESTAMP
         WHERE id = v_next.reservation_id;

        -- 审计记录
        INSERT INTO audit_logs (
            action, resource_type, resource_id, detail,
            user_id, username, status, created_at
        ) VALUES (
            'SP_RESERVATION_READY', 'reservation', v_next.reservation_id,
            '用户 ID ' || v_next.user_id || ' 的预约《' || v_next.book_title
            || '》已就绪，请在 3 天内到馆取书',
            v_next.user_id,
            (SELECT username FROM users WHERE id = v_next.user_id),
            'success', CURRENT_TIMESTAMP
        );

        p_promoted_count := p_promoted_count + 1;
    END LOOP;

    p_msg := '清理完成：过期 ' || p_cleaned_count
             || ' 条，推进队列 ' || p_promoted_count || ' 位';

EXCEPTION WHEN OTHERS THEN
    p_code           := -99;
    p_msg            := '清理失败: ' || SQLERRM;
    p_cleaned_count  := 0;
    p_promoted_count := 0;
END;


-- ============================================================
-- Part 4: 附注
-- ============================================================


-- -------------------------------------------------------
-- 4.1 启用 / 禁用触发器
-- -------------------------------------------------------
-- 禁用单个触发器:
--   ALTER TABLE borrow_records DISABLE TRIGGER trg_before_borrow_validate;
--   ALTER TABLE borrow_records DISABLE TRIGGER trg_after_borrow_decrease_stock;
--   ALTER TABLE borrow_records DISABLE TRIGGER trg_after_return_increase_stock;
--   ALTER TABLE users DISABLE TRIGGER trg_audit_user_role_change;
--   ALTER TABLE reservations DISABLE TRIGGER trg_before_reservation_check;
--
-- 启用单个触发器:
--   ALTER TABLE borrow_records ENABLE TRIGGER trg_before_borrow_validate;
--   ALTER TABLE borrow_records ENABLE TRIGGER trg_after_borrow_decrease_stock;
--   ALTER TABLE borrow_records ENABLE TRIGGER trg_after_return_increase_stock;
--   ALTER TABLE users ENABLE TRIGGER trg_audit_user_role_change;
--   ALTER TABLE reservations ENABLE TRIGGER trg_before_reservation_check;
--
-- 禁用某表全部触发器:
--   ALTER TABLE borrow_records DISABLE TRIGGER ALL;
--
-- 启用某表全部触发器:
--   ALTER TABLE borrow_records ENABLE TRIGGER ALL;


-- -------------------------------------------------------
-- 4.2 与应用层冲突说明
-- -------------------------------------------------------
-- 当前 Flask 应用在 Service 层已实现以下逻辑：
--   - 借阅时扣减库存 / 归还时恢复库存（borrow_service.py）
--   - 借阅额度校验
--   - 罚款计算（BorrowRecord.calculate_fine()）
--
-- 【当前实际部署状态】（应用层管理模式）：
--   已禁用:  trg_after_borrow_decrease_stock   （应用层自己扣库存）
--            trg_after_return_increase_stock   （应用层自己加库存）
--   保持启用: trg_before_borrow_validate       （双重保险，不与应用冲突）
--            trg_before_reservation_check      （预约校验，不与应用冲突）
--            trg_audit_user_role_change        （审计，不与应用冲突）
--
-- 【定时任务】：
--   job_id=1600  每日 03:00 执行 sp_cleanup_expired_reservations
--   （清理过期预约并推进排队，与应用逻辑兼容）
--   注意: sp_batch_process_overdue 未配置定时调用——应用统计接口
--   （stats.py 的 overdueCount）按 status='borrowed' + 日期判断逾期，
--   续借功能也要求 status='borrowed'，若定时把记录标记为 'overdue'
--   会导致统计遗漏和无法续借。需要时手工调用即可。
--
-- 【备选方案】:
--   [方案 A] 数据库主导方案
--     启用触发器 2.2 和 2.3，删除应用层库存管理代码
--     （borrow_service.py 中的 book.stock -= 1 / += 1），
--     让数据库保证库存一致性。
--
--   [方案 B] 使用存储过程方案
--     不启用库存相关触发器，改由应用调用存储过程，
--     取消存储过程中库存操作的注释。


-- -------------------------------------------------------
-- 4.3 依赖的系统配置键
-- -------------------------------------------------------
-- 以下配置键在 init_default_configs() 中已预置默认值：
--
--  max_borrow_student        学生最大借阅数量       默认 5
--  max_borrow_teacher        教师最大借阅数量       默认 10
--  max_borrow_admin          管理员最大借阅数量     默认 20
--  borrow_days               默认借阅天数           默认 30
--  max_renew_count           最大续借次数           默认 2
--  renew_days                每次续借天数           默认 30
--  fine_per_day              每日逾期罚款金额       默认 0.10
--  stock_warning_threshold   库存预警阈值           默认 5
--
-- 可选配置键（不存在时使用硬编码默认值）：
--  max_reserve_count         最大预约数量           默认 5


-- -------------------------------------------------------
-- 4.4 调用示例
-- -------------------------------------------------------
--
-- ---- 工具函数调用 ----
--
-- 查询函数返回值，直接 SELECT 即可：
--   SELECT fn_calculate_overdue_fine('2026-07-01', '2026-07-15');
--   -- 返回: 1.40（逾期 14 天 × 0.10 元）
--
--   SELECT fn_get_user_active_borrows(1);
--   -- 返回: 用户 1 当前在借数量
--
--   SELECT fn_get_available_stock(3);
--   -- 返回: 图书 3 的可借库存
--
--   SELECT fn_get_reservation_position(2, 5);
--   -- 返回: 用户 2 在图书 5 预约队列中的位置（0=未排队）
--
--   SELECT fn_get_borrow_limit('student');
--   -- 返回: 5
--
-- ---- 存储过程调用 ----
--
-- 借阅图书：
--   CALL sp_borrow_book(
--       p_user_id     => 1,
--       p_book_id     => 3,
--       p_borrow_days => NULL,
--       p_record_id   => NULL,
--       p_due_date    => NULL,
--       p_msg         => NULL,
--       p_code        => NULL
--   );
--
-- 归还图书：
--   CALL sp_return_book(
--       p_record_id => 10,
--       p_fine      => NULL,
--       p_msg       => NULL,
--       p_code      => NULL
--   );
--
-- 续借图书：
--   CALL sp_renew_book(
--       p_record_id    => 10,
--       p_renew_days   => NULL,
--       p_new_due_date => NULL,
--       p_msg          => NULL,
--       p_code         => NULL
--   );
--
-- 批量逾期处理（建议每日定时执行）：
--   CALL sp_batch_process_overdue(
--       p_processed_count => NULL,
--       p_total_fine      => NULL,
--       p_msg             => NULL,
--       p_code            => NULL
--   );
--
-- 清理过期预约（建议每日定时执行）：
--   CALL sp_cleanup_expired_reservations(
--       p_cleaned_count  => NULL,
--       p_promoted_count => NULL,
--       p_msg            => NULL,
--       p_code           => NULL
--   );
