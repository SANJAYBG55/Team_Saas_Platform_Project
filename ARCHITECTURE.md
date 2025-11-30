# 🏗️ SYSTEM ARCHITECTURE DOCUMENTATION

## OVERVIEW

This is a complete **Multi-Tenant SaaS Platform** built with Django + MySQL, featuring two distinct software systems:

1. **Software A**: Company Control Panel (Admin System)
2. **Software B**: Tenant Application (Customer System)

---

## 📊 HIGH-LEVEL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                         USERS / CLIENTS                          │
└─────────────┬───────────────────────────────────┬────────────────┘
              │                                   │
              │ (HTTP/HTTPS)                      │ (HTTP/HTTPS)
              ▼                                   ▼
┌─────────────────────────┐         ┌────────────────────────────┐
│   ADMIN PANEL PORTAL    │         │   TENANT APP PORTAL        │
│   (Software A)          │         │   (Software B)             │
│   /admin/               │         │   /app/                    │
└────────────┬────────────┘         └────────────┬───────────────┘
             │                                   │
             └───────────────┬───────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │     DJANGO APPLICATION       │
              │                              │
              │  ┌────────────────────────┐  │
              │  │   URL Router           │  │
              │  │   /api/...             │  │
              │  └──────────┬─────────────┘  │
              │             │                │
              │  ┌──────────▼─────────────┐  │
              │  │   Middleware Layer     │  │
              │  │  - TenantMiddleware    │  │
              │  │  - ApprovalMiddleware  │  │
              │  │  - ActivityMiddleware  │  │
              │  └──────────┬─────────────┘  │
              │             │                │
              │  ┌──────────▼─────────────┐  │
              │  │   Views & ViewSets     │  │
              │  │  - API Endpoints       │  │
              │  │  - Business Logic      │  │
              │  └──────────┬─────────────┘  │
              │             │                │
              │  ┌──────────▼─────────────┐  │
              │  │   Serializers          │  │
              │  │  - Validation          │  │
              │  │  - Data Transform      │  │
              │  └──────────┬─────────────┘  │
              │             │                │
              │  ┌──────────▼─────────────┐  │
              │  │   Models (ORM)         │  │
              │  │  - Business Objects    │  │
              │  └──────────┬─────────────┘  │
              └─────────────┼────────────────┘
                            │
                            ▼
              ┌──────────────────────────────┐
              │   MySQL DATABASE             │
              │   Team_Saas_Platform         │
              │                              │
              │  Tables:                     │
              │  - users                     │
              │  - tenants                   │
              │  - subscriptions             │
              │  - teams                     │
              │  - tasks                     │
              │  - payments                  │
              │  - invoices                  │
              │  - activity_logs             │
              └──────────────────────────────┘
```

---

## 🎯 MULTI-TENANCY ARCHITECTURE

### Tenant Resolution Flow

```
User Request → Domain/Subdomain → Middleware → Tenant Object → Scoped Queries

Example Flows:

1. acme.saasplatform.com → Tenant: Acme Corporation
2. tech.saasplatform.com → Tenant: Tech Innovators  
3. custom-domain.com → Tenant: Custom Domain Co.
```

### Tenant Isolation

```python
# All queries are automatically scoped to tenant
class TenantMiddleware:
    - Extract subdomain from request
    - Query Domain model
    - Attach tenant to request
    - All subsequent queries filtered by tenant
```

### Data Separation

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Tenant A    │     │  Tenant B    │     │  Tenant C    │
│  (Acme)      │     │  (Tech)      │     │  (Startup)   │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                            ▼
                  ┌─────────────────────┐
                  │  Shared Database    │
                  │  (Row-Level Filter) │
                  └─────────────────────┘

Each row has tenant_id → Complete data isolation
```

---

## 🔐 AUTHENTICATION & AUTHORIZATION

### Authentication Flow

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │ 1. POST /api/auth/login/
       │    { email, password }
       ▼
┌──────────────────────┐
│  LoginView           │
│  - Validate          │
│  - Check tenant      │
└──────┬───────────────┘
       │ 2. Generate JWT
       ▼
┌──────────────────────┐
│  JWT Tokens          │
│  - access_token      │
│  - refresh_token     │
└──────┬───────────────┘
       │ 3. Return to client
       ▼
┌──────────────────────┐
│  Frontend stores     │
│  tokens in localStorage │
└──────────────────────┘

Subsequent requests:
Authorization: Bearer <access_token>
```

### Role-Based Access Control

```
Role Hierarchy:
┌────────────────────────────────────────┐
│         SUPER_ADMIN (Platform Owner)   │  Full Access
├────────────────────────────────────────┤
│         TENANT_ADMIN (Company Admin)   │  Tenant Management
├────────────────────────────────────────┤
│         MANAGER (Team Manager)         │  Team Management
├────────────────────────────────────────┤
│         MEMBER (Regular User)          │  Basic Access
└────────────────────────────────────────┘

