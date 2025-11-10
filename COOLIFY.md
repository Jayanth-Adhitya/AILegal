# Coolify Deployment Guide

This guide provides step-by-step instructions for deploying the AI Legal Assistant to Coolify.

## Prerequisites

- A Coolify server (self-hosted or managed)
- Git repository with this code (GitHub, GitLab, etc.)
- Google API Key (Gemini API)

## Important: Port Configuration

**For Coolify deployments**, the `docker-compose.yml` uses `expose` instead of `ports`. This allows Coolify's reverse proxy to handle port mapping without conflicts.

**For local testing**, use `docker-compose.local.yml` which includes port mappings:
```bash
docker-compose -f docker-compose.local.yml up -d
```

## Deployment Steps

### 1. Prepare Your Repository

Ensure your code is pushed to a Git repository:

```bash
git add .
git commit -m "Prepare for Coolify deployment"
git push origin main
```

### 2. Create a New Project in Coolify

1. Log in to your Coolify dashboard
2. Click **"+ New"** → **"Project"**
3. Give your project a name (e.g., "AI Legal Assistant")
4. Click **"Create"**

### 3. Add Your Repository

1. In your project, click **"+ New"** → **"Resource"**
2. Select **"Docker Compose"**
3. Configure the source:
   - **Source**: Choose your Git provider (GitHub, GitLab, etc.)
   - **Repository**: Select or enter your repository URL
   - **Branch**: `main` (or your deployment branch)
   - **Docker Compose Location**: `/docker-compose.yml`

**Note**: The docker-compose.yml uses `expose` instead of `ports` to avoid port conflicts. Coolify will automatically handle port mapping through its reverse proxy.

### 4. Configure Environment Variables

In the Coolify resource settings, add the following environment variables:

#### Required Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `GOOGLE_API_KEY` | Your actual API key | **REQUIRED** - Your Google Gemini API key |

#### Production Variables

| Variable | Value | Notes |
|----------|-------|-------|
| `NEXT_PUBLIC_API_URL` | `https://api.yourdomain.com` | Replace with your actual backend domain |
| `BACKEND_PORT` | `8000` | Optional - default is 8000 |
| `FRONTEND_PORT` | `3000` | Optional - default is 3000 |

#### Optional Configuration (with defaults)

```
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=models/gemini-embedding-001
TEMPERATURE=0.1
MAX_OUTPUT_TOKENS=8192
BATCH_MODE=true
MAX_BATCH_SIZE=50
REQUESTS_PER_MINUTE=15
REQUESTS_PER_DAY=250
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_K=3
MAX_FILE_SIZE_MB=50
```

### 5. Configure Domains

Coolify will automatically generate domains for your services, or you can use custom domains:

#### Backend Service
- **Auto-generated**: `https://[random].coolify.io`
- **Custom domain**: `api.yourdomain.com`
- **Port**: 8000

#### Frontend Service
- **Auto-generated**: `https://[random].coolify.io`
- **Custom domain**: `yourdomain.com` or `app.yourdomain.com`
- **Port**: 3000

**Important**: Update `NEXT_PUBLIC_API_URL` to match your backend domain!

### 6. Configure Persistent Storage

Coolify should automatically detect the volume from docker-compose.yml:
- Volume name: `backend_data`
- Mount path: `/app/data`

This volume persists:
- Uploaded contracts
- Generated reports
- Company policies
- Vector database (ChromaDB)

### 7. Deploy

1. Click **"Deploy"** in Coolify
2. Monitor the build logs
3. Wait for both services to become healthy (green status)

### 8. Post-Deployment Setup

1. **Access your application**: Visit your frontend domain
2. **Upload policies**: Go to Policies page → Upload your company policies
3. **Reingest**: Click "Reingest Policies" to build the vector database
4. **Test**: Analyze a sample contract

## Architecture in Coolify

```
Internet
   │
   ├─> Frontend (Next.js)
   │   ├─> Port: 3000
   │   └─> Domain: yourdomain.com
   │
   └─> Backend (FastAPI)
       ├─> Port: 8000
       ├─> Domain: api.yourdomain.com
       └─> Volume: backend_data
```

## Monitoring

### Health Checks

Coolify automatically monitors health checks configured in docker-compose.yml:

- **Backend**: `GET /health` every 30s
- **Frontend**: HTTP check on port 3000 every 30s

### Logs

