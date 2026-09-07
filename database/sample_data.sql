CREATE DATABASE IF NOT EXISTS mini_netflix;
USE mini_netflix;


-- USER
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status BOOLEAN DEFAULT TRUE
);


-- GÓI DỊCH VỤ
CREATE TABLE subscription_tier (
    tier_id INT AUTO_INCREMENT PRIMARY KEY,
    tier_name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    duration_days INT DEFAULT 30,
    max_profiles INT NOT NULL,
    max_devices INT NOT NULL,
    video_quality VARCHAR(20) NOT NULL
);


-- ĐĂNG KÝ GÓI
CREATE TABLE subscription (
    subscription_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    tier_id INT NOT NULL,
    start_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date DATETIME NOT NULL,
    status BOOLEAN DEFAULT TRUE,
    auto_renew BOOLEAN DEFAULT FALSE,

    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (tier_id) REFERENCES subscription_tier(tier_id)
);


-- PROFILE
CREATE TABLE profile (
    profile_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    profile_name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    age_limit INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id)
);


-- CONTENT: thông tin chung của Movie và Episode
CREATE TABLE content (
    content_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    release_date DATE,
    duration INT CHECK (duration > 0),
    age_rating VARCHAR(20),
    thumbnail_url VARCHAR(500),
    video_url VARCHAR(1000)
);


-- TV SERIES
CREATE TABLE tv_series (
    series_id INT AUTO_INCREMENT PRIMARY KEY,
    series_title VARCHAR(255) NOT NULL,
    description TEXT,
    release_year INT,
    status VARCHAR(50),
    age_rating VARCHAR(10),
    thumbnail_url VARCHAR(500)
);


-- MOVIE là một CONTENT
CREATE TABLE movie (
    content_id INT PRIMARY KEY,
    movie_type VARCHAR(50),

    FOREIGN KEY (content_id)
        REFERENCES content(content_id)
        ON DELETE CASCADE
);


-- EPISODE là một CONTENT và thuộc TV SERIES
CREATE TABLE episode (
    content_id INT PRIMARY KEY,
    series_id INT NOT NULL,
    season_number INT NOT NULL CHECK (season_number > 0),
    episode_number INT NOT NULL CHECK (episode_number > 0),

    FOREIGN KEY (content_id)
        REFERENCES content(content_id)
        ON DELETE CASCADE,

    FOREIGN KEY (series_id)
        REFERENCES tv_series(series_id)
        ON DELETE CASCADE,

    UNIQUE (series_id, season_number, episode_number)
);


-- LỊCH SỬ XEM
CREATE TABLE watch_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    profile_id INT NOT NULL,
    content_id INT NOT NULL,
    watched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    progress_seconds INT DEFAULT 0 CHECK (progress_seconds >= 0),
    completed BOOLEAN DEFAULT FALSE,

    FOREIGN KEY (profile_id)
        REFERENCES profile(profile_id)
        ON DELETE CASCADE,

    FOREIGN KEY (content_id)
        REFERENCES content(content_id)
        ON DELETE CASCADE
);


-- DANH SÁCH XEM SAU
CREATE TABLE watchlist (
    profile_id INT NOT NULL,
    content_id INT NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (profile_id, content_id),

    FOREIGN KEY (profile_id)
        REFERENCES profile(profile_id)
        ON DELETE CASCADE,

    FOREIGN KEY (content_id)
        REFERENCES content(content_id)
        ON DELETE CASCADE
);


-- ĐÁNH GIÁ
CREATE TABLE rating (
    rating_id INT AUTO_INCREMENT PRIMARY KEY,
    profile_id INT NOT NULL,
    content_id INT NOT NULL,
    score INT NOT NULL CHECK (score BETWEEN 1 AND 5),
    review VARCHAR(1000),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (profile_id) REFERENCES profile(profile_id),
    FOREIGN KEY (content_id) REFERENCES content(content_id),

    UNIQUE (profile_id, content_id)
);


-- THỂ LOẠI
CREATE TABLE genre (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    genre_name VARCHAR(100) NOT NULL,
    description TEXT
);


-- CONTENT - GENRE
CREATE TABLE content_genre (
    content_id INT NOT NULL,
    genre_id INT NOT NULL,

    PRIMARY KEY (content_id, genre_id),

    FOREIGN KEY (content_id)
        REFERENCES content(content_id)
        ON DELETE CASCADE,

    FOREIGN KEY (genre_id)
        REFERENCES genre(genre_id)
        ON DELETE CASCADE
);


-- DIỄN VIÊN
CREATE TABLE actor (
    actor_id INT AUTO_INCREMENT PRIMARY KEY,
    actor_name VARCHAR(255) NOT NULL,
    date_of_birth DATE,
    nationality VARCHAR(100),
    biography TEXT,
    photo_url VARCHAR(500)
);


-- CONTENT - ACTOR
CREATE TABLE content_actor (
    content_id INT NOT NULL,
    actor_id INT NOT NULL,
    character_name VARCHAR(255),

    PRIMARY KEY (content_id, actor_id),

    FOREIGN KEY (content_id)
        REFERENCES content(content_id)
        ON DELETE CASCADE,

    FOREIGN KEY (actor_id)
        REFERENCES actor(actor_id)
        ON DELETE CASCADE
);
