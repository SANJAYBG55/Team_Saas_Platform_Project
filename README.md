# Team SaaS Platform

A comprehensive multi-tenant SaaS platform built with Django, featuring team collaboration, task management, subscription billing, and admin controls.

## 🚀 Features

### Software A - Admin Panel (Company Control Panel)
- **Dashboard**: Tenant overview, statistics, and analytics
- **Tenant Management**: Approve, suspend, or manage tenants
- **Payment Verification**: Manual payment verification system
- **Billing Monitor**: Track subscriptions and invoices
- **Reports & Analytics**: Comprehensive reporting dashboard
- **Admin Users & Roles**: Internal staff management
- **Audit Logs**: Complete activity tracking

### Software B - Tenant App (Tasks + Teams + Billing)
- **Team Management**: Create teams, invite members
- **Task Management**: Kanban board, list view, calendar view
- **Collaboration**: Comments, attachments, mentions
- **Billing & Subscriptions**: Plan management, payment tracking
- **Notifications**: Real-time notifications system
- **User Profiles**: Customizable user settings
- **Dark Mode**: Theme toggle support

## 🏗️ Architecture

```
Team_Saas_Platform_Project/
├── config/                 # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
├── apps/
│   ├── accounts/          # User authentication & management
│   ├── tenants/           # Multi-tenancy support
│   ├── subscriptions/     # Billing & payments
│   ├── teams/             # Team management
│   ├── tasks/             # Task management
│   ├── notifications/     # Notification system
│   ├── admin_panel/       # Admin panel features
│   └── core/              # Core utilities & middleware
├── templates/
│   ├── base.html
│   ├── layouts/
│   ├── components/
│   ├── public/
│   ├── admin/
│   └── tenant/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── media/                 # User uploaded files
├── logs/                  # Application logs
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── manage.py
```

## 📋 Prerequisites

- Python 3.11+
- MySQL 8.0+
- Redis 7.0+ (optional, for caching and Celery)
- Docker & Docker Compose (optional, for containerized deployment)

## 🔧 Installation

### Option 1: Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd Team_Saas_Platform_Project
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
copy .env.example .env
# Edit .env with your configuration
```

5. **Create MySQL database**
```sql
CREATE DATABASE Team_Saas_Platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'Saas_User'@'localhost' IDENTIFIED BY 'Saas@123';
GRANT ALL PRIVILEGES ON Team_Saas_Platform.* TO 'Saas_User'@'localhost';
FLUSH PRIVILEGES;
```

6. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Create superuser**
```bash
python manage.py createsuperuser
```

8. **Collect static files**
```bash
python manage.py collectstatic
```

9. **Run development server**
```bash
python manage.py runserver
```

### Option 2: Docker Deployment

1. **Clone the repository**
```bash
git clone <repository-url>
cd Team_Saas_Platform_Project
```

2. **Create .env file**
```bash
copy .env.example .env
# Edit .env with your configuration
```

3. **Build and run with Docker Compose**
```bash
docker-compose up -d --build
```

4. **Run migrations**
```bash
docker-compose exec web python manage.py migrate
```

5. **Create superuser**
```bash
docker-compose exec web python manage.py createsuperuser
```

6. **Access the application**
- Web: http://localhost:8000
- Admin: http://localhost:8000/django-admin/

## 📊 Database Schema

### Core Models

- **User**: Custom user model with role-based access
- **Tenant**: Multi-tenant organization model
- **Domain**: Domain/subdomain mapping
- **Subscription**: Subscription management
- **Plan**: Pricing plans with features
- **Payment**: Payment tracking and verification
- **Invoice**: Billing and invoicing
- **Team**: Team organization
- **TeamMember**: Team membership
- **Task**: Task management
- **Comment**: Task comments
- **Attachment**: File attachments
- **Notification**: User notifications
- **ActivityLog**: Global activity tracking
- **AuditLog**: Admin action auditing

## 🔐 Security Features

- CSRF protection
- SQL injection prevention (ORM)
- XSS protection
- Secure password hashing (PBKDF2)
- Session security
- Rate limiting (optional)
- Role-based access control
- Tenant isolation

## 🎨 UI/UX Features

- Responsive design (mobile-first)
- Dark mode support
- Keyboard shortcuts
- Toast notifications
- Loading states & skeletons
- Empty states
- Modal dialogs
- Accessible (WCAG AA)

## 📱 API Endpoints

### Authentication
- POST `/api/auth/register/` - Register new user
- POST `/api/auth/login/` - User login
- POST `/api/auth/logout/` - User logout
- GET/PATCH `/api/auth/profile/` - User profile
- POST `/api/auth/change-password/` - Change password
- GET/PATCH `/api/auth/preferences/` - User preferences

### Tenants
- GET `/api/tenants/` - List tenants (admin)
- POST `/api/tenants/` - Create tenant
- GET `/api/tenants/{id}/` - Tenant details
- PATCH `/api/tenants/{id}/` - Update tenant
- POST `/api/tenants/{id}/approve/` - Approve tenant

### Teams
- GET `/api/teams/` - List teams
- POST `/api/teams/` - Create team
- GET `/api/teams/{id}/` - Team details
- PATCH `/api/teams/{id}/` - Update team
- DELETE `/api/teams/{id}/` - Delete team

### Tasks
- GET `/api/tasks/` - List tasks
- POST `/api/tasks/` - Create task
- GET `/api/tasks/{id}/` - Task details
- PATCH `/api/tasks/{id}/` - Update task
- DELETE `/api/tasks/{id}/` - Delete task

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 📈 Monitoring & Logging

Logs are stored in the `logs/` directory:
- `django.log` - Application logs
- Activity logs in database
- Audit logs for admin actions

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in settings
- [ ] Update `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Setup proper database credentials
- [ ] Configure email settings
- [ ] Enable HTTPS/SSL
- [ ] Setup static file serving (Nginx/CDN)
- [ ] Configure backup strategy
- [ ] Setup monitoring (Sentry, etc.)
- [ ] Enable security headers
- [ ] Setup rate limiting

### Recommended Stack

- **Web Server**: Nginx
- **WSGI Server**: Gunicorn
- **Database**: MySQL 8.0+
- **Cache**: Redis
- **Task Queue**: Celery
- **Monitoring**: Sentry, Prometheus
- **Hosting**: AWS, DigitalOcean, or similar

## 🔧 Configuration

### Environment Variables

See `.env.example` for all available environment variables.

Key variables:
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `EMAIL_HOST` - SMTP host
- `REDIS_URL` - Redis connection URL

## 📝 License

This project is proprietary software. All rights reserved.

## 👥 Contributors

- Development Team

## 📧 Support

For support, email support@example.com or create an issue in the repository.

## 🗺️ Roadmap

- [ ] REST API documentation (Swagger/OpenAPI)
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Integration with third-party services
- [ ] AI-powered task suggestions
- [ ] Video calling integration
- [ ] Advanced reporting
- [ ] Multi-language support

## 📚 Documentation

Additional documentation:
- [API Documentation](docs/api.md)
- [User Guide](docs/user-guide.md)
- [Admin Guide](docs/admin-guide.md)
- [Developer Guide](docs/developer-guide.md)

---

Built with ❤️ using Django
