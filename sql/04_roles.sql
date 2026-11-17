SET NAMES utf8mb4;
USE mini_netflix;
CREATE ROLE 'mn_app', 'mn_catalog', 'mn_report', 'mn_retention';

GRANT SELECT, INSERT ON mini_netflix.users TO 'mn_app';
GRANT UPDATE (email, phone, password_hash, full_name)
ON mini_netflix.users TO 'mn_app';
GRANT SELECT, INSERT, DELETE ON mini_netflix.profiles TO 'mn_app';
GRANT UPDATE (profile_name, avatar_url)
ON mini_netflix.profiles TO 'mn_app';
GRANT SELECT ON mini_netflix.subscription_tiers TO 'mn_app';
GRANT SELECT, INSERT ON mini_netflix.subscriptions TO 'mn_app';
GRANT UPDATE (start_date, end_date, auto_renew, status)
ON mini_netflix.subscriptions TO 'mn_app';
GRANT SELECT, INSERT ON mini_netflix.payments TO 'mn_app';
GRANT SELECT, INSERT, DELETE ON mini_netflix.watch_lists TO 'mn_app';
GRANT SELECT, INSERT ON mini_netflix.watch_histories TO 'mn_app';
GRANT UPDATE (watch_progress, last_watch_at)
ON mini_netflix.watch_histories TO 'mn_app';
GRANT EXECUTE ON PROCEDURE mini_netflix.sp_renew_subscription TO 'mn_app';

GRANT SELECT ON mini_netflix.contents TO 'mn_app';

GRANT SELECT ON mini_netflix.movies TO 'mn_app';

GRANT SELECT ON mini_netflix.tv_series TO 'mn_app';

GRANT SELECT ON mini_netflix.episodes TO 'mn_app';

GRANT SELECT ON mini_netflix.genres TO 'mn_app';

GRANT SELECT ON mini_netflix.content_genres TO 'mn_app';

GRANT SELECT ON mini_netflix.v_active_subscriptions TO 'mn_app';

GRANT SELECT ON mini_netflix.v_episode_counts TO 'mn_app';

GRANT SELECT ON mini_netflix.v_series_progress TO 'mn_app';

GRANT SELECT ON mini_netflix.v_content_catalog TO 'mn_app';

GRANT SELECT, INSERT, DELETE ON mini_netflix.contents TO 'mn_catalog';
GRANT UPDATE (title, description, date_released)
ON mini_netflix.contents TO 'mn_catalog';
GRANT SELECT ON mini_netflix.movies TO 'mn_catalog';
GRANT INSERT (content_id, video_url, duration), UPDATE (video_url, duration)
ON mini_netflix.movies TO 'mn_catalog';
GRANT SELECT, INSERT (content_id)
ON mini_netflix.tv_series TO 'mn_catalog';
GRANT SELECT, INSERT, DELETE ON mini_netflix.episodes TO 'mn_catalog';
GRANT UPDATE (content_id, episode_number, title, duration, video_url, date_released)
ON mini_netflix.episodes TO 'mn_catalog';
GRANT SELECT, INSERT, DELETE ON mini_netflix.genres TO 'mn_catalog';
GRANT UPDATE (genre_name) ON mini_netflix.genres TO 'mn_catalog';
GRANT SELECT, INSERT, DELETE ON mini_netflix.content_genres TO 'mn_catalog';
GRANT SELECT ON mini_netflix.v_content_catalog TO 'mn_catalog';
GRANT SELECT ON mini_netflix.v_episode_counts TO 'mn_catalog';

GRANT SELECT (profile_id, user_id, profile_name)
ON mini_netflix.profiles TO 'mn_report';

GRANT SELECT (subscription_id, user_id, tier_id, start_date, end_date, auto_renew, status)
ON mini_netflix.subscriptions TO 'mn_report';

GRANT SELECT (tier_id, tier_name, prices, max_profile, max_device, video_quality)
ON mini_netflix.subscription_tiers TO 'mn_report';

GRANT SELECT (payment_id, subscription_id, prices, history_payment)
ON mini_netflix.payments TO 'mn_report';

GRANT SELECT (history_id, profile_id, content_id, episode_id, last_watch_at, watch_progress)
ON mini_netflix.watch_histories TO 'mn_report';

GRANT SELECT ON mini_netflix.contents TO 'mn_report';

GRANT SELECT ON mini_netflix.movies TO 'mn_report';

GRANT SELECT ON mini_netflix.tv_series TO 'mn_report';

GRANT SELECT ON mini_netflix.episodes TO 'mn_report';

GRANT SELECT ON mini_netflix.genres TO 'mn_report';

GRANT SELECT ON mini_netflix.content_genres TO 'mn_report';

GRANT SELECT ON mini_netflix.v_active_subscriptions TO 'mn_report';

GRANT SELECT ON mini_netflix.v_episode_counts TO 'mn_report';

GRANT SELECT ON mini_netflix.v_series_progress TO 'mn_report';

GRANT SELECT ON mini_netflix.v_content_catalog TO 'mn_report';

GRANT SELECT, DELETE ON mini_netflix.payments TO 'mn_retention';

GRANT SELECT ON mini_netflix.watch_lists TO 'mn_report';
