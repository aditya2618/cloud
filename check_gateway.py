import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthome_cloud.settings')
django.setup()

from gateways.models import Gateway, HomePermission

print("\n=== Gateways ===")
gateways = Gateway.objects.all()
for g in gateways:
    print(f"Gateway: {g.id}")
    print(f"  Home ID: {g.home_id}")
    print(f"  Owner: {g.owner.email}")
    print(f"  Status: {g.status}")
    
print("\n=== Home Permissions ===")
perms = HomePermission.objects.all()
for p in perms:
    print(f"User: {p.user.email}")
    print(f"  Home ID: {p.home_id}")
    print(f"  Role: {p.role}")
    print(f"  Gateway: {p.gateway.id if p.gateway else 'None'}")
    print()
