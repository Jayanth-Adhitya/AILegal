# Deployment Comparison: VPS vs Azure

This document explains the two separate deployments and how they work together.

## Overview

You have **TWO independent deployments** of the Legal Agent application:

### 1. VPS Deployment (contract.cirilla.ai)
- **Infrastructure**: Your own VPS server
- **Control**: Full control over infrastructure
- **Domains**: `contract.cirilla.ai`, `api.contract.cirilla.ai`, etc.
- **Purpose**: Primary production environment
- **Config File**: `docker-compose.vps.yml`
- **Environment**: `.env.vps`

### 2. Azure Deployment (contracts.cirilla.ai)
- **Infrastructure**: Azure Container Apps
- **Control**: Managed by Azure
- **Domains**: `contracts.cirilla.ai`, `api.cirilla.ai`, etc.
- **Purpose**: Cloud-hosted backup/alternative
- **Config File**: `docker-compose.azure.yml`
- **Environment**: `.env.azure.local`

---

## Domain Mapping

| Service | VPS Domain | Azure Domain |
|---------|-----------|--------------|
| Frontend | `contract.cirilla.ai` | `contracts.cirilla.ai` |
| Backend API | `api.contract.cirilla.ai` | `api.cirilla.ai` |
| Collaboration | `collab.contract.cirilla.ai` | `collab.cirilla.ai` |
| Word Add-in | `word.contract.cirilla.ai` | `word-addin.niceground-5231e36c.uaenorth.azurecontainerapps.io` |

---

## CORS Configuration

The backend automatically allows **both** sets of domains:

```python
# Allowed origins (from src/api.py)
origins = [
    # VPS domains
    "https://contract.cirilla.ai",
    "https://api.contract.cirilla.ai",
    "https://collab.contract.cirilla.ai",
    "https://word.contract.cirilla.ai",

    # Azure domains
    "https://contracts.cirilla.ai",
    "https://api.cirilla.ai",
    "https://collab.cirilla.ai",

    # Development
    "http://localhost:3000",
    "http://localhost:3001",
]
```

This means:
- ✅ VPS frontend can call VPS backend
- ✅ Azure frontend can call Azure backend
- ❌ VPS frontend **cannot** call Azure backend (cross-deployment)
- ❌ Azure frontend **cannot** call VPS backend (cross-deployment)

Each deployment is **isolated** and independent.

---

## When to Use Which Deployment

### Use VPS Deployment (contract.cirilla.ai) When:
- You need full control over infrastructure
- You want to avoid Azure costs
- You need to customize server configuration
- You want faster deployment cycles
- You need direct SSH access to servers

### Use Azure Deployment (contracts.cirilla.ai) When:
- You need global availability (Azure CDN)
- You want auto-scaling capabilities
- You need Azure-specific features
- You want Microsoft's SLA guarantees
- You need integration with other Azure services

---

## Deployment Workflows

### VPS Deployment Workflow

```bash
# 1. Make code changes locally
git add .
git commit -m "feat: new feature"
git push

# 2. SSH to VPS
ssh root@your-vps-ip

# 3. Pull and rebuild
cd /opt/legal-agent
git pull
docker-compose -f docker-compose.vps.yml up -d --build

# 4. Verify
curl https://api.contract.cirilla.ai/health
```

**Time**: ~5-10 minutes

### Azure Deployment Workflow

```cmd
# 1. Build images locally
docker build -f Dockerfile.backend -t legalagentjaacr.azurecr.io/legal-agent-backend:latest .
docker build -f Dockerfile.frontend -t legalagentjaacr.azurecr.io/legal-agent-frontend:latest --build-arg NEXT_PUBLIC_API_URL=https://api.cirilla.ai --build-arg NEXT_PUBLIC_COLLAB_URL=https://collab.cirilla.ai .

# 2. Push to registry
az acr login --name legalagentjaacr
docker push legalagentjaacr.azurecr.io/legal-agent-backend:latest
docker push legalagentjaacr.azurecr.io/legal-agent-frontend:latest

# 3. Update container apps
az containerapp update --name backend-api --resource-group legal-agent-rg --image legalagentjaacr.azurecr.io/legal-agent-backend:latest
az containerapp update --name frontend --resource-group legal-agent-rg --image legalagentjaacr.azurecr.io/legal-agent-frontend:latest

# 4. Purge Cloudflare cache
# (Go to Cloudflare dashboard and purge cache)
```

