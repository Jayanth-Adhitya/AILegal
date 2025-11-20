# VPS Deployment Guide - contract.cirilla.ai

Deploy Legal Agent on your VPS with custom domains separate from Azure deployment.

## Domain Architecture

### VPS Deployment (contract.cirilla.ai)
- **Frontend**: `https://contract.cirilla.ai`
- **Backend API**: `https://api.contract.cirilla.ai`
- **Collaboration Server**: `https://collab.contract.cirilla.ai`
- **Word Add-in**: `https://word.contract.cirilla.ai`

### Azure Deployment (contracts.cirilla.ai) - Separate
- **Frontend**: `https://contracts.cirilla.ai`
- **Backend API**: `https://api.cirilla.ai`
- **Collaboration Server**: `https://collab.cirilla.ai`

Both deployments work independently with proper CORS configuration.

---

## Prerequisites

1. **VPS Server** with:
   - Ubuntu 20.04/22.04 or Debian 11/12
   - At least 4GB RAM, 2 CPU cores
   - 20GB storage
   - Root or sudo access

2. **Docker & Docker Compose** installed
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

3. **Reverse Proxy** (choose one):
   - **Option A**: Traefik (recommended - auto SSL)
   - **Option B**: Nginx + Certbot
   - **Option C**: Caddy (easiest)

4. **DNS Records** configured:
   ```
   Type  Name      Value (Your VPS IP)
   A     contract  123.456.789.10
   A     api       123.456.789.10
   A     collab    123.456.789.10
   A     word      123.456.789.10
   ```

---

## Deployment Steps

### Step 1: Upload Code to VPS

```bash
# On your local machine
scp -r "C:\Files\JaziriX\Legal Agent" root@your-vps-ip:/opt/legal-agent

# OR clone from git (recommended)
ssh root@your-vps-ip
cd /opt
git clone https://github.com/yourusername/legal-agent.git
cd legal-agent
```

### Step 2: Configure Environment

```bash
# Copy VPS environment file
cp .env.vps .env

# Edit if needed (API keys, domains, etc.)
nano .env
```

**Important**: Make sure these values are set correctly:
```env
NEXT_PUBLIC_API_URL=https://api.contract.cirilla.ai
NEXT_PUBLIC_COLLAB_URL=https://collab.contract.cirilla.ai
CORS_ORIGINS=https://contract.cirilla.ai,https://api.contract.cirilla.ai,https://collab.contract.cirilla.ai,https://word.contract.cirilla.ai
```

### Step 3: Set Up Reverse Proxy

#### Option A: Traefik (Recommended)

Create `traefik.yml`:
```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    container_name: traefik
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik-config:/etc/traefik
      - ./letsencrypt:/letsencrypt
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=your@email.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    networks:
      - legal-agent

networks:
  legal-agent:
    external: true
```

Start Traefik:
```bash
# Create network
docker network create legal-agent

# Start Traefik
docker-compose -f traefik.yml up -d
```

#### Option B: Nginx + Certbot

Create `/etc/nginx/sites-available/legal-agent`:
```nginx
# Frontend (contract.cirilla.ai)
server {
    listen 80;
    server_name contract.cirilla.ai;

    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Backend API (api.contract.cirilla.ai)
server {
    listen 80;
    server_name api.contract.cirilla.ai;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Collaboration Server (collab.contract.cirilla.ai)
server {
    listen 80;
    server_name collab.contract.cirilla.ai;

    location / {
        proxy_pass http://localhost:1234;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Word Add-in (word.contract.cirilla.ai)
server {
    listen 80;
    server_name word.contract.cirilla.ai;

    location / {
        proxy_pass http://localhost:3002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable and get SSL:
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/legal-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificates
sudo certbot --nginx -d contract.cirilla.ai -d api.contract.cirilla.ai -d collab.contract.cirilla.ai -d word.contract.cirilla.ai
```

### Step 4: Deploy Application

```bash
# Build and start all services
docker-compose -f docker-compose.vps.yml up -d --build

# Check status
docker-compose -f docker-compose.vps.yml ps

# View logs
docker-compose -f docker-compose.vps.yml logs -f
```

