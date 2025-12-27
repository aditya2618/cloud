# Production Cloud Server Fix Guide

## Issues Identified from Logs

1. **TypeError in /api/auth/login/** - Production doesn't have latest login view 
2. **ALLOWED_HOSTS** - Missing `35.209.239.164` and your domain
3. **Migrations** - New models need migration (PairingCode, HomePermission)

## SSH to Production Server

```bash
ssh adityagracy18@35.209.239.164
# or
ssh adityagracy18@instance-20251224-044641
```

## Step 1: Navigate to Cloud Directory

```bash
cd ~/cloud
source cloud/bin/activate
```

---

## Step 2: Update ALLOWED_HOSTS

Edit settings.py on the production server:

```bash
nano smarthome_cloud/settings.py
```

Find the `ALLOWED_HOSTS` line and change it to:

```python
ALLOWED_HOSTS = ['*']  # For development, restrict later
# OR for production:
# ALLOWED_HOSTS = ['35.209.239.164', 'localhost', '127.0.0.1', 'adityapech.site', 'www.adityapech.site']
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Step 3: Upload Updated Files

Either use git pull OR manually copy these files:

### Option A: If using Git
```bash
git pull origin main
```

### Option B: Manual Copy (SCP from Windows)
Run these from your Windows PowerShell (NOT on server):

```powershell
# From Windows machine:
cd d:\PROJECT\esp32-flasher\cloud

scp accounts/views.py adityagracy18@35.209.239.164:~/cloud/accounts/
scp accounts/login_serializer.py adityagracy18@35.209.239.164:~/cloud/accounts/
scp accounts/jwt_utils.py adityagracy18@35.209.239.164:~/cloud/accounts/
scp accounts/urls.py adityagracy18@35.209.239.164:~/cloud/accounts/
scp gateways/views.py adityagracy18@35.209.239.164:~/cloud/gateways/
scp gateways/urls.py adityagracy18@35.209.239.164:~/cloud/gateways/
scp gateways/pairing_codes.py adityagracy18@35.209.239.164:~/cloud/gateways/
scp gateways/pairing_serializers.py adityagracy18@35.209.239.164:~/cloud/gateways/
scp smarthome_cloud/consumers.py adityagracy18@35.209.239.164:~/cloud/smarthome_cloud/
```

---

## Step 4: Run Migrations (on production server)

```bash
cd ~/cloud
source cloud/bin/activate
python manage.py makemigrations
python manage.py migrate
```

---

## Step 5: Restart Service

```bash
sudo systemctl restart smarthome-cloud
```

Check status:
```bash
sudo systemctl status smarthome-cloud
sudo journalctl -u smarthome-cloud -n 50 --no-pager
```

---

## Step 6: Test

From your Windows machine:
```bash
python quick_pair.py
```

Should now get a pairing code!

---

## Quick Settings Fix (Minimum Required)

If you want the quickest fix, just change settings.py on production:

```python
# Line ~19: Change to
ALLOWED_HOSTS = ['*']

# Line ~17: Make sure DEBUG=True temporarily
DEBUG = True
```

Then restart: `sudo systemctl restart smarthome-cloud`

---

## Summary of Files to Update

**Must upload:**
- `accounts/views.py` - New LoginView
- `accounts/login_serializer.py` - New serializer
- `accounts/jwt_utils.py` - JWT utilities
- `accounts/urls.py` - Updated URLs
- `gateways/pairing_codes.py` - NEW file
- `gateways/pairing_serializers.py` - NEW file  
- `gateways/views.py` - Pairing endpoints
- `gateways/urls.py` - Pairing URLs
- `smarthome_cloud/consumers.py` - JWT validation

**Must run:**
- `python manage.py makemigrations`
- `python manage.py migrate`
- `sudo systemctl restart smarthome-cloud`