View logs in Coolify dashboard:
1. Go to your resource
2. Click **"Logs"** tab
3. Select service (backend or frontend)
4. View real-time logs

### Resource Usage

Monitor CPU, memory, and network usage in the Coolify dashboard.

## Updating the Application

### Method 1: Auto-Deploy (Recommended)

Enable automatic deployments in Coolify:
1. Go to resource settings
2. Enable **"Auto Deploy"**
3. Coolify will automatically deploy when you push to your branch

### Method 2: Manual Deploy

1. Push changes to your Git repository
2. In Coolify, click **"Deploy"**
3. Coolify will pull latest code and redeploy

## Troubleshooting

### Issue: Port Already Allocated Error

**Error**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution**:
- Ensure you're using the main `docker-compose.yml` (not docker-compose.local.yml)
- The main docker-compose.yml uses `expose` instead of `ports`
- Stop any existing containers: In Coolify, delete the old deployment before creating new one
- Coolify handles port mapping automatically via its reverse proxy

### Issue: Build Fails

**Check build logs** in Coolify for specific errors.

Common causes:
- Missing dependencies in Dockerfile
- Invalid docker-compose.yml syntax
- Build timeout (increase in Coolify settings)
- Port conflicts (use `expose` not `ports` in docker-compose.yml)

### Issue: Frontend Can't Connect to Backend

**Solution**: Verify `NEXT_PUBLIC_API_URL` environment variable:
- Should point to your **backend domain**
- Must include protocol: `https://api.yourdomain.com`
- No trailing slash

### Issue: Backend Health Check Failing

**Possible causes**:
1. `GOOGLE_API_KEY` not set correctly
2. Database initialization issue
3. Port not accessible

**Check**:
```bash
# View backend logs in Coolify
# Look for startup errors
```

### Issue: Data Lost After Restart

**Solution**: Ensure persistent volume is configured:
1. Check Coolify resource → **Volumes** tab
2. Verify `backend_data` volume exists
3. Check mount path is `/app/data`

### Issue: SSL/HTTPS Not Working

Coolify automatically provisions SSL certificates via Let's Encrypt:
1. Ensure your domain DNS is pointing to Coolify server
2. Wait a few minutes for certificate provisioning
3. Check Coolify logs for SSL errors

## Scaling

### Horizontal Scaling

To handle more traffic, scale backend instances:

1. In Coolify, duplicate the backend service
2. Use a load balancer (Coolify supports this)
3. Both instances will share the same volume

### Vertical Scaling

Increase resources for services:
1. Go to resource settings in Coolify
2. Adjust CPU/Memory limits
3. Redeploy

## Backup and Recovery

### Backup Data

Coolify provides automatic volume backups. Manually backup:

1. Access your Coolify server via SSH
2. Locate the volume:
   ```bash
   docker volume ls | grep backend_data
   ```
3. Backup:
   ```bash
   docker run --rm -v [volume_name]:/data -v $(pwd):/backup \
     alpine tar czf /backup/legal-assistant-backup.tar.gz -C /data .
   ```

### Restore Data

1. Stop the service in Coolify
2. Restore backup to volume
3. Restart service

## Security Best Practices

1. **Use Secrets**: Store `GOOGLE_API_KEY` in Coolify secrets, not plain environment variables
2. **Enable HTTPS**: Always use SSL (Coolify does this automatically)
3. **Firewall**: Ensure only necessary ports are exposed
4. **Updates**: Keep Docker images updated
5. **Monitoring**: Set up alerts in Coolify for service failures

## Cost Optimization

- **API Usage**: Monitor `REQUESTS_PER_MINUTE` and `REQUESTS_PER_DAY` to stay within free tier
- **Batch Mode**: Keep `BATCH_MODE=true` to maximize free tier quota
- **Resources**: Start with minimal CPU/RAM and scale as needed

## Support

- **Coolify Issues**: [Coolify GitHub](https://github.com/coollabsio/coolify)
- **Application Issues**: Check logs in Coolify dashboard
- **Docker Issues**: Refer to `README.Docker.md`

## Next Steps After Deployment

1. ✅ Verify both services are running (green status in Coolify)
2. ✅ Access frontend via your domain
3. ✅ Upload company policies
4. ✅ Run policy ingestion
5. ✅ Test contract analysis
6. ✅ Set up monitoring and alerts
7. ✅ Configure automatic backups

Your AI Legal Assistant is now live and ready to use! 🎉
