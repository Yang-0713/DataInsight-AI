CREATE DATABASE IF NOT EXISTS datainsight_ai
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE datainsight_ai;

CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('USER', 'ADMIN') NOT NULL DEFAULT 'USER',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_username (username),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS datasets (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(512) NOT NULL,
    `rows` INT NOT NULL,
    `columns` INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_datasets_filepath (filepath),
    KEY ix_datasets_user_id (user_id),
    CONSTRAINT fk_datasets_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS analysis_results (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    dataset_id INT UNSIGNED NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    result_json JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_analysis_results_dataset_id (dataset_id),
    CONSTRAINT fk_analysis_results_dataset
        FOREIGN KEY (dataset_id) REFERENCES datasets (id)
        ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
