-- SQL script to create the database for Team SaaS Platform
-- Run this as MySQL root user

-- Create database
CREATE DATABASE IF NOT EXISTS Team_Saas_Platform 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Grant all privileges to existing Saas_User
GRANT ALL PRIVILEGES ON Team_Saas_Platform.* TO 'Saas_User'@'localhost';
FLUSH PRIVILEGES;

-- Verify the database was created
SHOW DATABASES LIKE 'Team_Saas_Platform';

-- Show current privileges for Saas_User
SHOW GRANTS FOR 'Saas_User'@'localhost';
