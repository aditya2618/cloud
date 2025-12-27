"""
Quick script to create test user and provision gateway via Django ORM
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthome_cloud.settings')
django.setup()

from accounts.models import CloudUser
from gateways.models import Gateway, HomePermission
from django.contrib.auth.hashers import make_password
import uuid

print("=== Cloud Backend Setup ===\n")

# Create user
email = "test@smarthome.local"
password = "testpass123"

user, created = CloudUser.objects.get_or_create(
    email=email,
    defaults={'password': make_password(password)}
)
if created:
    print(f"✅ User created: {email}")
else:
    print(f"ℹ️  User exists: {email}")

# Provision gateway
home_id = uuid.UUID('550e8400-e29b-41d4-a716-446655440000')

# Generate secret
from gateways.models import Gateway as GatewayModel
secret = GatewayModel.generate_secret()
secret_hash = make_password(secret)

# Check if gateway exists
gateway = Gateway.objects.filter(home_id=home_id).first()

if not gateway:
    gateway = Gateway.objects.create(
        home_id=home_id,
        owner=user,
        name="Test Home",
        secret_hash=secret_hash,
        status='provisioning'
    )
    
    # Create owner permission
    HomePermission.objects.create(
        user=user,
        home_id=home_id,
        role='owner',
        granted_by=user
    )
    
    print(f"✅ Gateway provisioned!")
    print(f"   Gateway ID: {gateway.id}")
    print(f"   Home ID: {gateway.home_id}")
    print(f"   Secret: {secret}")
    
    # Save credentials to file
    with open("../server/gateway_credentials.env", "w") as f:
        f.write(f"CLOUD_BRIDGE_URL=ws://localhost:9000/bridge/\n")
        f.write(f"CLOUD_GATEWAY_ID={gateway.id}\n")
        f.write(f"CLOUD_GATEWAY_SECRET={secret}\n")
    
    print(f"\n📝 Credentials saved to ../server/gateway_credentials.env")
else:
    print(f"ℹ️  Gateway already exists: {gateway.id}")
    print(f"⚠️  Cannot retrieve secret (it's hashed in database)")
    print(f"   If you need to re-provision, delete the gateway first")

print("\n✅ Setup complete!")
