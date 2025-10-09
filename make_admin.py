#!/usr/bin/env python
"""
Script para tornar um usuário administrador
Uso: python make_admin.py <username>
"""
import os
import sys
import django

# Configura o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User

if len(sys.argv) < 2:
    print("❌ Uso: python make_admin.py <username>")
    print("\nExemplo: python make_admin.py admin")
    sys.exit(1)

username = sys.argv[1]

try:
    user = User.objects.get(username=username)
    user.is_staff = True
    user.is_superuser = True
    user.save()

    print(f"✅ Usuário '{username}' agora é administrador!")
    print(f"   - is_staff: {user.is_staff}")
    print(f"   - is_superuser: {user.is_superuser}")
    print(f"\nAgora você pode criar usuários via /api/auth/admin/users/")

except User.DoesNotExist:
    print(f"❌ Usuário '{username}' não encontrado")
    print("\nUsuários disponíveis:")
    for u in User.objects.all()[:10]:
        admin_badge = " 🔑" if u.is_superuser else ""
        print(f"   - {u.username}{admin_badge}")
    sys.exit(1)
