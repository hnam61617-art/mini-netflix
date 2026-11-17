SET NAMES utf8mb4;
USE mini_netflix;

-- Q1 Lọc phim theo thể loại và ngày phát hành
SET @genre_id = 1;
SET @from_date = '2025-01-01';
SET @to_date = '2026-01-01';
SELECT c.content_id, c.title, c.content_type, c.date_released
FROM contents AS c
WHERE c.content_type = 'MOVIE'
  AND c.date_released >= @from_date
  AND c.date_released < @to_date
  AND EXISTS (
      SELECT 1 FROM content_genres AS cg
      WHERE cg.content_id = c.content_id AND cg.genre_id = @genre_id
  )
ORDER BY c.date_released DESC, c.content_id DESC
LIMIT 20;

-- Q2 Doanh thu theo tháng và mức tăng trưởng
WITH monthly AS (
    SELECT DATE_FORMAT(history_payment, '%Y-%m-01') AS month_start,
           SUM(prices) AS revenue
    FROM payments
    WHERE history_payment >= '2025-01-01'
      AND history_payment < '2026-01-01'
    GROUP BY DATE_FORMAT(history_payment, '%Y-%m-01')
), compared AS (
    SELECT month_start, revenue,
           LAG(month_start) OVER (ORDER BY month_start) AS previous_month,
           LAG(revenue) OVER (ORDER BY month_start) AS previous_revenue
    FROM monthly
)
SELECT month_start, revenue,
       CASE WHEN TIMESTAMPDIFF(MONTH, previous_month, month_start) = 1
            THEN ROUND(100.0 * (revenue - previous_revenue)
                       / NULLIF(previous_revenue, 0), 2)
       END AS growth_percent
FROM compared ORDER BY month_start;

-- Q3 Xếp hạng nội dung theo số hồ sơ đã xem
WITH audience AS (
    SELECT COALESCE(wh.content_id, e.content_id) AS content_id,
           COUNT(DISTINCT wh.profile_id) AS viewer_profiles
    FROM watch_histories AS wh
    LEFT JOIN episodes AS e ON e.episode_id = wh.episode_id
    WHERE wh.watch_progress > 0
    GROUP BY COALESCE(wh.content_id, e.content_id)
), ranked AS (
    SELECT c.content_id, c.title, a.viewer_profiles,
           DENSE_RANK() OVER (ORDER BY a.viewer_profiles DESC) AS rank_no
    FROM audience AS a
    JOIN contents AS c ON c.content_id = a.content_id
)
SELECT content_id, title, viewer_profiles, rank_no
FROM ranked WHERE rank_no <= 10
ORDER BY rank_no, content_id;

-- Q4 Tiến độ hoàn thành phim bộ của một hồ sơ
SET @profile_id = 1;
SELECT c.content_id, c.title, ec.episode_count,
       COALESCE(sp.completed_episodes, 0) AS completed_episodes,
       ROUND(100.0 * COALESCE(sp.completed_episodes, 0)
             / NULLIF(ec.episode_count, 0), 2) AS completed_percent,
       (ec.episode_count > 0
        AND COALESCE(sp.completed_episodes, 0) = ec.episode_count)
           AS is_completed
FROM v_episode_counts AS ec
JOIN contents AS c ON c.content_id = ec.content_id
LEFT JOIN v_series_progress AS sp
       ON sp.content_id = ec.content_id AND sp.profile_id = @profile_id
WHERE EXISTS (SELECT 1 FROM profiles WHERE profile_id = @profile_id)
ORDER BY c.content_id;

-- Q5 Danh sách xem sau chưa hoàn thành
SELECT c.content_id, c.title, c.content_type, wl.added_at
FROM watch_lists AS wl
JOIN contents AS c ON c.content_id = wl.content_id
LEFT JOIN watch_histories AS wh
       ON wh.profile_id = wl.profile_id
      AND wh.content_id = wl.content_id AND wh.episode_id IS NULL
LEFT JOIN v_episode_counts AS ec ON ec.content_id = c.content_id
LEFT JOIN v_series_progress AS sp
       ON sp.profile_id = wl.profile_id AND sp.content_id = c.content_id
