-- Phase 1 creates the database only. Feature tables are added with migrations
-- in the phase that owns them.
CREATE DATABASE IF NOT EXISTS datainsight_ai
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

