import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthome_cloud.settings')
django.setup()

from accounts.models import CloudUser

users = CloudUser.objects.all()
print("\n=== Cloud Users ===")
for u in users:
    print(f"Email: {u.email}, ID: {u.id}")
print(f"Total: {users.count()}\n")
