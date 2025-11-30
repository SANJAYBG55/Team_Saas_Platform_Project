@echo off
cls
echo ============================================================
echo   TEAM SAAS PLATFORM - SETUP AND START
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [1/6] Creating virtual environment...
    python -m venv venv
    echo      Virtual environment created!
) else (
    echo [1/6] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo [2/6] Activating virtual environment...
call venv\Scripts\activate.bat
echo      Virtual environment activated!
echo.

REM Install dependencies
echo [3/6] Installing dependencies (this may take a few minutes)...
pip install -q Django==5.0 djangorestframework==3.14.0 djangorestframework-simplejwt==5.3.0 PyMySQL==1.1.0 python-decouple==3.8 django-cors-headers==4.3.0 django-filter==23.3 markdown==3.5.1 bleach==6.2.0 drf-yasg==1.21.7
if %ERRORLEVEL% EQU 0 (
    echo      Dependencies installed successfully!
) else (
    echo      WARNING: Some dependencies may have failed to install
)
echo.

REM Run migrations
echo [4/6] Running database migrations...
python manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================
    echo   DATABASE ERROR!
    echo ============================================================
    echo.
    echo The database 'team_saas_db' does not exist yet.
    echo.
    echo PLEASE CREATE THE DATABASE:
    echo.
    echo Option 1: Run as MySQL root user:
    echo    mysql -u root -p
    echo    CREATE DATABASE team_saas_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    echo    GRANT ALL PRIVILEGES ON team_saas_db.* TO 'Saas_User'@'localhost';
    echo    FLUSH PRIVILEGES;
    echo    EXIT;
    echo.
    echo Option 2: Use MySQL Workbench:
    echo    1. Open MySQL Workbench
    echo    2. Run the SQL commands above
    echo.
    echo Then run this script again.
    echo ============================================================
    pause
    exit /b 1
)
echo      Migrations applied successfully!
echo.

REM Create sample data
echo [5/6] Creating sample data...
python manage.py create_sample_data
if %ERRORLEVEL% EQU 0 (
    echo      Sample data created!
) else (
    echo      Note: Sample data command may not exist yet
)
echo.

REM Start server
echo [6/6] Starting development server...
echo.
echo ============================================================
echo   SERVER STARTING
echo ============================================================
echo.
echo   API Documentation: http://localhost:8000/api/
echo   Django Admin:      http://localhost:8000/django-admin/
echo.
echo   Default Admin (after sample data):
echo   Email: admin@example.com
echo   Password: Admin@123
echo.
echo   Press CTRL+C to stop the server
echo ============================================================
echo.

python manage.py runserver
