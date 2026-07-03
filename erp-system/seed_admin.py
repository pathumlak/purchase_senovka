#!/usr/bin/env python
"""
Run with:  python seed_admin.py
Creates the default superuser if one does not already exist.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.contrib.auth.models import User

USERNAME   = 'admin'
PASSWORD   = 'admin123'
FIRST_NAME = 'Admin'
LAST_NAME  = 'User'

if User.objects.filter(username=USERNAME).exists():
    print(f'[skip] Superuser "{USERNAME}" already exists.')
else:
    User.objects.create_superuser(
        username=USERNAME,
        password=PASSWORD,
        first_name=FIRST_NAME,
        last_name=LAST_NAME,
        email='',
    )
    print(f'[ok] Superuser created.')
    print(f'     Username : {USERNAME}')
    print(f'     Password : {PASSWORD}')
    print(f'     --> Change the password after first login at /profile/')
