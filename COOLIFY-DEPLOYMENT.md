# Coolify Deployment Guide - contract.cirilla.ai

Deploy Legal Agent on Coolify with custom domains and automatic SSL management.

## Overview

Coolify manages the entire deployment process including:
- ✅ Domain routing (configured in Coolify UI)
- ✅ SSL certificates (automatic via Let's Encrypt)
- ✅ Reverse proxy (Coolify's managed Traefik)
- ✅ Container orchestration

**Your Domain Configuration:**
- **Frontend**: `https://contract.cirilla.ai`
- **Backend API**: `https://api.contract.cirilla.ai`
- **Collaboration Server**: `https://collab.contract.cirilla.ai`
- **Word Add-in**: `https://word.contract.cirilla.ai`

---

## Prerequisites

1. **Coolify** installed and running on your VPS
2. **GitHub repository** with latest code (already pushed)
3. **API Keys**: Google AI API key (required), Groq API key (optional)
4. **DNS Records** pointing to your VPS IP:
   ```
   Type  Name      Value (Your VPS IP)
   A     contract  your-vps-ip
   A     api       your-vps-ip
   A     collab    your-vps-ip
   A     word      your-vps-ip
   ```

---

## Deployment Steps

### Step 1: Create New Project in Coolify

1. Log in to Coolify dashboard
2. Click **"+ New Resource"** → **"Docker Compose"**
3. Select your server
4. Choose **"From Git Repository"**

### Step 2: Configure Git Repository

1. **Repository URL**: `https://github.com/yourusername/legal-agent`
2. **Branch**: `main`
3. **Docker Compose Location**: `docker-compose.vps.yml`
4. **Build Pack**: Docker Compose

### Step 3: Set Environment Variables

In Coolify, go to **Environment Variables** tab and add:

```env
# Required: Google AI API Key
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Groq API Key (for voice features)
GROQ_API_KEY=your_groq_api_key_here

# Frontend URLs (IMPORTANT: Set these exactly)
NEXT_PUBLIC_API_URL=https://api.contract.cirilla.ai
NEXT_PUBLIC_COLLAB_URL=https://collab.contract.cirilla.ai

# CORS Origins (all allowed domains)
CORS_ORIGINS=https://contract.cirilla.ai,https://api.contract.cirilla.ai,https://collab.contract.cirilla.ai,https://word.contract.cirilla.ai

# Internal backend URL for collaboration server
FASTAPI_INTERNAL_URL=http://backend:8000

# AI Model Configuration (defaults are fine)
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=models/gemini-embedding-001
TEMPERATURE=0.1
MAX_OUTPUT_TOKENS=8192

# ChromaDB Configuration
CHROMA_COLLECTION_NAME=legal_policies

# Document Processing
MAX_FILE_SIZE_MB=50
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_K=3

# Performance & Rate Limiting
BATCH_MODE=true
MAX_BATCH_SIZE=50
REQUESTS_PER_MINUTE=15
REQUESTS_PER_DAY=250
```

### Step 4: Configure Domains in Coolify

For **each service**, go to **Domains** section in Coolify:

#### Backend Service
- **Container Name**: `legal-agent-backend`
- **Domain**: `api.contract.cirilla.ai`
- **Port**: `8000`
- **HTTPS**: Enabled (Coolify auto-generates SSL)

#### Frontend Service
- **Container Name**: `legal-agent-frontend`
- **Domain**: `contract.cirilla.ai`
- **Port**: `3001`
- **HTTPS**: Enabled

#### Collaboration Server
- **Container Name**: `legal-agent-collab`
- **Domain**: `collab.contract.cirilla.ai`
- **Port**: `1234`
- **HTTPS**: Enabled

#### Word Add-in Service
- **Container Name**: `legal-agent-word`
- **Domain**: `word.contract.cirilla.ai`
- **Port**: `3001`
- **HTTPS**: Enabled

### Step 5: Deploy

1. Click **"Deploy"** button in Coolify
2. Coolify will:
   - Pull code from GitHub
   - Build Docker images
   - Start containers
   - Configure Traefik routing
   - Generate SSL certificates

**Deployment time**: ~5-10 minutes

### Step 6: Verify Deployment

Check each service:

```bash
# Test backend health
curl https://api.contract.cirilla.ai/health

# Test frontend
curl -I https://contract.cirilla.ai

# Test collaboration server
curl https://collab.contract.cirilla.ai/health
```

Open in browser:
- **Frontend**: https://contract.cirilla.ai
- **API Docs**: https://api.contract.cirilla.ai/docs
- **Collaboration**: https://collab.contract.cirilla.ai/health

---

## Coolify UI Domain Configuration

You've already configured these in Coolify UI:

- ✅ **Backend**: `https://api.contract.cirilla.ai`
- ✅ **Frontend**: `https://contract.cirilla.ai`
- ✅ **Collaboration**: `https://collab.contract.cirilla.ai`
- ✅ **Word Add-in**: `https://word.contract.cirilla.ai`

These match the environment variables in `.env.vps`, so everything is aligned!

---

## Updating Deployment

When you push code changes to GitHub:

1. Go to Coolify dashboard
2. Click **"Redeploy"** button
3. Coolify will:
   - Pull latest code
   - Rebuild changed containers
   - Zero-downtime deployment

**OR** enable **Auto Deploy** in Coolify:
- Settings → Auto Deploy → Enable
- Coolify will auto-deploy on git push

---

## Monitoring

### View Logs in Coolify

1. Go to your project in Coolify
2. Click on a service (e.g., `legal-agent-backend`)
3. Click **"Logs"** tab
4. Real-time logs will appear

### Check Service Status

In Coolify dashboard:
- **Green**: Service running
- **Yellow**: Building/Starting
- **Red**: Error (check logs)

### Resource Usage

Coolify shows:
- CPU usage
- Memory usage
- Network traffic
- Disk usage

---

## Troubleshooting

### Issue: Service Won't Start

**Check logs in Coolify:**
1. Click on the failing service
2. Go to **Logs** tab
3. Look for error messages

**Common fixes:**
- Verify environment variables are set correctly
- Check if ports are conflicting
- Ensure Docker images built successfully

### Issue: Domain Not Accessible

**Verify DNS:**
```bash
nslookup contract.cirilla.ai
nslookup api.contract.cirilla.ai
```

Should resolve to your VPS IP.

**Check Traefik routing:**
In Coolify, verify domain is mapped to correct container and port.

**SSL Certificate:**
- Coolify auto-generates SSL via Let's Encrypt
- First request may take 30-60 seconds
- Check Coolify logs for certificate generation

### Issue: CORS Errors

**Verify CORS_ORIGINS environment variable includes all domains:**
```env
CORS_ORIGINS=https://contract.cirilla.ai,https://api.contract.cirilla.ai,https://collab.contract.cirilla.ai,https://word.contract.cirilla.ai
```

**Check backend logs:**
```bash
# In Coolify, view backend logs
# Look for: "CORS allowed origins: [...]"
```

Should show all your domains.

### Issue: Frontend Shows Old Version

**Clear build cache in Coolify:**
1. Go to project settings
2. Click **"Force Rebuild"**
3. Redeploy

**Or manually rebuild:**
```bash
# SSH to VPS
ssh user@your-vps-ip

# Remove old images
docker system prune -a

# Redeploy in Coolify
```

---

## Data Persistence

Coolify automatically manages volumes:

**Backend Data Volume**: `legal-agent_backend_data`
- Contains: ChromaDB, uploads, SQLite database
- Persists across deployments
- Backed up by Coolify (if configured)

**Backup Data:**

In Coolify:
1. Go to **Volumes** tab
2. Click **"Backup"** on `backend_data` volume
3. Download backup file

**Restore Data:**
1. Upload backup file to Coolify
2. Click **"Restore"** on volume
3. Restart services

---

## Port Mapping Reference

| Service | Container Port | Coolify Domain | HTTPS |
|---------|---------------|----------------|-------|
| Backend | 8000 | api.contract.cirilla.ai | ✅ |
| Frontend | 3001 | contract.cirilla.ai | ✅ |
| Collaboration | 1234 | collab.contract.cirilla.ai | ✅ |
| Word Add-in | 3001 | word.contract.cirilla.ai | ✅ |

---

## Environment Variables Reference

### Required

- **GOOGLE_API_KEY**: Your Google AI API key (required)
- **NEXT_PUBLIC_API_URL**: Frontend API URL (must be HTTPS)
- **NEXT_PUBLIC_COLLAB_URL**: Collaboration server URL (must be HTTPS)
- **CORS_ORIGINS**: Comma-separated list of allowed domains

### Optional

- **GROQ_API_KEY**: Groq API key for voice features
- **GEMINI_MODEL**: AI model to use (default: gemini-2.5-flash)
- **MAX_FILE_SIZE_MB**: Max upload size (default: 50)
- **REQUESTS_PER_MINUTE**: Rate limit (default: 15)

---

## Security Checklist

- [x] SSL certificates auto-generated by Coolify
- [x] Environment variables stored securely in Coolify (not in git)
- [x] CORS origins restricted to specific domains
- [x] Firewall configured (Coolify manages this)
- [x] API keys not committed to repository

---

## Coolify vs Manual VPS Deployment

| Feature | Coolify | Manual VPS |
|---------|---------|------------|
| SSL Management | ✅ Automatic | ❌ Manual (Certbot) |
| Domain Routing | ✅ UI-based | ❌ Manual (Nginx/Traefik config) |
| Deployment | ✅ One-click | ❌ Manual docker-compose |
| Updates | ✅ Git push + auto-deploy | ❌ SSH + git pull + rebuild |
| Monitoring | ✅ Built-in dashboard | ❌ Manual (docker logs) |
| Backups | ✅ Built-in | ❌ Manual scripts |
| Rollbacks | ✅ One-click | ❌ Manual git revert |

**Coolify is recommended** for easier management and faster updates.

---

## Quick Command Reference

### Redeploy All Services
1. Go to Coolify dashboard
2. Click **"Redeploy"**

### View All Logs
1. Coolify dashboard → Project
2. **Logs** tab (shows all services)

### Restart Service
1. Click on service (e.g., `legal-agent-backend`)
2. Click **"Restart"**

### Check Health
```bash
curl https://api.contract.cirilla.ai/health
curl https://contract.cirilla.ai
curl https://collab.contract.cirilla.ai/health
```

---

## Next Steps

1. **Deploy to Coolify** using the steps above
2. **Test all services** at your custom domains
3. **Enable Auto Deploy** for automatic updates on git push
4. **Set up monitoring** alerts in Coolify
5. **Configure backups** for `backend_data` volume

---

## Support

- **Coolify Docs**: https://coolify.io/docs
- **Check logs** in Coolify dashboard first
- **Verify DNS** with `nslookup`
- **Test endpoints** with `curl`
- **Check CORS** in browser console

Your deployment is ready to go! All code changes are in Git, environment variables are documented, and domains are configured in Coolify UI.