Permission Checks:
┌──────────────────────────────────────────────────────┐
│  Request → Permission Class → Role Check → Allow/Deny │
└──────────────────────────────────────────────────────┘
```

---

## 💳 BILLING & SUBSCRIPTION FLOW

### Subscription Lifecycle

```
1. SIGNUP
   User → Register → Tenant Created (Status: PENDING)

2. APPROVAL
   Admin → Approve Tenant → Status: ACTIVE

3. SUBSCRIPTION
   Tenant → Choose Plan → Create Subscription → Status: TRIAL

4. PAYMENT
   Tenant → Submit Payment → Upload Proof → Status: PENDING_VERIFICATION

5. VERIFICATION
   Admin → Verify Payment → Payment Status: COMPLETED
                          → Subscription Status: ACTIVE

6. RENEWAL
   Auto-renew enabled → Generate Invoice → Process Payment
   OR
   Manual → Tenant Pays → Repeat verification

7. EXPIRY/CANCELLATION
   No payment → Subscription: EXPIRED → Tenant: SUSPENDED
   OR
   Cancel → Subscription: CANCELLED → Tenant can renew
```

### Payment Verification Workflow

```
┌──────────────┐
│   Tenant     │
│   Uploads    │
│   Payment    │
│   Proof      │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│  Payment Record      │
│  status: PENDING     │
│  verification_status:│
│  PENDING            │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Admin Reviews       │
│  - Check proof       │
│  - Verify amount     │
└──────┬───────────────┘
       │
       ├─── Approve ───┐
       │               │
       └─── Reject ────┤
                       ▼
              ┌─────────────────┐
              │  Update Payment │
              │  status: COMPLETED │
              │  OR FAILED      │
              └─────────┬───────┘
                        │
                        ▼
              ┌─────────────────┐
              │  Update         │
              │  Subscription   │
              │  Activate       │
              └─────────────────┘
```

---

## 📦 APPLICATION STRUCTURE

### Apps & Responsibilities

```
apps/
├── accounts/           # User management & authentication
│   ├── models.py      → User, UserSession, UserPreference
│   ├── views.py       → Register, Login, Profile
│   ├── serializers.py → User data transformation
│   └── signals.py     → User creation hooks
│
├── tenants/           # Multi-tenancy management
│   ├── models.py      → Tenant, Domain, TenantSettings
│   ├── views.py       → Tenant CRUD, Approval
│   └── serializers.py → Tenant data
│
├── subscriptions/     # Billing & payments
│   ├── models.py      → Plan, Subscription, Payment, Invoice
│   ├── views.py       → Subscription management, Payment verification
│   └── serializers.py → Billing data
│
├── teams/             # Team collaboration
│   ├── models.py      → Team, TeamMember, TeamInvitation
│   ├── views.py       → Team CRUD, Member management
│   └── serializers.py → Team data
│
├── tasks/             # Task management
│   ├── models.py      → Task, Comment, Attachment, Activity
│   ├── views.py       → Task CRUD, Kanban board
│   └── serializers.py → Task data
│
├── notifications/     # Notification system
│   ├── models.py      → Notification, NotificationPreference
│   ├── views.py       → Notification delivery
│   └── serializers.py → Notification data
│
├── admin_panel/       # Admin dashboard
│   ├── views.py       → Admin-specific views
│   └── serializers.py → Admin data
│
└── core/              # Shared utilities
    ├── models.py      → ActivityLog, AuditLog, SystemSetting
    ├── middleware.py  → TenantMiddleware, ApprovalMiddleware
    ├── permissions.py → Role-based permissions
    ├── utils.py       → Helper functions
    └── context_processors.py → Template context
```

---

## 🔄 REQUEST FLOW EXAMPLE

### Example: Creating a Task

```
1. CLIENT REQUEST
   POST /api/tasks/
   Headers: Authorization: Bearer <token>
   Body: {
       "team": 1,
       "title": "Fix bug",
       "priority": "HIGH"
   }

2. DJANGO RECEIVES
   ├─ urls.py routes to tasks.urls
   └─ tasks.urls routes to TaskViewSet.create

3. MIDDLEWARE PROCESSING
   ├─ TenantMiddleware: 
   │  └─ Extract subdomain → Resolve tenant → Attach to request
   ├─ AuthenticationMiddleware:
   │  └─ Validate JWT → Authenticate user
   └─ ApprovalMiddleware:
       └─ Check if tenant is approved

4. VIEW PROCESSING
   TaskViewSet.create():
   ├─ Check permissions (IsAuthenticated, IsApprovedTenant)
   ├─ Validate serializer
   ├─ Check tenant limits (max_projects)
   └─ Create task

5. MODEL LAYER
   Task.objects.create():
   ├─ Set tenant=request.tenant
   ├─ Set created_by=request.user
   └─ Save to database

6. ACTIVITY LOGGING
   ActivityLog.create():
   └─ Log task creation with user, tenant, timestamp

7. RESPONSE
   HTTP 201 Created
   Body: {
       "id": 123,
       "title": "Fix bug",
       "status": "TODO",
       "created_by": {...},
       ...
   }
