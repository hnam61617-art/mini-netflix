SET NAMES utf8mb4;
USE mini_netflix;
-- Tìm riêng phim theo tên, không tải toàn bộ movies.
SELECT content_id,title,content_type,movie_duration,genre_names
FROM v_content_catalog WHERE title LIKE '%Extraction%';
-- Lọc thể loại và loại phim; không lọc ngày khi nguồn chỉ có năm.
SET @genre_id=1;
SELECT c.content_id,c.title,c.date_released,m.duration
FROM contents c JOIN movies m ON m.content_id=c.content_id
WHERE EXISTS(SELECT 1 FROM content_genres cg WHERE cg.content_id=c.content_id AND cg.genre_id=@genre_id)
ORDER BY c.content_id LIMIT 20;
-- Tài khoản/hồ sơ là dữ liệu mô phỏng, không phải khách hàng Netflix.
SELECT user_id,full_name,email,phone FROM users WHERE email='student001@gmail.com';
SELECT p.profile_id,p.profile_name,u.full_name FROM profiles p
JOIN users u ON u.user_id=p.user_id WHERE u.email='student001@gmail.com';
-- Phải trả 0 dòng: trigger đếm tập khớp số tập được nạp, không phải số mùa CSV.
SELECT s.content_id,s.total_episodes,COUNT(e.episode_id) AS actual
FROM tv_series s LEFT JOIN episodes e ON e.content_id=s.content_id
GROUP BY s.content_id,s.total_episodes HAVING s.total_episodes<>actual;
