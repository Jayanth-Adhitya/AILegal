# Troubleshooting "No Available Server" in Coolify

## Problem
Accessing `https://ailegal.mehh.ae/` shows "no available server" error.

## Root Cause
This error means Traefik (Coolify's reverse proxy) cannot find healthy containers to route traffic to.

## Solution Steps

### Step 1: Configure Service Domains in Coolify

**Critical**: You must assign domains to each service in Coolify's UI.

#### Frontend Service Configuration
1. In Coolify dashboard, go to your Docker Compose resource
2. Click on the **frontend** service
3. Find "Domains" or "Configuration" section
4. Add domain: `ailegal.mehh.ae`
5. **Port**: Specify `3000` (frontend listens on port 3000, not 80)
6. Enable HTTPS/SSL certificates

#### Backend Service Configuration
1. Click on the **backend** service
2. Add domain: `api.ailegal.mehh.ae` (or your preferred subdomain)
3. **Port**: Specify `8000` (backend listens on port 8000)
4. Enable HTTPS/SSL certificates

### Step 2: Update NEXT_PUBLIC_API_URL
In Coolify environment variables:
```
NEXT_PUBLIC_API_URL=https://api.ailegal.mehh.ae
```
This tells the frontend where to find the backend.

### Step 3: Push Updated docker-compose.yml
The updated docker-compose.yml now includes Traefik labels:
```bash
git add docker-compose.yml
git commit -m "Add Traefik labels for Coolify routing"
git push origin main
```

### Step 4: Force Redeploy in Coolify
1. In Coolify dashboard, find your resource
2. Click **"Force Deploy"** or **"Redeploy"**
3. Watch deployment logs for errors

### Step 5: Verify Container Status
SSH into your Coolify server:
```bash
# Check if containers are running
docker ps

# Check for your containers - look for "unhealthy" status
docker ps | grep legal

# View logs
docker logs <container-name>

# Check health status
docker inspect <container-name> | grep -A 10 Health
```

## Common Issues & Fixes

### Issue 1: Health Checks Failing
**Symptoms**: Containers show as "unhealthy" or constantly restarting

**Check**:
```bash
docker ps
# Look for Status column showing "(unhealthy)"
```

**Fix**:
- Ensure `GOOGLE_API_KEY` is set correctly in Coolify
- Check container logs: `docker logs <container-name>`
- Health check endpoints:
  - Backend: `curl http://localhost:8000/health`
  - Frontend: `curl http://localhost:3000`

### Issue 2: Port Not Specified
**Symptoms**: "No available server" but containers are healthy

**Fix**: In Coolify service settings, explicitly set:
- Frontend port: `3000`
- Backend port: `8000`

According to Coolify docs:
> "If services listen on port 80, assigning a domain is enough. **If they're listening on other ports, add that port to the domain**."

### Issue 3: Wrong Domain Format
**Correct formats**:
- `ailegal.mehh.ae` (frontend)
- `api.ailegal.mehh.ae` (backend)

**Incorrect**:
- `http://ailegal.mehh.ae` (don't include protocol in Coolify domain field)
- `ailegal.mehh.ae/` (no trailing slash)

### Issue 4: Backend Not Reachable from Frontend
**Symptoms**: Frontend loads but can't connect to backend

**Check**:
1. Verify `NEXT_PUBLIC_API_URL` points to correct backend domain
2. Ensure both services are in same docker network
3. Check backend logs for CORS errors

**Fix**:
```bash
# In Coolify environment variables
NEXT_PUBLIC_API_URL=https://api.ailegal.mehh.ae
```

### Issue 5: Old Container Still Running
**Symptoms**: Changes not taking effect after redeploy

**Fix**:
```bash
# SSH into server
docker ps -a | grep legal

# Stop old containers
docker stop <container-id>
docker rm <container-id>

# Then redeploy in Coolify
```

## Debugging Commands

### Check Container Status
```bash
docker ps
docker ps -a  # Include stopped containers
```

### View Logs
```bash
# Real-time logs
docker logs -f <container-name>

# Last 100 lines
docker logs --tail 100 <container-name>
```

### Check Network
```bash
# List networks
docker network ls

# Inspect network
docker network inspect <network-name>

# Check if containers are in same network
docker inspect <container-name> | grep -A 20 Networks
```

### Test Health Endpoints
```bash
# From inside container
docker exec <container-name> curl http://localhost:8000/health
docker exec <container-name> curl http://localhost:3000

# From host (if ports are exposed)
curl http://localhost:8000/health
```

### Check Traefik Labels
```bash
# View container labels
docker inspect <container-name> | grep -A 50 Labels
```

## Alternative: Simplified Deployment

If you continue having issues, use the simplified docker-compose:

1. In Coolify, change Docker Compose location to: `/docker-compose.coolify.yml`
2. This version has explicit Traefik labels
3. Redeploy

## Expected Behavior After Fix

✅ **Healthy Deployment**:
- `docker ps` shows containers with "healthy" status
- `https://ailegal.mehh.ae/` loads the frontend
- `https://api.ailegal.mehh.ae/docs` shows FastAPI documentation
- Frontend can communicate with backend

## Still Not Working?

### Check Coolify Logs
In Coolify dashboard:
1. Go to resource
2. View deployment logs
3. Look for specific error messages

### Check Traefik Dashboard
If enabled in Coolify:
1. Access Traefik dashboard
2. Check if services are registered
3. Verify routing rules

### DNS Issues
```bash
# Check DNS resolution
nslookup ailegal.mehh.ae
dig ailegal.mehh.ae

# Should point to your Coolify server IP
```

### Firewall
Ensure ports 80 and 443 are open on your Coolify server:
```bash
# Check firewall status
sudo ufw status

# Should show:
# 80/tcp    ALLOW
# 443/tcp   ALLOW
```

## Key Takeaways

1. **Always assign domains in Coolify UI** - docker-compose alone isn't enough
2. **Specify ports** for services not on port 80
3. **Check health checks** - unhealthy containers won't receive traffic
4. **Use Traefik labels** to help Coolify route correctly
5. **Update NEXT_PUBLIC_API_URL** to actual backend domain

## Contact Points

- Coolify Docs: https://coolify.io/docs/troubleshoot/applications/no-available-server
- GitHub Issues: https://github.com/coollabsio/coolify/issues
- Community Discord: https://discord.gg/coolify
