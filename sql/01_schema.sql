CREATE DATABASE mini_netflix
CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE mini_netflix;
SET NAMES utf8mb4;
SET SESSION time_zone = '+00:00';
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(10) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT uq_users_phone UNIQUE (phone),
    CONSTRAINT chk_users_email CHECK (
        email = TRIM(email) AND email REGEXP '^[A-Za-z0-9._%+-]+@gmail[.]com$'
    ),
    CONSTRAINT chk_users_phone CHECK (phone REGEXP '^[0-9]{10}$'),
    CONSTRAINT chk_users_name CHECK (CHAR_LENGTH(TRIM(full_name)) > 0),
    CONSTRAINT chk_users_password CHECK (CHAR_LENGTH(TRIM(password_hash)) > 0)
) ENGINE=InnoDB;

CREATE TABLE profiles (
    profile_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    profile_name VARCHAR(50) NOT NULL,
    avatar_url VARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_profiles_name CHECK (CHAR_LENGTH(TRIM(profile_name)) > 0),
    CONSTRAINT fk_profiles_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE subscription_tiers (
    tier_id INT AUTO_INCREMENT PRIMARY KEY,
    tier_name VARCHAR(50) NOT NULL,
    prices DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    max_profile INT NOT NULL DEFAULT 1,
    max_device INT NOT NULL DEFAULT 1,
    video_quality VARCHAR(10) COLLATE utf8mb4_0900_as_cs NOT NULL DEFAULT 'SD',
    CONSTRAINT uq_tiers_name UNIQUE (tier_name),
    CONSTRAINT chk_tiers_price CHECK (prices >= 0),
    CONSTRAINT chk_tiers_profiles CHECK (max_profile >= 1),
    CONSTRAINT chk_tiers_devices CHECK (max_device >= 1),
    CONSTRAINT chk_tiers_quality CHECK (video_quality IN ('SD','HD','4K')),
    CONSTRAINT chk_tiers_name CHECK (CHAR_LENGTH(TRIM(tier_name)) > 0)
) ENGINE=InnoDB;

CREATE TABLE subscriptions (
    subscription_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    tier_id INT NOT NULL,
    start_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date DATETIME NOT NULL,
    auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(10) COLLATE utf8mb4_0900_as_cs NOT NULL,
    CONSTRAINT chk_subscriptions_auto CHECK (auto_renew IN (0, 1)),
    CONSTRAINT chk_subscriptions_dates CHECK (end_date > start_date),
    CONSTRAINT chk_subscriptions_status CHECK (status IN ('ACTIVE','CANCELED','EXPIRED')),
    CONSTRAINT fk_subscriptions_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_subscriptions_tier FOREIGN KEY (tier_id)
        REFERENCES subscription_tiers(tier_id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    subscription_id INT NOT NULL,
    prices DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    transaction_method VARCHAR(30) NOT NULL,
    history_payment DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_payments_price CHECK (prices >= 0),
    CONSTRAINT chk_payments_method CHECK (CHAR_LENGTH(TRIM(transaction_method)) > 0),
    CONSTRAINT fk_payments_subscription FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(subscription_id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE contents (
    content_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    date_released DATE NULL,
    content_type VARCHAR(10) COLLATE utf8mb4_0900_as_cs NOT NULL,
    CONSTRAINT chk_contents_title CHECK (CHAR_LENGTH(TRIM(title)) > 0),
    CONSTRAINT chk_contents_type CHECK (content_type IN ('MOVIE','TV_SERIES'))
) ENGINE=InnoDB;

CREATE TABLE movies (
    content_id INT PRIMARY KEY,
    video_url VARCHAR(500) NOT NULL,
    duration INT NOT NULL,
    CONSTRAINT chk_movies_url CHECK (CHAR_LENGTH(TRIM(video_url)) > 0),
    CONSTRAINT chk_movies_duration CHECK (duration > 0),
    CONSTRAINT fk_movies_content FOREIGN KEY (content_id)
        REFERENCES contents(content_id) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE tv_series (
    content_id INT PRIMARY KEY,
    total_episodes INT NOT NULL DEFAULT 0,
    CONSTRAINT chk_series_episodes CHECK (total_episodes >= 0),
    CONSTRAINT fk_series_content FOREIGN KEY (content_id)
        REFERENCES contents(content_id) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE episodes (
    episode_id INT AUTO_INCREMENT PRIMARY KEY,
    content_id INT NOT NULL,
    episode_number INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    duration INT NOT NULL,
    video_url VARCHAR(500) NOT NULL,
    date_released DATE NULL,
    CONSTRAINT uq_episode_number UNIQUE (content_id, episode_number),
    CONSTRAINT chk_episode_number CHECK (episode_number > 0),
    CONSTRAINT chk_episode_title CHECK (CHAR_LENGTH(TRIM(title)) > 0),
    CONSTRAINT chk_episode_duration CHECK (duration > 0),
    CONSTRAINT chk_episode_url CHECK (CHAR_LENGTH(TRIM(video_url)) > 0),
    CONSTRAINT fk_episodes_series FOREIGN KEY (content_id)
        REFERENCES tv_series(content_id) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE genres (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    genre_name VARCHAR(50) NOT NULL,
    CONSTRAINT uq_genres_name UNIQUE (genre_name),
    CONSTRAINT chk_genres_name CHECK (CHAR_LENGTH(TRIM(genre_name)) > 0)
) ENGINE=InnoDB;

CREATE TABLE content_genres (
    content_id INT NOT NULL,
    genre_id INT NOT NULL,
    PRIMARY KEY (content_id, genre_id),
    CONSTRAINT fk_content_genres_content FOREIGN KEY (content_id)
        REFERENCES contents(content_id) ON DELETE CASCADE ON UPDATE RESTRICT,
    CONSTRAINT fk_content_genres_genre FOREIGN KEY (genre_id)
        REFERENCES genres(genre_id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE watch_lists (
    profile_id INT NOT NULL,
    content_id INT NOT NULL,
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (profile_id, content_id),
    CONSTRAINT fk_watch_lists_profile FOREIGN KEY (profile_id)
        REFERENCES profiles(profile_id) ON DELETE CASCADE ON UPDATE RESTRICT,
    CONSTRAINT fk_watch_lists_content FOREIGN KEY (content_id)
        REFERENCES contents(content_id) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE watch_histories (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    profile_id INT NOT NULL,
    content_id INT NULL,
    episode_id INT NULL,
    last_watch_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    watch_progress DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT chk_watch_progress CHECK (watch_progress BETWEEN 0 AND 100),
    CONSTRAINT chk_history_target CHECK (
        (content_id IS NOT NULL AND episode_id IS NULL)
        OR (content_id IS NULL AND episode_id IS NOT NULL)
    ),
    CONSTRAINT fk_watch_histories_profile FOREIGN KEY (profile_id)
        REFERENCES profiles(profile_id) ON DELETE CASCADE ON UPDATE RESTRICT,
    CONSTRAINT fk_watch_histories_content FOREIGN KEY (content_id)
        REFERENCES movies(content_id) ON DELETE CASCADE ON UPDATE RESTRICT,
    CONSTRAINT fk_watch_histories_episode FOREIGN KEY (episode_id)
        REFERENCES episodes(episode_id) ON DELETE CASCADE ON UPDATE RESTRICT,
    UNIQUE KEY uq_history_profile_movie (profile_id, content_id),
    UNIQUE KEY uq_history_profile_episode (profile_id, episode_id)
) ENGINE=InnoDB;

CREATE OR REPLACE SQL SECURITY INVOKER VIEW v_active_subscriptions
AS
SELECT s.subscription_id, s.user_id, s.tier_id, t.tier_name,
       s.start_date, s.end_date, s.auto_renew,
       t.max_profile, t.max_device, t.video_quality
FROM subscriptions AS s
JOIN subscription_tiers AS t ON t.tier_id = s.tier_id
WHERE s.status = 'ACTIVE'
  AND s.start_date <= CURRENT_TIMESTAMP
  AND s.end_date > CURRENT_TIMESTAMP;
 
CREATE OR REPLACE SQL SECURITY INVOKER VIEW v_episode_counts AS
SELECT ts.content_id, COUNT(e.episode_id) AS episode_count
FROM tv_series AS ts
LEFT JOIN episodes AS e ON e.content_id = ts.content_id
GROUP BY ts.content_id;
 
CREATE OR REPLACE SQL SECURITY INVOKER VIEW v_series_progress AS
SELECT wh.profile_id, e.content_id,
       COUNT(*) AS started_episodes,
       SUM(wh.watch_progress >= 90) AS completed_episodes
FROM watch_histories AS wh
JOIN episodes AS e ON e.episode_id = wh.episode_id
GROUP BY wh.profile_id, e.content_id;
 
CREATE OR REPLACE SQL SECURITY INVOKER VIEW v_content_catalog AS
SELECT c.content_id, c.title, c.date_released, c.content_type,
       m.duration AS movie_duration,
       ts.total_episodes,
       GROUP_CONCAT(g.genre_name ORDER BY g.genre_name
                    SEPARATOR ', ') AS genre_names
FROM contents AS c
LEFT JOIN movies AS m ON m.content_id = c.content_id
LEFT JOIN tv_series AS ts ON ts.content_id = c.content_id
LEFT JOIN content_genres AS cg ON cg.content_id = c.content_id
LEFT JOIN genres AS g ON g.genre_id = cg.genre_id
GROUP BY c.content_id, c.title, c.date_released,
         c.content_type, m.duration, ts.total_episodes;
CREATE INDEX idx_subscriptions_user_status_end
ON subscriptions (user_id, status, end_date);
 
CREATE INDEX idx_subscriptions_end_renew
    ON subscriptions (end_date, auto_renew, status);
 
CREATE INDEX idx_payments_subscription_date
    ON payments (subscription_id, history_payment);
 
CREATE INDEX idx_payments_date
    ON payments (history_payment);
 
CREATE INDEX idx_contents_type_release
    ON contents (content_type, date_released);
 
CREATE INDEX idx_contents_title
    ON contents (title);
 
CREATE INDEX idx_content_genres_genre
    ON content_genres (genre_id, content_id);
 
CREATE INDEX idx_watch_lists_content
    ON watch_lists (content_id, profile_id);
 
CREATE INDEX idx_history_profile_lastwatch
    ON watch_histories (profile_id, last_watch_at);
 
CREATE INDEX idx_history_content
    ON watch_histories (content_id);
 

DELIMITER $$
CREATE TRIGGER bi_movies_type
BEFORE INSERT ON movies
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM contents
        WHERE content_id = NEW.content_id
          AND content_type = 'MOVIE'
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Content type does not match subtype';
    END IF;
END$$

CREATE TRIGGER bu_movies_type
BEFORE UPDATE ON movies
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM contents
        WHERE content_id = NEW.content_id
          AND content_type = 'MOVIE'
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Content type does not match subtype';
    END IF;
END$$

CREATE TRIGGER bd_movies_parent
BEFORE DELETE ON movies
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM contents WHERE content_id = OLD.content_id) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Delete content through contents table';
    END IF;
END$$

CREATE TRIGGER bi_tv_series_type
BEFORE INSERT ON tv_series
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM contents
        WHERE content_id = NEW.content_id
          AND content_type = 'TV_SERIES'
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Content type does not match subtype';
    END IF;
END$$

CREATE TRIGGER bu_tv_series_type
BEFORE UPDATE ON tv_series
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM contents
        WHERE content_id = NEW.content_id
          AND content_type = 'TV_SERIES'
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Content type does not match subtype';
    END IF;
END$$

CREATE TRIGGER bd_tv_series_parent
BEFORE DELETE ON tv_series
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM contents WHERE content_id = OLD.content_id) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Delete content through contents table';
    END IF;
END$$

CREATE TRIGGER bu_users_id
BEFORE UPDATE ON users
FOR EACH ROW
BEGIN
    IF NEW.user_id <> OLD.user_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'user_id is immutable';
    END IF;
END$$

CREATE TRIGGER bu_payments_immutable
BEFORE UPDATE ON payments
FOR EACH ROW
BEGIN
    IF NEW.payment_id <> OLD.payment_id
       OR NEW.subscription_id <> OLD.subscription_id
       OR NEW.prices <> OLD.prices
       OR NEW.history_payment <> OLD.history_payment
       OR BINARY NEW.transaction_method <> BINARY OLD.transaction_method THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Recorded payments are immutable';
    END IF;
END$$

CREATE TRIGGER bd_payments_retention
BEFORE DELETE ON payments
FOR EACH ROW
BEGIN
    IF CURRENT_TIMESTAMP < DATE_ADD(OLD.history_payment, INTERVAL 6 MONTH) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Payment retention period has not ended';
    END IF;
END$$

CREATE TRIGGER bu_watch_histories_time
BEFORE UPDATE ON watch_histories
FOR EACH ROW
BEGIN
    IF NEW.watch_progress <> OLD.watch_progress THEN
        SET NEW.last_watch_at = CURRENT_TIMESTAMP;
    END IF;
END$$

CREATE TRIGGER ai_episodes_count
AFTER INSERT ON episodes
FOR EACH ROW
BEGIN
    UPDATE tv_series
    SET total_episodes = total_episodes + 1
    WHERE content_id = NEW.content_id;
END$$

CREATE TRIGGER ad_episodes_count
AFTER DELETE ON episodes
FOR EACH ROW
BEGIN
    UPDATE tv_series
    SET total_episodes = total_episodes - 1
    WHERE content_id = OLD.content_id;
END$$

CREATE TRIGGER au_episodes_move
AFTER UPDATE ON episodes
FOR EACH ROW
BEGIN
    IF NEW.content_id <> OLD.content_id THEN
        UPDATE tv_series
        SET total_episodes = total_episodes - 1
        WHERE content_id = OLD.content_id;
        UPDATE tv_series
        SET total_episodes = total_episodes + 1
        WHERE content_id = NEW.content_id;
    END IF;
END$$
 
DELIMITER ;
DELIMITER $$
CREATE PROCEDURE sp_renew_subscription
(
    IN p_user_id INT,
    IN p_subscription_id INT,
    IN p_expected_end DATETIME,
    IN p_is_automatic BOOLEAN,
    IN p_payment_ok BOOLEAN,
    IN p_method VARCHAR(30)
)
SQL SECURITY INVOKER
main: BEGIN
    DECLARE v_user INT DEFAULT NULL;
    DECLARE v_tier INT DEFAULT NULL;
    DECLARE v_start DATETIME;
    DECLARE v_end DATETIME;
    DECLARE v_now DATETIME;
    DECLARE v_status VARCHAR(10);
    DECLARE v_auto BOOLEAN;
    DECLARE v_price DECIMAL(10,2);
    DECLARE v_limit INT;
    DECLARE v_profiles INT;
    DECLARE v_other INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
 
    START TRANSACTION;
    SELECT user_id INTO v_user
    FROM users WHERE user_id = p_user_id FOR UPDATE;
    IF v_user IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Unknown user';
    END IF;
    SELECT tier_id, start_date, end_date, status, auto_renew
      INTO v_tier, v_start, v_end, v_status, v_auto
    FROM subscriptions
    WHERE subscription_id = p_subscription_id AND user_id = p_user_id
    FOR UPDATE;
    IF v_tier IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Unknown subscription';
    END IF;
    SET v_now = CURRENT_TIMESTAMP;
    IF p_expected_end IS NULL OR p_expected_end <> v_end
       OR v_status <> 'ACTIVE' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stale renewal request';
    END IF;
    IF p_is_automatic IS NULL OR p_is_automatic NOT IN (0, 1)
       OR p_payment_ok IS NULL OR p_payment_ok NOT IN (0, 1) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid simulation flag';
    END IF;
    IF v_start > v_now THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Subscription not started';
    END IF;
    IF p_is_automatic = TRUE THEN
        IF v_end > v_now THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Not due for renewal';
        END IF;
        IF v_auto = FALSE THEN
            UPDATE subscriptions SET status = 'EXPIRED'
            WHERE subscription_id = p_subscription_id;
            COMMIT;
            LEAVE main;
        END IF;
        IF p_payment_ok = FALSE THEN
            UPDATE subscriptions SET status = 'CANCELED'
            WHERE subscription_id = p_subscription_id;
            COMMIT;
            LEAVE main;
        END IF;
    ELSEIF p_payment_ok = FALSE THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Simulated payment failed';
    END IF;
    IF p_method IS NULL OR CHAR_LENGTH(TRIM(p_method)) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Payment method required';
    END IF;
    SELECT COUNT(*) INTO v_other
    FROM subscriptions
    WHERE user_id = p_user_id AND subscription_id <> p_subscription_id
      AND status = 'ACTIVE' AND start_date <
          DATE_ADD(GREATEST(v_end, v_now), INTERVAL 30 DAY)
      AND end_date > v_now;
    IF v_other > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Overlapping subscription';
    END IF;
    SELECT prices, max_profile INTO v_price, v_limit
    FROM subscription_tiers WHERE tier_id = v_tier FOR SHARE;
    SELECT COUNT(*) INTO v_profiles
    FROM profiles WHERE user_id = p_user_id;
    IF v_profiles > v_limit THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Profile limit exceeded';
    END IF;
    INSERT INTO payments
        (subscription_id, prices, transaction_method, history_payment)
    VALUES (p_subscription_id, v_price, p_method, v_now);
    UPDATE subscriptions
    SET start_date = IF(v_end <= v_now, v_now, v_start),
        end_date = DATE_ADD(GREATEST(v_end, v_now), INTERVAL 30 DAY),
        status = 'ACTIVE'
    WHERE subscription_id = p_subscription_id;
    COMMIT;
END$$
DELIMITER ;