```

---

## 📱 API ENDPOINTS MAP

```
/api/
├── auth/
│   ├── register/              POST    Create account
│   ├── login/                 POST    Get JWT tokens
│   ├── logout/                POST    Invalidate session
│   ├── profile/               GET/PATCH   User profile
│   ├── change-password/       POST    Change password
│   └── password-reset/        POST    Reset password
│
├── tenants/
│   ├── /                      GET/POST    List/Create tenants
│   ├── /{id}/                 GET/PATCH   Tenant details
│   ├── /{id}/approve/         POST    Approve tenant (admin)
│   ├── /{id}/suspend/         POST    Suspend tenant (admin)
│   ├── invitations/           GET/POST    Tenant invitations
│   └── settings/              GET/PATCH   Tenant settings
│
├── subscriptions/
│   ├── plans/                 GET     List subscription plans
│   ├── subscriptions/         GET/POST    Manage subscriptions
│   ├── subscriptions/{id}/cancel/  POST    Cancel subscription
│   ├── payments/              GET/POST    Payment records
│   ├── payments/{id}/verify/  POST    Verify payment (admin)
│   ├── invoices/              GET/POST    Invoices
│   └── billing/dashboard/     GET     Billing overview
│
├── teams/
│   ├── /                      GET/POST    List/Create teams
│   ├── /{id}/                 GET/PATCH/DELETE   Team details
│   ├── /{id}/members/         GET     Team members
│   ├── /{id}/add-member/      POST    Add member
│   ├── /{id}/remove-member/   POST    Remove member
│   └── invitations/           GET/POST    Team invitations
│
├── tasks/
│   ├── /                      GET/POST    List/Create tasks
│   ├── /{id}/                 GET/PATCH/DELETE   Task details
│   ├── /{id}/comments/        GET/POST    Task comments
│   ├── /{id}/attachments/     POST    Upload files
│   └── /{id}/activities/      GET     Task history
│
└── notifications/
    ├── /                      GET     List notifications
    ├── /{id}/mark-read/       POST    Mark as read
    └── preferences/           GET/PATCH   Notification settings
```

---

## 🗄️ DATABASE SCHEMA RELATIONSHIPS

```
┌──────────────┐
│    USERS     │
└──────┬───────┘
       │ belongs_to
       ▼
┌──────────────┐      ┌─────────────────┐
│   TENANTS    │◄─────│  SUBSCRIPTIONS  │
└──────┬───────┘      └────────┬────────┘
       │ has_many             │ belongs_to
       │                      ▼
       │               ┌──────────────┐
       │               │    PLANS     │
       │               └──────────────┘
       │
       ├──────────┬──────────┬──────────┐
       │          │          │          │
       ▼          ▼          ▼          ▼
  ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────┐
  │ TEAMS  │ │ TASKS  │ │PAYMENTS│ │INVOICES │
  └────┬───┘ └────┬───┘ └────────┘ └─────────┘
       │          │
       │          ├──────┬──────────┐
       │          │      │          │
       ▼          ▼      ▼          ▼
  ┌──────────┐ ┌─────────┐ ┌────────────┐
  │  TEAM    │ │COMMENTS │ │ATTACHMENTS │
  │ MEMBERS  │ └─────────┘ └────────────┘
  └──────────┘

Activity & Audit Logs track all changes
```

---

## 🚀 DEPLOYMENT ARCHITECTURE

```
┌────────────────────────────────────────────────────────┐
│                    LOAD BALANCER                       │
│                    (Nginx/HAProxy)                     │
└───────────────┬────────────────────────────────────────┘
                │
                ├──────────┬──────────┬──────────┐
                │          │          │          │
                ▼          ▼          ▼          ▼
         ┌──────────┐ ┌──────────┐ ┌──────────┐
         │ Django   │ │ Django   │ │ Django   │
         │ App      │ │ App      │ │ App      │
         │ Instance │ │ Instance │ │ Instance │
         └────┬─────┘ └────┬─────┘ └────┬─────┘
              │            │            │
              └────────────┼────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   MySQL Database       │
              │   (Master)             │
              └────────┬───────────────┘
                       │ Replication
                       ▼
              ┌────────────────────────┐
              │   MySQL Database       │
              │   (Replica - Read)     │
              └────────────────────────┘

Additional Services:
├── Redis → Caching & Sessions
├── Celery → Background Tasks
├── S3 → File Storage
└── Sentry → Error Tracking
```

---

## 🔒 SECURITY ARCHITECTURE

### Security Layers

```
1. NETWORK LEVEL
   - HTTPS/TLS encryption
   - CORS configuration
   - Rate limiting
   - IP whitelisting (admin)

2. APPLICATION LEVEL
   - JWT authentication
   - Role-based permissions
   - Tenant isolation
   - CSRF protection
   - SQL injection prevention (ORM)
   - XSS protection

3. DATA LEVEL
   - Password hashing (PBKDF2)
   - Sensitive data encryption
   - Audit logging
   - Data backup

4. BUSINESS LOGIC
   - Approval workflow
   - Payment verification
   - Usage limits
   - Session management
```

---

This architecture provides a scalable, secure, and maintainable foundation for a multi-tenant SaaS platform.
