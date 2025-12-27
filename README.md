# Smart Home Cloud Backend

Production-grade cloud backend for offline-first smart home platform.

## Overview

This is the **cloud component** of the offline-first smart home architecture. It provides:

- **Remote Access**: Control your home from anywhere via secure cloud relay
- **Multi-Tenant**: Multiple users can access shared homes with role-based permissions
- **Offline-First**: Local control always works; cloud is optional
- **Secure Bridge**: NAT-friendly WebSocket connection from edge gateways
- **JWT Authentication**: Industry-standard token-based auth

## Architecture

```
Mobile App (Remote)
        ↕ HTTPS/REST
Cloud Backend (This Project)
        ↕ WSS/TLS (Bridge)
Edge Gateway (Local Django)
        ↕ MQTT
ESP32 Devices
```

## Features

### ✅ Built
- User authentication (email/password with JWT)
- Gateway provisioning with secure secret generation
- Multi-tenant home permissions (owner/admin/user/viewer)
- WebSocket bridge for secure edge-cloud communication
- Session tracking and monitoring
- Admin interface for management

### 🚧 Next Phase
- Edge client implementation (WebSocket client on local Django)
- Remote control API (relay commands through bridge)
- State caching for offline resilience
- Mobile app dual-mode networking

## Tech Stack

- **Framework**: Django 5.2 + Django REST Framework
- **WebSockets**: Django Channels + Daphne
- **Database**: PostgreSQL (production) / SQLite (development)
- **Cache**: Redis
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Deployment**: Gunicorn + NGINX (production)

## Installation

### 1. Set up virtual environment
```bash
python -m venv cloud
cloud\Scripts\activate  # Windows
# or: source cloud/bin/activate  # Linux/Mac
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Run migrations
```bash
python manage.py migrate
```

### 5. Create superuser
```bash
python manage.py createsuperuser
```

### 6. Start development server
```bash
# HTTP/REST + WebSocket
python manage.py runserver
# or with Daphne (ASGI server):
daphne -b 0.0.0.0 -p 8000 smarthome_cloud.asgi:application
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (get JWT tokens)
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout (blacklist refresh token)
- `GET /api/auth/profile` - Get current user profile
- `PATCH /api/auth/profile` - Update profile
- `POST /api/auth/change-password` - Change password

### Gateway Management
- `POST /api/gateways/provision` - Provision new gateway
- `GET /api/gateways/` - List user's gateways
- `GET /api/gateways/{id}/` - Get gateway details
- `PATCH /api/gateways/{id}/` - Update gateway
- `DELETE /api/gateways/{id}/` - Delete gateway (soft delete)
- `POST /api/gateways/{id}/revoke` - Revoke gateway access

### Home Permissions
- `GET /api/gateways/homes/{home_id}/permissions/` - List permissions
- `POST /api/gateways/homes/{home_id}/permissions/` - Grant permission

## WebSocket Bridge

### Connection
```
wss://your-cloud-domain.com/bridge/?gateway_id=<UUID>&secret=<SECRET>
```

### Message Format
```json
{
  "type": "command | state | sync | ping | pong | ack",
  "request_id": "uuid",
  "timestamp": 1735288000,
  "payload": {}
}
```

### Message Types
- `ping` - Heartbeat from edge
- `pong` - Heartbeat response
- `command` - Control command from cloud to edge
- `ack` - Command acknowledgment from edge
- `state` - State update from edge
- `sync` - Metadata sync (devices, scenes, etc.)

## Security

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Change `SECRET_KEY`
- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall
- [ ] Set up rate limiting
- [ ] Enable logging/monitoring
- [ ] Regular security updates

### Authentication Flow
1. User registers/logs in → Receives JWT tokens
2. Edge gateway provisions → Receives gateway_id + secret
3. Edge connects via WebSocket → Authenticates with gateway_id + secret
4. Commands relay through authenticated connection

## Development

### Project Structure
```
smarthome_cloud/
├── accounts/          # User authentication
├── gateways/          # Gateway provisioning
├── bridge/            # WebSocket bridge server
├── homes/             # Home metadata
└── smarthome_cloud/   # Project settings
```

### Database Models
- **CloudUser**: Email-based user accounts
- **Gateway**: Edge gateway registration
- **HomePermission**: Multi-tenant access control
- **BridgeSession**: Active WebSocket connections
- **HomeMetadata**: Synced home data from edge

## Deployment

### Docker (Recommended)
```bash
# Coming in next phase
```

### Manual
1. Set up PostgreSQL database
2. Set up Redis
3. Configure NGINX reverse proxy
4. Use Gunicorn for WSGI + Daphne for ASGI
5. Set up SSL certificates (Let's Encrypt)
6. Configure systemd services

## Monitoring

- Admin: http://your-domain.com/admin
- Active bridges: Check `BridgeSession` model in admin
- Gateway status: Check `Gateway.last_seen` and `status` fields

## Next Steps

1. **Implement Edge Client**: WebSocket client on local Django
2. **Remote Control API**: Command relay through bridge
3. **State Synchronization**: Cache device states
4. **Mobile App Update**: Dual-mode networking (local/cloud)

## License

[Your License Here]

## Support

[Your Support Info Here]
