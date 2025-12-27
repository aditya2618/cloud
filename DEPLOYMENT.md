# Deployment Guide - Production Cloud Server

## 🚀 Deploy to http://35.209.239.164

### Files to Update on Production Server

**New/Modified Files**:
1. `gateways/pairing_codes.py` - NEW (pairing code model)
2. `gateways/pairing_serializers.py` - NEW (serializers)
3. `gateways/views.py` - UPDATED (added 3 pairing endpoints)
4. `gateways/urls.py` - UPDATED (added pairing URLs)
5. `accounts/jwt_utils.py` - NEW (JWT with homes)
6. `accounts/login_serializer.py` - NEW (login serializer)
7. `accounts/views.py` - UPDATED (custom login endpoint)
8. `accounts/urls.py` - UPDATED (use custom login)
9. `smarthome_cloud/consumers.py` - UPDATED (JWT validation)

### Deployment Steps

```bash
# 1. SSH to your GCP instance
ssh your-user@35.209.239.164

# 2. Navigate to project directory
cd /path/to/esp32-flasher/cloud

# 3. Activate virtual environment
source venv/bin/activate  # or: & cloud/Scripts/Activate.ps1 on Windows

# 4. Pull latest code (or upload files)
# If using git:
git pull origin main

# If manually uploading, use SCP/SFTP to copy these files:
# - gateways/pairing_codes.py
# - gateways/pairing_serializers.py
# - gateways/views.py (overwrite)
# - gateways/urls.py (overwrite)
# - accounts/jwt_utils.py
# - accounts/login_serializer.py
# - accounts/views.py (overwrite)
# - accounts/urls.py (overwrite)
# - smarthome_cloud/consumers.py (overwrite)

# 5. Run migrations (creates pairing_codes table)
python manage.py makemigrations
python manage.py migrate

# 6. Restart services
# If using systemd:
sudo systemctl restart smarthome-cloud
sudo systemctl restart smarthome-websocket

# If using supervisor:
sudo supervisorctl restart smarthome-cloud
sudo supervisorctl restart smarthome-websocket

# If using docker:
docker-compose restart

# If manual (not recommended for production):
# Kill existing process and restart
pkill -f "manage.py runserver"
nohup python manage.py runserver 0.0.0.0:9000 &
```

### Quick File Transfer (Windows to Linux)

```powershell
# From your Windows machine
cd d:\PROJECT\esp32-flasher\cloud

# Using SCP
scp gateways/pairing_codes.py your-user@35.209.239.164:/path/to/cloud/gateways/
scp gateways/pairing_serializers.py your-user@35.209.239.164:/path/to/cloud/gateways/
scp gateways/views.py your-user@35.209.239.164:/path/to/cloud/gateways/
scp gateways/urls.py your-user@35.209.239.164:/path/to/cloud/gateways/
scp accounts/jwt_utils.py your-user@35.209.239.164:/path/to/cloud/accounts/
scp accounts/login_serializer.py your-user@35.209.239.164:/path/to/cloud/accounts/
scp accounts/views.py your-user@35.209.239.164:/path/to/cloud/accounts/
scp accounts/urls.py your-user@35.209.239.164:/path/to/cloud/accounts/
scp smarthome_cloud/consumers.py your-user@35.209.239.164:/path/to/cloud/smarthome_cloud/
```

### Verify Deployment

```bash
# Test new endpoints
curl -X POST http://35.209.239.164/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpass"}'

# Should return: { "access": "...", "refresh": "...", "user": {...}, "homes": [] }

# Test pairing code (after login)
curl -X POST http://35.209.239.164/api/gateways/request-pairing \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"home_name":"Test Home","expiry_minutes":10}'

# Should return: { "code": "12345678", "expires_at": "...", "message": "..." }
```

---

## 🏠 Configure Local Server to Connect to Production Cloud

Update your local server's `.env`:

```bash
# d:\PROJECT\esp32-flasher\server\.env
CLOUD_ENABLED=true
CLOUD_BRIDGE_URL=ws://35.209.239.164:9000/ws/gateway/
CLOUD_GATEWAY_ID=your-home-uuid
CLOUD_GATEWAY_SECRET=your-secret-from-pairing
```

Then restart local server:
```bash
cd d:\PROJECT\esp32-flasher\server
& server/Scripts/Activate.ps1
python manage.py runserver 0.0.0.0:8000
```

---

## ✅ Checklist

- [ ] SSH to 35.209.239.164
- [ ] Upload new files (9 files total)
- [ ] Run `python manage.py migrate`
- [ ] Restart cloud services
- [ ] Test login endpoint (returns homes in response)
- [ ] Test pairing code endpoint
- [ ] Update local server `.env` with production cloud URL
- [ ] Restart local server
- [ ] Verify local server connects to production cloud

---

## 📱 Mobile App (Already Configured!)

Your mobile app is already pointing to the correct server:
```typescript
const CLOUD_URL = 'http://35.209.239.164';
```

The updated `cloudClient.ts` will:
- ✅ Store homes from JWT login response
- ✅ Use new pairing code functions
- ✅ Handle JWT refresh automatically

No changes needed on mobile side - just redeploy the code!
