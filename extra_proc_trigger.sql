-- =============================================
-- 1、存储过程1：proc_borrow_book 处理借书记录
-- =============================================
CREATE OR REPLACE PROCEDURE proc_borrow_book(
    IN p_user_id INT,
    IN p_book_id INT,
    IN p_borrow_date TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- 新增借书记录
    INSERT INTO borrow_record(user_id, book_id, borrow_time)
    VALUES(p_user_id, p_book_id, p_borrow_date);

    -- 更新图书可借数量（模拟）
    UPDATE book
    SET stock = stock - 1
    WHERE id = p_book_id;

END;
$$;

-- =============================================
-- 2、存储过程2：proc_return_book 处理还书
-- =============================================
CREATE OR REPLACE PROCEDURE proc_return_book(
    IN p_record_id INT,
    IN p_return_date TIMESTAMP
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_book_id INT;
BEGIN
    -- 获取图书ID
    SELECT book_id INTO v_book_id FROM borrow_record WHERE id = p_record_id;

    -- 更新归还时间
    UPDATE borrow_record
    SET return_time = p_return_date
    WHERE id = p_record_id;

    -- 归还，库存+1
    UPDATE book
    SET stock = stock + 1
    WHERE id = v_book_id;

END;
$$;


-- =============================================
-- 触发器1：trig_before_borrow 借书前校验库存
-- 函数：trig_func_before_borrow
-- =============================================
CREATE OR REPLACE FUNCTION trig_func_before_borrow()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_stock INT;
BEGIN
    SELECT stock INTO v_stock FROM book WHERE id = NEW.book_id;
    IF v_stock <= 0 THEN
        RAISE EXCEPTION '图书库存不足，无法借阅';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trig_before_borrow ON borrow_record;
CREATE TRIGGER trig_before_borrow
BEFORE INSERT ON borrow_record
FOR EACH ROW
EXECUTE FUNCTION trig_func_before_borrow();


-- =============================================
-- 触发器2：trig_after_return 还书之后生成操作日志
-- 函数：trig_func_after_return
-- =============================================
-- 先建简单操作日志表（脚本顺带创建，不存在就新建）
CREATE TABLE IF NOT EXISTS operate_log(
    id SERIAL PRIMARY KEY,
    operate_type VARCHAR(50),
    operate_msg TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION trig_func_after_return()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- 当return_time由null变为有值，代表完成还书
    IF OLD.return_time IS NULL AND NEW.return_time IS NOT NULL THEN
        INSERT INTO operate_log(operate_type,operate_msg)
        VALUES('还书操作',CONCAT('记录id:',NEW.id,',图书id:',NEW.book_id,'完成归还'));
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trig_after_return ON borrow_record;
CREATE TRIGGER trig_after_return
AFTER UPDATE ON borrow_record
FOR EACH ROW
EXECUTE FUNCTION trig_func_after_return();