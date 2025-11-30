"""
Management command to create sample data for development/testing.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.accounts.models import User
from apps.tenants.models import Tenant, Domain, TenantSettings
from apps.subscriptions.models import Plan, Subscription, Payment, Invoice, InvoiceItem
from apps.teams.models import Team, TeamMember
from apps.tasks.models import Task, Comment
from apps.core.models import SystemSetting


class Command(BaseCommand):
    help = 'Create sample data for development and testing'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...\n')
        
        # Create Plans
        self.stdout.write('Creating subscription plans...')
        plans = self.create_plans()
        
        # Create Super Admin
        self.stdout.write('Creating super admin...')
        super_admin = self.create_super_admin()
        
        # Create Sample Tenants
        self.stdout.write('Creating sample tenants...')
        tenants = self.create_tenants(plans)
        
        # Create Users for each tenant
        self.stdout.write('Creating users...')
        users = self.create_users(tenants)
        
        # Create Teams
        self.stdout.write('Creating teams...')
        teams = self.create_teams(tenants, users)
        
        # Create Tasks
        self.stdout.write('Creating tasks...')
        self.create_tasks(teams, users)
        
        # Create System Settings
        self.stdout.write('Creating system settings...')
        self.create_system_settings()
        
        self.stdout.write(self.style.SUCCESS('\nSample data created successfully!'))
        self.stdout.write(f'\nSuper Admin: admin@example.com / Admin@123')
        self.stdout.write(f'Tenant Admins: Check the created tenants\n')
    
    def create_plans(self):
        plans = []
        
        # Free Plan
        plan = Plan.objects.create(
            name='Free',
            slug='free',
            description='Perfect for getting started',
            price=Decimal('0.00'),
            currency='USD',
            billing_interval='MONTHLY',
            max_users=5,
            max_teams=2,
            max_projects=5,
            max_storage_gb=1,
            enable_api_access=False,
            enable_advanced_reports=False,
            enable_priority_support=False,
            is_popular=False,
            is_active=True,
            trial_days=14,
            sort_order=1
        )
        plans.append(plan)
        
        # Starter Plan
        plan = Plan.objects.create(
            name='Starter',
            slug='starter',
            description='Great for small teams',
            price=Decimal('29.00'),
            currency='USD',
            billing_interval='MONTHLY',
            max_users=10,
            max_teams=5,
            max_projects=20,
            max_storage_gb=10,
            enable_api_access=True,
            enable_advanced_reports=False,
            enable_priority_support=False,
            is_popular=True,
            is_active=True,
            trial_days=14,
            sort_order=2
        )
        plans.append(plan)
        
        # Professional Plan
        plan = Plan.objects.create(
            name='Professional',
            slug='professional',
            description='For growing businesses',
            price=Decimal('99.00'),
            currency='USD',
            billing_interval='MONTHLY',
            max_users=50,
            max_teams=20,
            max_projects=100,
            max_storage_gb=100,
            enable_api_access=True,
            enable_advanced_reports=True,
            enable_priority_support=True,
            enable_custom_branding=True,
            is_popular=False,
            is_active=True,
            trial_days=14,
            sort_order=3
        )
        plans.append(plan)
        
        # Enterprise Plan
        plan = Plan.objects.create(
            name='Enterprise',
            slug='enterprise',
            description='For large organizations',
            price=Decimal('299.00'),
            currency='USD',
            billing_interval='MONTHLY',
            max_users=999,
            max_teams=999,
            max_projects=999,
            max_storage_gb=1000,
            enable_api_access=True,
            enable_advanced_reports=True,
            enable_priority_support=True,
            enable_custom_branding=True,
            enable_sso=True,
            enable_audit_logs=True,
            is_popular=False,
            is_active=True,
            trial_days=14,
            sort_order=4
        )
        plans.append(plan)
        
        return plans
    
    def create_super_admin(self):
        if User.objects.filter(email='admin@example.com').exists():
            return User.objects.get(email='admin@example.com')
        
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='Admin@123',
            first_name='Super',
            last_name='Admin'
        )
        return user
    
    def create_tenants(self, plans):
        tenants = []
        
        tenant_data = [
            {
                'name': 'Acme Corporation',
                'slug': 'acme',
                'company_name': 'Acme Corporation Inc.',
                'company_email': 'contact@acme.com',
                'admin_email': 'admin@acme.com',
                'plan': plans[1],  # Starter
                'status': 'ACTIVE',
                'is_approved': True,
            },
            {
                'name': 'Tech Innovators',
                'slug': 'tech-innovators',
                'company_name': 'Tech Innovators LLC',
                'company_email': 'info@techinnovators.com',
                'admin_email': 'admin@techinnovators.com',
                'plan': plans[2],  # Professional
                'status': 'ACTIVE',
                'is_approved': True,
            },
            {
                'name': 'Startup Demo',
                'slug': 'startup-demo',
                'company_name': 'Startup Demo Inc.',
                'company_email': 'hello@startupdemo.com',
                'admin_email': 'admin@startupdemo.com',
                'plan': plans[0],  # Free
                'status': 'PENDING',
                'is_approved': False,
            },
        ]
        
        for data in tenant_data:
            plan = data.pop('plan')
            admin_email = data.pop('admin_email')
            
            tenant = Tenant.objects.create(**data)
            
            # Create subscription
            now = timezone.now()
            subscription = Subscription.objects.create(
                tenant=tenant,
                plan=plan,
                status='TRIAL',
                current_period_start=now,
                current_period_end=now + timedelta(days=30),
                trial_start=now,
                trial_end=now + timedelta(days=plan.trial_days)
            )
            
            tenant.subscription = subscription
            tenant.max_users = plan.max_users
            tenant.max_teams = plan.max_teams
            tenant.max_projects = plan.max_projects
            tenant.max_storage_gb = plan.max_storage_gb
            tenant.save()
            
            # Create domain
            Domain.objects.create(
                tenant=tenant,
                domain=f"{tenant.slug}.saasplatform.com",
                domain_type='SUBDOMAIN',
                is_primary=True,
                is_verified=True
            )
            
            # Create tenant settings
            TenantSettings.objects.create(tenant=tenant)
            
            # Create tenant admin
            User.objects.create_user(
                email=admin_email,
                password='Password@123',
                first_name=tenant.name,
                last_name='Admin',
                role='TENANT_ADMIN',
                tenant=tenant,
                is_email_verified=True
            )
            
            tenant.current_users_count = 1
            tenant.save()
            
            tenants.append(tenant)
        
        return tenants
    
    def create_users(self, tenants):
        users = []
        
        for tenant in tenants[:2]:  # Only for approved tenants
            # Create managers
            for i in range(2):
                user = User.objects.create_user(
                    email=f'manager{i+1}@{tenant.slug}.com',
                    password='Password@123',
                    first_name=f'Manager{i+1}',
                    last_name='User',
                    role='MANAGER',
                    tenant=tenant,
                    is_email_verified=True
                )
                users.append(user)
            
            # Create members
            for i in range(3):
                user = User.objects.create_user(
                    email=f'member{i+1}@{tenant.slug}.com',
                    password='Password@123',
                    first_name=f'Member{i+1}',
                    last_name='User',
                    role='MEMBER',
                    tenant=tenant,
                    is_email_verified=True
                )
                users.append(user)
            
            # Update tenant user count
            tenant.current_users_count = tenant.users.count()
            tenant.save()
        
        return users
    
    def create_teams(self, tenants, users):
        teams = []
        
        for tenant in tenants[:2]:  # Only for approved tenants
            tenant_users = list(tenant.users.all())
            if not tenant_users:
                continue
            
            team_names = ['Development', 'Design', 'Marketing']
            
            for team_name in team_names:
                team = Team.objects.create(
                    tenant=tenant,
                    name=team_name,
                    slug=team_name.lower(),
                    description=f'{team_name} team for {tenant.name}',
                    owner=tenant_users[0]
                )
                
                # Add team members
                for i, user in enumerate(tenant_users[:3]):
                    role = 'OWNER' if i == 0 else 'ADMIN' if i == 1 else 'MEMBER'
                    TeamMember.objects.create(
                        team=team,
                        user=user,
                        role=role
                    )
                
                team.members_count = 3
                team.save()
                teams.append(team)
            
            # Update tenant team count
            tenant.current_teams_count = tenant.teams.count()
            tenant.save()
        
        return teams
    
    def create_tasks(self, teams, users):
        for team in teams:
            members = list(team.members.all())
            if not members:
                continue
            
            statuses = ['TODO', 'IN_PROGRESS', 'IN_REVIEW', 'COMPLETED']
            priorities = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
            
            for i in range(5):
                task = Task.objects.create(
                    tenant=team.tenant,
                    team=team,
                    title=f'Task {i+1} for {team.name}',
                    description=f'This is a sample task description for task {i+1}',
                    status=statuses[i % len(statuses)],
                    priority=priorities[i % len(priorities)],
                    created_by=members[0].user,
                    assigned_to=members[i % len(members)].user if len(members) > 0 else None,
                    start_date=timezone.now().date(),
                    due_date=(timezone.now() + timedelta(days=7)).date(),
                    position=i
                )
                
                # Add a comment
                Comment.objects.create(
                    task=task,
                    user=members[0].user,
                    content=f'This is a sample comment on task {i+1}'
                )
                
                task.comments_count = 1
                task.save()
            
            team.tasks_count = 5
            team.save()
    
    def create_system_settings(self):
        settings = [
            {
                'key': 'site_name',
                'value': 'SaaS Platform',
                'value_type': 'STRING',
                'description': 'Site name',
                'is_public': True
            },
            {
                'key': 'maintenance_mode',
                'value': 'false',
                'value_type': 'BOOLEAN',
                'description': 'Enable maintenance mode',
                'is_public': False
            },
            {
                'key': 'allow_signup',
                'value': 'true',
                'value_type': 'BOOLEAN',
                'description': 'Allow new tenant signups',
                'is_public': True
            },
        ]
        
        for setting_data in settings:
            SystemSetting.objects.get_or_create(
                key=setting_data['key'],
                defaults=setting_data
            )
