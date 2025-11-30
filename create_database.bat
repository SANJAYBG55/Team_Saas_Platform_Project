@echo off
REM Batch script to create Team_Saas_Platform database
REM Run this script as administrator or with MySQL root access

echo ============================================
echo Creating Team_Saas_Platform Database
echo ============================================
echo.

REM Prompt for MySQL root password
set /p MYSQL_ROOT_PASS="Enter MySQL root password: "

echo.
echo Creating database and granting privileges...
echo.

mysql -u root -p%MYSQL_ROOT_PASS% -e "CREATE DATABASE IF NOT EXISTS Team_Saas_Platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL PRIVILEGES ON Team_Saas_Platform.* TO 'Saas_User'@'localhost'; FLUSH PRIVILEGES; SHOW DATABASES LIKE 'Team_Saas_Platform';"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo SUCCESS! Database created successfully!
    echo ============================================
    echo.
    echo You can now run: python manage.py migrate
    echo.
) else (
    echo.
    echo ============================================
    echo ERROR! Failed to create database
    echo ============================================
    echo.
    echo Please check your MySQL root password and try again
    echo Or manually run: create_database.sql
    echo.
)

pause
