"""
Quick test script for cloud backend APIs
"""
import requests
import json

BASE_URL = "http://localhost:9000"

print("=== Testing Cloud Backend ===\n")

# Test 1: Register user
print("1. Registering user...")
response = requests.post(
    f"{BASE_URL}/api/auth/register",
    json={
        "email": "test@smarthome.local",
        "password": "testpass123",
        "password2": "testpass123"
    }
)
print(f"Status: {response.status_code}")
if response.status_code == 201:
    data = response.json()
    print(f"✅ User registered: {data['user']['email']}")
    access_token = data['tokens']['access']
    print(f"Access token: {access_token[:50]}...")
else:
    print(f"❌ Registration failed: {response.text}")
    exit(1)

# Test 2: Provision gateway
print("\n2. Provisioning gateway...")
home_id = "550e8400-e29b-41d4-a716-446655440000"  # Example UUID
response = requests.post(
    f"{BASE_URL}/api/gateways/provision/",  # Added trailing slash
    headers={"Authorization": f"Bearer {access_token}"},
    json={"home_id": home_id, "name": "Test Home"}
)
print(f"Status: {response.status_code}")
if response.status_code == 201:
    data = response.json()
    print(f"✅ Gateway provisioned!")
    print(f"   Gateway ID: {data['gateway_id']}")
    print(f"   Home ID: {data['home_id']}")
    print(f"   Secret: {data['secret']}")
    print(f"\n📝 Save these credentials for edge client!")
    
    # Save to file for easy configuration
    with open("gateway_credentials.txt", "w") as f:
        f.write(f"CLOUD_GATEWAY_ID={data['gateway_id']}\n")
        f.write(f"CLOUD_GATEWAY_SECRET={data['secret']}\n")
        f.write(f"CLOUD_BRIDGE_URL=ws://localhost:9000/bridge/\n")
    print("   Saved to gateway_credentials.txt")
else:
    print(f"❌ Provisioning failed: {response.text}")

print("\n✅ Cloud backend is working!")
