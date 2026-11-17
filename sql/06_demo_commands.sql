SET NAMES utf8mb4;
USE mini_netflix;
-- Dữ liệu thực tế (không dùng TABLE_ROWS ước lượng)
SELECT 'watch_histories' AS table_name, COUNT(*) AS row_count FROM watch_histories;
SHOW TRIGGERS;
SHOW INDEX FROM watch_histories;
SELECT * FROM v_content_catalog LIMIT 20;
-- Phải trả 0 dòng:
SELECT ts.content_id,ts.total_episodes,COUNT(e.episode_id) AS actual
FROM tv_series ts LEFT JOIN episodes e ON e.content_id=ts.content_id
GROUP BY ts.content_id,ts.total_episodes HAVING total_episodes<>actual;
-- INSERT phim đầy đủ trong transaction, xem ngay rồi rollback để diễn tập.
START TRANSACTION;
INSERT INTO contents(title,content_type) VALUES('Phim bảo vệ đồ án','MOVIE');
SET @new_content=LAST_INSERT_ID();
INSERT INTO movies(content_id,video_url,duration) VALUES(@new_content,'https://example.com/demo.mp4',100);
INSERT INTO content_genres VALUES(@new_content,1);
SELECT * FROM v_content_catalog WHERE content_id=@new_content;
ROLLBACK;
-- Chạy RIÊNG câu dưới để minh họa lỗi CHECK; dữ liệu sẽ không đổi:
-- UPDATE watch_histories SET watch_progress=101 WHERE history_id=1;
