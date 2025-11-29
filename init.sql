-- Initialize database schema
-- This file runs automatically when MySQL container starts for the first time

USE Team_Saas_Platform;

-- Grant permissions
GRANT ALL PRIVILEGES ON Team_Saas_Platform.* TO 'Saas_User'@'%';
FLUSH PRIVILEGES;

-- Set timezone
SET GLOBAL time_zone = '+00:00';

-- Set character set
ALTER DATABASE Team_Saas_Platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
