-- ============================================================
-- 图书管理系统 - 评价/评分 触发器与存储过程
--
-- 数据库: book_manager (openGauss 6.x / PostgreSQL 兼容)
-- 字符集: UTF-8
--
-- 说明
-- ============================================================
--  本文件为「评价/评分」功能在 PostgreSQL / openGauss 下的数据库层实现，
--  与《借阅》模块（triggers_and_procedures.sql）保持一致的设计哲学：
--
--    · 应用层（Python 服务层 review_service.add_review）是主逻辑，
--      始终负责写入 book_reviews 并维护 books.avg_rating / review_count；
--    · 本文件的触发器作为「数据一致性补充 / 双保险」——
--      当有人绕过应用层直接 INSERT/UPDATE/DELETE book_reviews 时，
--      也能自动同步图书聚合评分，避免评分失真。
--
--  注意：本地 SQLite 运行模式不执行本文件（语法不兼容），
--        评分聚合完全由应用层 review_service 维护，功能等价。
--
-- 目录
-- ============================================================
--  Part 1: 触发器 (Triggers)
--    1.1 trg_after_review_maintain_rating  评价增删改后自动维护图书评分
--  Part 2: 存储过程 (Stored Procedures)
--    2.1 sp_recalculate_book_rating        重算（单本或全部）图书评分
-- ============================================================


-- ============================================================
-- Part 1: 触发器
-- ============================================================

-- -------------------------------------------------------
-- 1.1 trg_after_review_maintain_rating
--      在 book_reviews 发生 INSERT / UPDATE / DELETE 后，
--      自动重算并更新对应图书的 avg_rating 与 review_count。
--      逻辑与 review_service._recalculate() 保持一致。
-- -------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_maintain_book_rating()
RETURNS TRIGGER
AS $$
DECLARE
    v_book_id INT;
BEGIN
    -- DELETE 时取 OLD，其余取 NEW
    IF TG_OP = 'DELETE' THEN
        v_book_id := OLD.book_id;
    ELSE
        v_book_id := NEW.book_id;
    END IF;

    UPDATE books
       SET avg_rating = (
               SELECT COALESCE(ROUND(AVG(rating)::numeric, 2), 0)
                 FROM book_reviews
                WHERE book_id = v_book_id
           ),
           review_count = (
               SELECT COUNT(*) FROM book_reviews WHERE book_id = v_book_id
           )
     WHERE id = v_book_id;

    RETURN NULL;  -- AFTER 行级触发器返回 NULL 即可
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_maintain_book_rating() IS '评价增删改后自动维护图书平均评分与评价数';


CREATE TRIGGER trg_after_review_maintain_rating
    AFTER INSERT OR UPDATE OR DELETE ON book_reviews
    FOR EACH ROW
    EXECUTE FUNCTION fn_maintain_book_rating();

COMMENT ON TRIGGER trg_after_review_maintain_rating ON book_reviews
    IS '评价变更后同步图书聚合评分（与应用层双保险）';


-- ============================================================
-- Part 2: 存储过程
-- ============================================================

-- -------------------------------------------------------
-- 2.1 sp_recalculate_book_rating
--      重算图书评分。
--        p_book_id 为 NULL 时，重算全部图书（用于数据修复/初始化）；
--        指定 p_book_id 时，仅重算该图书。
--      逻辑与 fn_maintain_book_rating / review_service._recalculate 一致。
-- -------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_recalculate_book_rating(
    p_book_id INT DEFAULT NULL
)
AS $$
DECLARE
    r RECORD;
BEGIN
    IF p_book_id IS NULL THEN
        FOR r IN SELECT id FROM books LOOP
            UPDATE books b
               SET avg_rating = (
                       SELECT COALESCE(ROUND(AVG(rating)::numeric, 2), 0)
                         FROM book_reviews
                        WHERE book_id = b.id
                   ),
                   review_count = (
                       SELECT COUNT(*) FROM book_reviews WHERE book_id = b.id
                   )
             WHERE b.id = r.id;
        END LOOP;
    ELSE
        UPDATE books
           SET avg_rating = (
                   SELECT COALESCE(ROUND(AVG(rating)::numeric, 2), 0)
                     FROM book_reviews
                    WHERE book_id = p_book_id
               ),
               review_count = (
                   SELECT COUNT(*) FROM book_reviews WHERE book_id = p_book_id
               )
         WHERE id = p_book_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON PROCEDURE sp_recalculate_book_rating(INT) IS '重算图书平均评分与评价数（单本或全部）';


-- ============================================================
-- 启用/禁用指南
-- ============================================================
--  本文件对象默认创建后即生效。如需临时停用触发器：
--      ALTER TABLE book_reviews DISABLE TRIGGER trg_after_review_maintain_rating;
--  重新启用：
--      ALTER TABLE book_reviews ENABLE  TRIGGER trg_after_review_maintain_rating;
--
--  手动重算全部图书评分（数据修复）：
--      CALL sp_recalculate_book_rating(NULL);
--  重算指定图书：
--      CALL sp_recalculate_book_rating(1);
-- ============================================================
