"""
Test script for Remote Control API

Tests the complete flow:
1. Authenticate with cloud
2. Check gateway status
3. Send entity control command
4. Send scene run command
"""
import requests
import json

# Cloud server URL
CLOUD_URL = "http://localhost:9000"

# User credentials (from provision_gateway.py)
EMAIL = "test@smarthome.local"
PASSWORD = "testpass123"

# Test data
HOME_ID = "550e8400-e29b-41d4-a716-446655440000"  # From gateway provisioning (UUID)
ENTITY_ID = 6  # Living room light switch from LOCAL database
SCENE_ID = 27  # A scene to run from LOCAL database

def test_remote_control():
    """Test the complete remote control flow"""
    
    print("=" * 60)
    print("🧪 Testing Cloud Remote Control API")
    print("=" * 60)
    
    # Step 1: Login and get JWT token
    print("\n1️⃣  Authenticating with cloud...")
    login_response = requests.post(
        f"{CLOUD_URL}/api/auth/login/",
        json={"email": EMAIL, "password": PASSWORD}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json()["access"]
    print(f"✅ Logged in successfully")
    print(f"   Token: {token[:50]}...")
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Check gateway status
    print(f"\n2️⃣  Checking gateway status for home {HOME_ID}...")
    status_response = requests.get(
        f"{CLOUD_URL}/api/remote/homes/{HOME_ID}/status",
        headers=headers
    )
    
    if status_response.status_code != 200:
        print(f"❌ Status check failed: {status_response.status_code}")
        print(status_response.text)
        return
    
    status_data = status_response.json()
    print(f"✅ Gateway status: {status_data['status']}")
    print(f"   Gateway ID: {status_data['gateway_id']}")
    print(f"   Last ping: {status_data['last_ping']}")
    
    if status_data['status'] != 'online':
        print(f"⚠️  Gateway is {status_data['status']}, commands may fail")
    
    # Step 3: Control entity (turn on light)
    print(f"\n3️⃣  Sending command to entity {ENTITY_ID} (turn ON)...")
    control_response = requests.post(
        f"{CLOUD_URL}/api/remote/homes/{HOME_ID}/entities/{ENTITY_ID}/control",
        headers=headers,
        json={"command": "turn_on"}
    )
    
    if control_response.status_code != 200:
        print(f"❌ Control failed: {control_response.status_code}")
        print(control_response.text)
    else:
        control_data = control_response.json()
        print(f"✅ Command sent successfully!")
        print(f"   Command ID: {control_data['command_id']}")
        print(f"   Status: {control_data['status']}")
    
    # Step 4: Wait a bit, then turn off
    import time
    print("\n   ⏳ Waiting 3 seconds...")
    time.sleep(3)
    
    print(f"\n4️⃣  Sending command to entity {ENTITY_ID} (turn OFF)...")
    control_response2 = requests.post(
        f"{CLOUD_URL}/api/remote/homes/{HOME_ID}/entities/{ENTITY_ID}/control",
        headers=headers,
        json={"command": "turn_off"}
    )
    
    if control_response2.status_code != 200:
        print(f"❌ Control failed: {control_response2.status_code}")
        print(control_response2.text)
    else:
        control_data2 = control_response2.json()
        print(f"✅ Command sent successfully!")
        print(f"   Command ID: {control_data2['command_id']}")
    
    # Step 5: Run a scene
    print(f"\n5️⃣  Running scene {SCENE_ID}...")
    scene_response = requests.post(
        f"{CLOUD_URL}/api/remote/homes/{HOME_ID}/scenes/{SCENE_ID}/run",
        headers=headers
    )
    
    if scene_response.status_code != 200:
        print(f"❌ Scene run failed: {scene_response.status_code}")
        print(scene_response.text)
    else:
        scene_data = scene_response.json()
        print(f"✅ Scene command sent!")
        print(f"   Command ID: {scene_data['command_id']}")
    
    print("\n" + "=" * 60)
    print("🎉 Remote Control Test Complete!")
    print("=" * 60)
    print("\nCheck the following logs to verify:")
    print("  • Cloud server logs - Should show 'Sending command to gateway'")
    print("  • Edge client logs - Should show 'Received command from cloud'")
    print("  • Local Django logs - Should show entity state updates")
    print("  • MQTT logs - Should see device commands published")
    print()


if __name__ == "__main__":
    try:
        test_remote_control()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
