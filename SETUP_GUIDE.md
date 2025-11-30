# 🚀 STEP-BY-STEP SETUP GUIDE

Follow these exact steps to get your SaaS platform running.

---

## ✅ PREREQUISITES

Before starting, ensure you have:
- ✅ Python 3.9+ installed
- ✅ MySQL 8.0+ installed and running
- ✅ pip (Python package manager)
- ✅ Git (optional, for version control)

---

## 📋 STEP 1: VERIFY PROJECT LOCATION

```powershell
# Open PowerShell and navigate to project
cd "c:\ABSP\Django Projects\Team_Saas_Platform_Project"

# Verify you're in the right directory
ls
# You should see: config/, apps/, templates/, manage.py, requirements.txt, etc.
```

---

## 📋 STEP 2: CREATE MYSQL DATABASE

### Option A: Using MySQL Command Line

```powershell
# Open MySQL command line
mysql -u root -p
# Enter your MySQL root password when prompted
```

```sql
-- Inside MySQL, run these commands:
CREATE DATABASE Team_Saas_Platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'Saas_User'@'localhost' IDENTIFIED BY 'Saas@123';
GRANT ALL PRIVILEGES ON Team_Saas_Platform.* TO 'Saas_User'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Option B: Using MySQL Workbench

1. Open MySQL Workbench
2. Click on your local connection
3. Click the "SQL" tab
4. Copy and paste the SQL commands from Option A
5. Click Execute (⚡ icon)

### Verify Database Creation

```powershell
mysql -u Saas_User -pSaas@123
```

```sql
SHOW DATABASES;
USE Team_Saas_Platform;
EXIT;
```

You should see `Team_Saas_Platform` in the list.

---

## 📋 STEP 3: CREATE PYTHON VIRTUAL ENVIRONMENT

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Your prompt should now show (venv) at the beginning
# Example: (venv) PS C:\ABSP\Django Projects\Team_Saas_Platform_Project>
```

---

## 📋 STEP 4: INSTALL DEPENDENCIES

```powershell
# Upgrade pip first (recommended)
python -m pip install --upgrade pip

# Install all project dependencies
pip install -r requirements.txt

# This will install ~20 packages including:
# - Django
# - djangorestframework
# - mysqlclient
# - JWT libraries
# - etc.

# Wait for installation to complete (2-5 minutes)
```

### If you get errors:

**Error: "Microsoft Visual C++ 14.0 is required"**
- Download and install: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Or use: `pip install mysqlclient‑1.4.6‑cp39‑cp39‑win_amd64.whl` (pre-built wheel)

**Error: "mysqlclient installation failed"**
```powershell
# Try installing build dependencies first:
pip install wheel
pip install mysqlclient
```

---

## 📋 STEP 5: CREATE ENVIRONMENT FILE

```powershell
# Copy the example environment file
copy .env.example .env

# Verify the file was created
ls .env
```

The .env file already has the correct database credentials:
```
DB_NAME=Team_Saas_Platform
DB_USER=Saas_User
DB_PASSWORD=Saas@123
DB_HOST=localhost
DB_PORT=3306
```

**No changes needed unless you used different database credentials.**

---

## 📋 STEP 6: RUN DATABASE MIGRATIONS

```powershell
# Create migration files (if not already exist)
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate

# You should see output like:
# Operations to perform:
#   Apply all migrations: accounts, admin, auth, contenttypes, core, notifications, sessions, subscriptions, tasks, teams, tenants
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   ... (many more)
```

### Expected Output:
- ✅ About 30-40 migrations will be applied
- ✅ All should say "OK"
- ✅ No errors should appear

### If you get errors:

**Error: "Access denied for user"**
- Check your .env file has correct DB_USER and DB_PASSWORD
- Verify the user exists in MySQL

**Error: "Unknown database"**
- Make sure you created the database in Step 2
- Database name must be exactly: `Team_Saas_Platform`

---

## 📋 STEP 7: VERIFY PROJECT SETUP

```powershell
# Run the verification command
python manage.py verify_project

# This will check:
# - Database connection
# - Installed apps
# - Models registration
# - Migration status
# - Current statistics
```

