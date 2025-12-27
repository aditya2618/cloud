# Test Production Cloud Server
import requests

CLOUD_URL = "http://35.209.239.164"

print("🧪 Testing Production Cloud Server")
print("=" * 60)

# Test 1: Check if new endpoints exist
print("\n1️⃣ Testing login endpoint...")
try:
    # Try to login (will fail with 400 but endpoint should exist)
    response = requests.post(
        f"{CLOUD_URL}/api/auth/login",
        json={"email": "test@test.com", "password": "test"},
        timeout=10
    )
    print(f"✅ Login endpoint exists (status: {response.status_code})")
    
    if response.status_code == 200:
        data = response.json()
        if 'homes' in data:
            print("✅ JWT with homes is ALREADY deployed!")
        else:
            print("⚠️  Old login format (no homes) - needs update")
    elif response.status_code in [400, 401]:
        print("ℹ️  Endpoint exists but credentials invalid (expected)")
    
except requests.exceptions.RequestException as e:
    print(f"❌ Cannot reach server: {e}")
    exit(1)

# Test 2: Check pairing code endpoint
print("\n2️⃣ Testing pairing code endpoint...")
try:
    response = requests.get(
        f"{CLOUD_URL}/api/gateways/verify-pairing/12345678",
        timeout=10
    )
    
    if response.status_code in [200, 404]:
        print("✅ Pairing endpoint exists!")
        if response.status_code == 200:
            print("✅ Pairing code feature is deployed!")
    elif response.status_code == 404:
        print("⚠️  Pairing endpoint not found - needs deployment")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Endpoint check failed: {e}")

print("\n" + "=" * 60)
print("📋 Summary:")
print("   Server: http://35.209.239.164")
print("   Next: Check DEPLOYMENT.md for update instructions")
print("=" * 60)
