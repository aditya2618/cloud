# Production Cloud Architecture - Setup Guide

## 🎯 Overview

Production-ready smart home cloud architecture following industry best practices (Home Assistant Cloud, AWS IoT Core).

**Components Updated**:
1. **Cloud Server** - JWT auth, pairing codes, WebSocket proxy
2. **Local Server** - Cloud client for remote access
3. **Mobile App** - JWT authentication with home_ids

---

## 📦 Cloud Server Setup

```bash
cd d:\PROJECT\esp32-flasher\cloud
& cloud/Scripts/Activate.ps1
python manage.py migrate
python manage.py runserver 0.0.0.0:9000
```

## 🏠 Local Server Setup

Create `.env` file:
```bash
CLOUD_ENABLED=true
CLOUD_BRIDGE_URL=ws://localhost:9000/ws/gateway/
```

Start server:
```bash
cd d:\PROJECT\esp32-flasher\server
& server/Scripts/Activate.ps1
python manage.py runserver 0.0.0.0:8000
```

## 📱 Mobile App

Updated `cloudClient.ts` with:
- JWT with homes storage
- `requestPairingCode()` - Generate 8-digit code
- `verifyPairingCode()` - Check validity
- `listGateways()` - List gateways

## 🧪 Testing

```bash
cd d:\PROJECT\esp32-flasher\cloud
python test_production_architecture.py
```

## API Endpoints

- `POST /api/auth/login` - Login (returns JWT + homes)
- `POST /api/gateways/request-pairing` - Get pairing code
- `GET /api/gateways/verify-pairing/{code}` - Verify code
- `POST /api/gateways/complete-pairing` - Register gateway

See walkthrough.md for full documentation.