WHERE wl.profile_id = @profile_id
  AND (
      (c.content_type = 'MOVIE'
       AND COALESCE(wh.watch_progress, 0) < 90)
      OR
      (c.content_type = 'TV_SERIES'
       AND (ec.episode_count = 0
            OR COALESCE(sp.completed_episodes, 0) < ec.episode_count))
  )
ORDER BY wl.added_at DESC, c.content_id;

-- Q6 Các lượt đăng ký cần xử lý hết hạn
SELECT subscription_id, user_id, end_date, auto_renew
FROM subscriptions
WHERE status = 'ACTIVE' AND end_date <= CURRENT_TIMESTAMP
ORDER BY end_date, subscription_id
LIMIT 100;

-- Q7 Doanh thu theo loại gói
SELECT t.tier_id, t.tier_name,
       COUNT(p.payment_id) AS payment_count,
       COALESCE(SUM(p.prices), 0) AS revenue
FROM subscription_tiers AS t
LEFT JOIN subscriptions AS s ON s.tier_id = t.tier_id
LEFT JOIN payments AS p
       ON p.subscription_id = s.subscription_id
      AND p.history_payment >= '2025-01-01'
      AND p.history_payment < '2026-01-01'
GROUP BY t.tier_id, t.tier_name
ORDER BY revenue DESC, t.tier_id;

-- Q8 Hồ sơ đã bắt đầu xem mọi nội dung của một thể loại
SET @genre_id = 1;
SELECT p.profile_id, p.profile_name
FROM profiles AS p
WHERE EXISTS (
    SELECT 1 FROM content_genres WHERE genre_id = @genre_id
)
AND NOT EXISTS (
    SELECT 1 FROM content_genres AS cg
    WHERE cg.genre_id = @genre_id
      AND NOT EXISTS (
          SELECT 1 FROM watch_histories AS wh
          LEFT JOIN episodes AS e ON e.episode_id = wh.episode_id
          WHERE wh.profile_id = p.profile_id AND wh.watch_progress > 0
            AND COALESCE(wh.content_id, e.content_id) = cg.content_id
      )
)
ORDER BY p.profile_id;

-- Q9 Top 3 nội dung theo số hồ sơ xem trong từng thể loại
WITH audience AS (
    SELECT COALESCE(wh.content_id, e.content_id) AS content_id,
           COUNT(DISTINCT wh.profile_id) AS viewer_profiles
    FROM watch_histories AS wh
    LEFT JOIN episodes AS e ON e.episode_id = wh.episode_id
    WHERE wh.watch_progress > 0
    GROUP BY COALESCE(wh.content_id, e.content_id)
), ranked AS (
    SELECT g.genre_name, c.content_id, c.title,
           COALESCE(a.viewer_profiles, 0) AS viewer_profiles,
           DENSE_RANK() OVER (
               PARTITION BY g.genre_id
               ORDER BY COALESCE(a.viewer_profiles, 0) DESC
           ) AS rank_no
    FROM genres AS g
    JOIN content_genres AS cg ON cg.genre_id = g.genre_id
    JOIN contents AS c ON c.content_id = cg.content_id
    LEFT JOIN audience AS a ON a.content_id = c.content_id
)
SELECT genre_name, content_id, title, viewer_profiles, rank_no
FROM ranked WHERE rank_no <= 3
ORDER BY genre_name, rank_no, content_id;

-- Q10 Tài khoản còn gói nhưng không xem trong 30 ngày gần nhất
SELECT s.user_id, s.subscription_id, s.tier_name, s.end_date
FROM v_active_subscriptions AS s
WHERE NOT EXISTS (
    SELECT 1 FROM profiles AS p
    JOIN watch_histories AS wh ON wh.profile_id = p.profile_id
    WHERE p.user_id = s.user_id
      AND wh.watch_progress > 0
      AND wh.last_watch_at >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 30 DAY)
      AND wh.last_watch_at <= CURRENT_TIMESTAMP
)
ORDER BY s.user_id;