### Expected Output:
```
======================================================================
  TEAM SAAS PLATFORM - PROJECT VERIFICATION
======================================================================

1. Database Connection...
   ✅ Connected to MySQL: 8.0.x

2. Installed Apps...
   ✅ apps.accounts
   ✅ apps.tenants
   ✅ apps.subscriptions
   ✅ apps.teams
   ✅ apps.tasks
   ✅ apps.notifications
   ✅ apps.admin_panel
   ✅ apps.core

3. Database Models...
   ✅ 25 models registered

4. Migrations Status...
   ✅ All migrations applied

5. Current Statistics...
   • Users: 0
   • Tenants: 0
   • Plans: 0
   • Subscriptions: 0
   • Payments: 0
   • Teams: 0
   • Tasks: 0

======================================================================
  OVERALL COMPLETION: 70-75%
======================================================================

✅ Backend is 90% complete and fully functional!
```

---

## 📋 STEP 8: CREATE SAMPLE DATA

```powershell
# Generate sample data for testing
python manage.py create_sample_data

# This creates:
# - 4 subscription plans (Free, Starter, Professional, Enterprise)
# - 1 Super Admin (admin@example.com / Admin@123)
# - 3 Tenants with users, teams, and tasks
```

### Expected Output:
```
Creating sample data...

Creating subscription plans...
Creating super admin...
Creating sample tenants...
Creating users...
Creating teams...
Creating tasks...
Creating system settings...

Sample data created successfully!

Super Admin: admin@example.com / Admin@123
Tenant Admins: Check the created tenants
```

---

## 📋 STEP 9: RUN DEVELOPMENT SERVER

```powershell
# Start the Django development server
python manage.py runserver

# You should see:
# Watching for file changes with StatReloader
# Performing system checks...
#
# System check identified no issues (0 silenced).
# November 30, 2025 - 10:30:00
# Django version 4.2.7, using settings 'config.settings'
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CTRL-BREAK.
```

### ✅ SUCCESS! Your server is now running.

**Keep this terminal window open.** The server must be running to access the application.

---

## 📋 STEP 10: ACCESS THE APPLICATION

Open your web browser and visit:

### Django Admin Panel
**URL:** http://localhost:8000/django-admin/
**Login:** admin@example.com
**Password:** Admin@123

**What you can do:**
- View all database records
- Manage users, tenants, subscriptions
- Approve pending tenants
- Verify payments

### API Documentation
**URL:** http://localhost:8000/api/

**Available endpoints:**
- http://localhost:8000/api/auth/
- http://localhost:8000/api/tenants/
- http://localhost:8000/api/subscriptions/
- http://localhost:8000/api/teams/
- http://localhost:8000/api/tasks/
- http://localhost:8000/api/notifications/

---

## 📋 STEP 11: TEST THE API

### Option A: Using Browser (Simple Test)

Visit: http://localhost:8000/api/subscriptions/plans/

You should see JSON data with 4 subscription plans.

### Option B: Using Postman (Recommended)

1. **Download Postman:** https://www.postman.com/downloads/

2. **Test Login:**
   ```
   POST http://localhost:8000/api/auth/login/
   Headers:
     Content-Type: application/json
   Body (raw JSON):
   {
       "email": "admin@acme.com",
       "password": "Password@123"
   }
   ```

3. **Expected Response:**
   ```json
   {
       "message": "Login successful",
       "user": {
           "id": 2,
           "email": "admin@acme.com",
           "first_name": "Acme Corporation",
           "role": "TENANT_ADMIN",
           ...
       },
       "tokens": {
           "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
           "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
       }
   }
   ```

4. **Use Access Token for Authenticated Requests:**
   ```
   GET http://localhost:8000/api/teams/
   Headers:
     Authorization: Bearer <your_access_token>
   ```

### Option C: Using curl

```powershell
# Test login
curl -X POST http://localhost:8000/api/auth/login/ `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"admin@acme.com\",\"password\":\"Password@123\"}'