### Step 5: Verify Deployment

```bash
# Test backend health
curl https://api.contract.cirilla.ai/health

# Test frontend
curl -I https://contract.cirilla.ai

# Test collaboration server
curl https://collab.contract.cirilla.ai/health
```

Open in browser:
- https://contract.cirilla.ai - Should show login page
- https://api.contract.cirilla.ai/docs - Should show API documentation

---

## Update Deployment

When you make code changes:

```bash
# Pull latest code
cd /opt/legal-agent
git pull

# Rebuild and restart
docker-compose -f docker-compose.vps.yml up -d --build

# Or rebuild specific service
docker-compose -f docker-compose.vps.yml up -d --build frontend
docker-compose -f docker-compose.vps.yml up -d --build backend
```

---

## Monitoring & Logs

```bash
# View all logs
docker-compose -f docker-compose.vps.yml logs -f

# View specific service logs
docker-compose -f docker-compose.vps.yml logs -f backend
docker-compose -f docker-compose.vps.yml logs -f frontend

# Check resource usage
docker stats
```

---

## Backup

```bash
# Backup data volume
docker run --rm -v legal-agent_backend_data:/data -v $(pwd)/backups:/backup ubuntu tar czf /backup/backend-data-$(date +%Y%m%d).tar.gz /data

# Restore backup
docker run --rm -v legal-agent_backend_data:/data -v $(pwd)/backups:/backup ubuntu tar xzf /backup/backend-data-YYYYMMDD.tar.gz -C /
```

---

## Troubleshooting

### CORS Errors

Check backend logs for CORS origins:
```bash
docker-compose -f docker-compose.vps.yml logs backend | grep "CORS allowed origins"
```

Should show:
```
CORS allowed origins: ['https://contract.cirilla.ai', 'https://api.contract.cirilla.ai', ...]
```

### SSL Certificate Issues

If using Certbot:
```bash
# Renew certificates
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

### Port Conflicts

Check if ports are in use:
```bash
sudo netstat -tulpn | grep -E ':(80|443|8000|3001|1234)'
```

### Container Not Starting

```bash
# Check container status
docker-compose -f docker-compose.vps.yml ps

# View detailed logs
docker-compose -f docker-compose.vps.yml logs backend
docker-compose -f docker-compose.vps.yml logs frontend

# Restart service
docker-compose -f docker-compose.vps.yml restart backend
```

---

## Firewall Configuration

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## Performance Tuning

### Increase Docker Resources

Edit `/etc/docker/daemon.json`:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
```

Restart Docker:
```bash
sudo systemctl restart docker
```

### Scale Replicas (if needed)

```bash
# Scale frontend
docker-compose -f docker-compose.vps.yml up -d --scale frontend=3
```

---

## Security Checklist

- [ ] SSL certificates installed and auto-renewing
- [ ] Firewall configured (only ports 80, 443, 22 open)
- [ ] Environment variables not committed to git
- [ ] Regular backups scheduled
- [ ] Docker daemon secured
- [ ] SSH key-based authentication only
- [ ] Fail2ban installed for SSH protection

---

## Quick Reference

### Useful Commands

```bash
# Stop all services
docker-compose -f docker-compose.vps.yml down

# Stop and remove volumes (careful!)
docker-compose -f docker-compose.vps.yml down -v

# Rebuild specific service
docker-compose -f docker-compose.vps.yml build frontend
docker-compose -f docker-compose.vps.yml up -d frontend

# Check disk usage
docker system df

# Clean up unused images
docker image prune -a
```

### Environment Variables

All configuration is in `.env` file:
- `NEXT_PUBLIC_API_URL` - Frontend API URL
- `NEXT_PUBLIC_COLLAB_URL` - Collaboration server URL
- `CORS_ORIGINS` - Allowed CORS origins
- `GOOGLE_API_KEY` - Google AI API key

---

## Support

- Check logs first: `docker-compose -f docker-compose.vps.yml logs -f`
- Verify DNS: `nslookup contract.cirilla.ai`
- Test connectivity: `curl https://api.contract.cirilla.ai/health`
- Check CORS: Browser console for CORS errors
