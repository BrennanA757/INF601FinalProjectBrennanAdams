DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS ratings;

CREATE TABLE user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    volume_id CHAR NOT NULL,
    author_id INTEGER NOT NULL,
    author_name CHAR NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    body TEXT NOT NULL,
    FOREIGN KEY (author_id) REFERENCES user (customerID)
);

CREATE TABLE ratings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ratings TEXT,
    users_who_have_set_ratings TEXT,
    volume_id TEXT NOT NULL UNIQUE
);