# Test plans endpoint
curl http://localhost:8000/api/subscriptions/plans/
```

---

## 📋 STEP 12: EXPLORE SAMPLE DATA

After creating sample data, you have:

### Test Accounts:

**Super Admin (Full Platform Access):**
- Email: admin@example.com
- Password: Admin@123
- Can approve tenants, verify payments, view all data

**Tenant 1: Acme Corporation (ACTIVE)**
- Admin: admin@acme.com / Password@123
- Plan: Starter ($29/month)
- Users: 6 (1 admin, 2 managers, 3 members)
- Teams: 3 (Development, Design, Marketing)
- Tasks: 15 total (5 per team)

**Tenant 2: Tech Innovators (ACTIVE)**
- Admin: admin@techinnovators.com / Password@123
- Plan: Professional ($99/month)
- Users: 6 (1 admin, 2 managers, 3 members)
- Teams: 3 (Development, Design, Marketing)
- Tasks: 15 total (5 per team)

**Tenant 3: Startup Demo (PENDING APPROVAL)**
- Admin: admin@startupdemo.com / Password@123
- Status: Waiting for admin approval
- Plan: Free

### Subscription Plans:
1. **Free** - $0/month (5 users, 2 teams, 5 projects)
2. **Starter** - $29/month (10 users, 5 teams, 20 projects) ⭐ Popular
3. **Professional** - $99/month (50 users, 20 teams, 100 projects)
4. **Enterprise** - $299/month (Unlimited)

---

## 📋 STEP 13: COMMON TASKS

### View all tenants (Super Admin):
```
GET http://localhost:8000/api/tenants/
Authorization: Bearer <super_admin_token>
```

### Approve a tenant:
```
POST http://localhost:8000/api/tenants/3/approve/
Authorization: Bearer <super_admin_token>
Body: { "notes": "Approved for testing" }
```

### View your teams (Tenant Admin/User):
```
GET http://localhost:8000/api/teams/
Authorization: Bearer <tenant_user_token>
```

### Create a new team:
```
POST http://localhost:8000/api/teams/
Authorization: Bearer <tenant_admin_token>
Body: {
    "name": "New Team",
    "description": "Team description",
    "is_private": false
}
```

### View subscription plans:
```
GET http://localhost:8000/api/subscriptions/plans/
(No authentication required)
```

---

## 🎯 WHAT TO DO NEXT

### 1. Explore the API
- Test all endpoints using Postman
- Try creating users, teams, tasks
- Test payment submission and verification
- Experiment with tenant approval workflow

### 2. Read Documentation
- **README.md** - Project overview
- **QUICK_START.md** - Quick start guide
- **ARCHITECTURE.md** - System architecture
- **COMPLETE_SUMMARY.md** - Full summary
- **IMPLEMENTATION_STATUS.md** - Feature status

### 3. Customize the System
- Modify subscription plans
- Add custom fields to models
- Create additional API endpoints
- Build frontend templates

### 4. Deploy to Production
- Follow **DEPLOYMENT.md** for production setup
- Configure proper database
- Set up HTTPS
- Configure email service

---

## 🛠️ TROUBLESHOOTING

### Problem: Server won't start
```powershell
# Check if port 8000 is already in use
netstat -ano | findstr :8000

# If in use, kill the process or use different port:
python manage.py runserver 8080
```

### Problem: Database connection error
```powershell
# Test database connection manually:
mysql -u Saas_User -pSaas@123 Team_Saas_Platform

# If fails, recreate the user:
mysql -u root -p
DROP USER 'Saas_User'@'localhost';
CREATE USER 'Saas_User'@'localhost' IDENTIFIED BY 'Saas@123';
GRANT ALL PRIVILEGES ON Team_Saas_Platform.* TO 'Saas_User'@'localhost';
```

### Problem: Module not found error
```powershell
# Reinstall requirements:
pip install -r requirements.txt --force-reinstall
```

### Problem: Migration conflicts
```powershell
# Reset migrations (WARNING: Deletes all data):
python manage.py migrate --fake-initial
python manage.py makemigrations
python manage.py migrate
python manage.py create_sample_data
```

---

## 📞 ADDITIONAL COMMANDS

```powershell
# Create a superuser manually
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Open Django shell
python manage.py shell

# Run tests
python manage.py test

# Check for issues
python manage.py check

# Show migrations
python manage.py showmigrations

# Verify project status
python manage.py verify_project
```

---

## ✅ SUCCESS CHECKLIST

- ✅ MySQL database created
- ✅ Virtual environment activated
- ✅ Dependencies installed
- ✅ Environment file created
- ✅ Migrations applied
- ✅ Sample data created
- ✅ Server running
- ✅ Can access Django admin
- ✅ API endpoints responding
- ✅ Can login with test accounts

---

## 🎉 CONGRATULATIONS!

Your SaaS platform is now running successfully!

**Next Steps:**
1. Explore the API endpoints
2. Test tenant approval workflow
3. Try payment verification
4. Build a frontend (React/Vue) or use the API directly
5. Deploy to production when ready

**Happy coding! 🚀**
