-- You're already logged into MySQL as root!
-- Just copy and paste these commands one by one:

CREATE DATABASE IF NOT EXISTS team_saas_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON team_saas_db.* TO 'Saas_User'@'localhost';

FLUSH PRIVILEGES;

SHOW DATABASES LIKE 'team_saas%';

-- You should see: team_saas_db

-- Then type: exit

-- After that, run in PowerShell: python manage.py migrate
