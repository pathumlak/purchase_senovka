#!/usr/bin/env python
"""
Creates default SuperAdmin and Admin users for the ERP system.
Run with: python seed_users.py

SuperAdmin — full access including billing management and user management.
Admin      — production, customers, bookings, purchasing, petty cash (no billing write access).
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.contrib.auth.models import User
from erp.models import UserProfile

USERS = [
    {
        'username':   'Dinusha',
        'password':   'superadmin123',
        'first_name': 'Dinusha',
        'last_name':  'Admin',
        'role':       UserProfile.SUPERADMIN,
        'is_staff':   True,
    },
    {
        'username':   'pathum',
        'password':   '123456789',
        'first_name': 'System',
        'last_name':  'Admin',
        'role':       UserProfile.ADMIN,
        'is_staff':   False,
    },{
        'username':   'Dushan',
        'password':   '123456789',
        'first_name': 'Admin',
        'last_name':  'User',
        'role':       UserProfile.ADMIN,
        'is_staff':   False,
    }
]

for spec in USERS:
    username = spec['username']
    role     = spec['role']

    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        profile, created = UserProfile.objects.get_or_create(user=user)
        if created or profile.role != role:
            profile.role = role
            profile.save()
        print(f'[skip] User "{username}" already exists — profile synced to {dict(UserProfile.ROLE_CHOICES)[role]}.')
    else:
        user = User.objects.create_user(
            username   = username,
            password   = spec['password'],
            first_name = spec['first_name'],
            last_name  = spec['last_name'],
            is_staff   = spec.get('is_staff', False),
        )
        UserProfile.objects.create(user=user, role=role)
        print(f'[ok] User created: {username}')
        print(f'     Role     : {dict(UserProfile.ROLE_CHOICES)[role]}')
        print(f'     Password : {spec["password"]}')
        print(f'     --> Change the password after first login at /profile/')

print()
print('Done. Users summary:')
for u in User.objects.select_related('profile').filter(is_active=True).order_by('username'):
    role_label = u.profile.get_role_display() if hasattr(u, 'profile') else 'No profile'
    print(f'  - {u.username:<20} {role_label}')