**Time**: ~15-20 minutes

---

## Data Isolation

### VPS Data Location
```
/opt/legal-agent/backend_data/
├── chroma_db/          # Vector database
├── uploads/            # Uploaded contracts
├── outputs/            # Generated reports
├── policies/           # Company policies
└── legal_ai.db         # SQLite database
```

### Azure Data Location
```
Azure Files Share: legalagentdata
├── chroma_db/          # Vector database
├── uploads/            # Uploaded contracts
├── outputs/            # Generated reports
├── policies/           # Company policies
└── legal_ai.db         # SQLite database
```

**Important**: Data is **NOT** shared between deployments. Each has its own database and file storage.

---

## Configuration Differences

| Setting | VPS | Azure |
|---------|-----|-------|
| Environment File | `.env.vps` | `.env.azure.local` |
| Docker Compose | `docker-compose.vps.yml` | `docker-compose.azure.yml` |
| Frontend URL | `contract.cirilla.ai` | `contracts.cirilla.ai` |
| Backend URL | `api.contract.cirilla.ai` | `api.cirilla.ai` |
| SSL Management | Traefik/Certbot | Azure managed |
| Scaling | Manual (docker-compose scale) | Auto (Azure Container Apps) |
| Monitoring | Docker logs | Azure Monitor |
| Cost | VPS hosting ($10-50/month) | Azure Container Apps (~$30/month) |

---

## Migration Between Deployments

If you need to migrate data from VPS to Azure (or vice versa):

### Export from VPS
```bash
# On VPS
cd /opt/legal-agent
docker run --rm -v legal-agent_backend_data:/data -v $(pwd):/backup ubuntu tar czf /backup/vps-data-backup.tar.gz /data
```

### Import to Azure
```bash
# Download backup
scp root@vps-ip:/opt/legal-agent/vps-data-backup.tar.gz .

# Upload to Azure Files
az storage file upload --account-name legalagentstorage --share-name legalagentdata --source vps-data-backup.tar.gz

# Extract in Azure Container
az containerapp exec --name backend-api --resource-group legal-agent-rg --command "/bin/bash -c 'cd /app && tar xzf /app/data/vps-data-backup.tar.gz -C /app/data --strip-components=1'"
```

---

## Monitoring Both Deployments

### VPS Monitoring
```bash
# Check services
ssh root@vps-ip "docker-compose -f /opt/legal-agent/docker-compose.vps.yml ps"

# View logs
ssh root@vps-ip "docker-compose -f /opt/legal-agent/docker-compose.vps.yml logs --tail=50"

# Check health
curl https://api.contract.cirilla.ai/health
```

### Azure Monitoring
```cmd
# Check status
az containerapp show --name backend-api --resource-group legal-agent-rg --query "properties.runningStatus"

# View logs
az containerapp logs show --name backend-api --resource-group legal-agent-rg --tail 50

# Check health
curl https://api.cirilla.ai/health
```

---

## Recommended Strategy

1. **Primary**: Use VPS deployment (`contract.cirilla.ai`) for day-to-day operations
   - Faster updates
   - Lower cost
   - Full control

2. **Backup**: Use Azure deployment (`contracts.cirilla.ai`) as:
   - High-availability backup
   - Testing ground for major changes
   - Disaster recovery option

3. **DNS Failover**: Configure DNS to failover from VPS to Azure if VPS goes down
   - Use Cloudflare load balancing
   - Or DNS health checks

---

## Summary

- **Two independent deployments** with different domains
- **Same codebase**, different infrastructure
- **Separate databases** and file storage
- **Both fully functional** and production-ready
- **Different use cases**: VPS for control, Azure for scale
- **CORS configured** to support both simultaneously

Choose the deployment that best fits your current needs, or use both for redundancy!
