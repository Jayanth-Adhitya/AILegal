# Azure Deployment Guide - Legal Agent

This guide walks you through deploying the Legal Agent system to **Azure Container Apps**, the simplest and most cost-effective way to run containerized microservices on Azure.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Architecture on Azure](#architecture-on-azure)
- [Step-by-Step Deployment](#step-by-step-deployment)
- [Post-Deployment Configuration](#post-deployment-configuration)
- [Managing Your Deployment](#managing-your-deployment)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Cost Optimization](#cost-optimization)
- [Custom Domains & SSL](#custom-domains--ssl)
- [Migration from Coolify](#migration-from-coolify)

---

## Overview

**Azure Container Apps** provides a serverless container platform that:
- ✅ Deploys directly from Docker/Docker Compose
- ✅ Auto-scales based on traffic (including scale-to-zero)
- ✅ Provides automatic HTTPS with managed certificates
- ✅ Supports WebSocket connections (essential for collaboration)
- ✅ Includes built-in monitoring and logging
- ✅ Offers simple pricing based on usage

### What Gets Deployed

Your deployment will include:

1. **Backend API** - FastAPI server with Gemini AI integration
2. **Frontend** - Next.js web application
3. **Collaboration Server** - Real-time document collaboration via WebSocket
4. **Word Add-in** - Microsoft Word integration
5. **Azure Files Storage** - Persistent storage for SQLite, ChromaDB, and uploads

---

## Prerequisites

### Required Tools

1. **Azure Account** - [Sign up for free](https://azure.microsoft.com/free/) ($200 credit for 30 days)
2. **Azure CLI** - [Install instructions](https://docs.microsoft.com/cli/azure/install-azure-cli)
3. **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop/)
4. **Google AI API Key** - [Get your key](https://aistudio.google.com/app/apikey)

### Verify Installations

```bash
# Check Azure CLI
az --version

# Check Docker
docker --version

# Login to Azure
az login
```

---

## Architecture on Azure

```
┌─────────────────────────────────────────────────────────────┐
│                  Azure Container Apps Environment            │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Frontend   │  │  Backend API │  │ Collab Server│      │
│  │  (Next.js)   │  │  (FastAPI)   │  │  (Node.js)   │      │
│  │              │  │              │  │              │      │
│  │  Port: 3001  │  │  Port: 8000  │  │  Port: 1234  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
│         │                 │                  │              │
│         │                 └──────────────────┘              │
│         │                   Uses Azure Files                │
│         │                          │                        │
│  ┌──────┴───────┐         ┌────────▼────────┐              │
│  │  Word Add-in │         │  Azure Files     │              │
│  │  (React)     │         │  - SQLite DB     │              │
│  │              │         │  - ChromaDB      │              │
│  │  Port: 3001  │         │  - Uploads       │              │
│  └──────────────┘         └─────────────────┘              │
│                                                              │
│  All services get auto-assigned HTTPS URLs:                 │
│  https://<name>.<unique-id>.<region>.azurecontainerapps.io │
└─────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Deployment

### Step 1: Configure Environment Variables

1. Copy the Azure environment template:
```bash
cp .env.azure .env.azure.local
```

2. Edit `.env.azure.local` and fill in required values:

```bash
# Required: Your Google AI API key
GOOGLE_API_KEY=your_actual_api_key_here

# Required: Azure configuration
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=legal-agent-rg
AZURE_LOCATION=eastus  # or your preferred region

# Storage configuration
AZURE_STORAGE_ACCOUNT=legalagentstorage  # Must be globally unique, lowercase, no hyphens
AZURE_STORAGE_SHARE_NAME=legalagentdata

# Optional: Groq API for voice features
GROQ_API_KEY=your_groq_api_key  # Leave empty if not using voice features
```

**How to get your Azure Subscription ID:**
```bash
az account list --output table
```

### Step 2: Run the Deployment Script

#### On Windows (PowerShell):
```powershell
.\deploy-azure.ps1
```

#### On Linux/Mac (Bash):
```bash
chmod +x deploy-azure.sh
./deploy-azure.sh
```

The script will:
1. ✅ Create Azure resource group
2. ✅ Set up Azure Files storage for persistent data
3. ✅ Create Container Apps environment
4. ✅ Build and deploy all 4 services
5. ✅ Configure HTTPS endpoints
6. ✅ Enable WebSocket support with sticky sessions
7. ✅ Display your deployment URLs

**Deployment takes approximately 15-20 minutes.**

### Step 3: Save Your URLs

After deployment completes, you'll see output like:

```
==================================================
  Deployment Complete!
==================================================

Your Legal Agent is now running on Azure:

  Frontend:             https://frontend.abc123.eastus.azurecontainerapps.io
  Backend API:          https://backend-api.abc123.eastus.azurecontainerapps.io
  Collaboration Server: https://collab-server.abc123.eastus.azurecontainerapps.io
  Word Add-in:          https://word-addin.abc123.eastus.azurecontainerapps.io
```

**Save these URLs** - you'll need them for configuration!

---

## Post-Deployment Configuration

### 1. Update CORS Origins

Add your Azure URLs to the backend environment:

```bash
az containerapp update \
  --name backend-api \
  --resource-group legal-agent-rg \
  --set-env-vars "AZURE_CORS_ORIGINS=https://frontend.abc123.eastus.azurecontainerapps.io,https://collab-server.abc123.eastus.azurecontainerapps.io,https://word-addin.abc123.eastus.azurecontainerapps.io"
```

### 2. Upload Company Policies

Upload your company policies to Azure Files storage:

```bash
# Using Azure Storage Explorer (GUI): https://azure.microsoft.com/features/storage-explorer/
# Or using Azure CLI:

# Get storage connection string
az storage account show-connection-string \
  --name legalagentstorage \
  --resource-group legal-agent-rg

# Upload policies
az storage file upload-batch \
  --destination legalagentdata/policies \
  --source ./Data/policies \
  --account-name legalagentstorage
```

### 3. Test Your Deployment

1. **Visit Frontend**: Open your frontend URL in a browser
2. **Create Account**: Register a new user account
3. **Upload Contract**: Test by uploading a sample .docx contract
4. **Verify Analysis**: Ensure the AI analysis completes successfully
5. **Test Collaboration**: Open the same contract in two browser tabs to verify real-time sync

---

## Managing Your Deployment

### View Application Logs

```bash
# Backend logs
az containerapp logs show \
  --name backend-api \
  --resource-group legal-agent-rg \
  --follow

# Frontend logs
az containerapp logs show \
  --name frontend \
  --resource-group legal-agent-rg \
  --follow

# Collaboration server logs
az containerapp logs show \
  --name collab-server \
  --resource-group legal-agent-rg \
  --follow
```

### Update Environment Variables

```bash
az containerapp update \
  --name backend-api \
  --resource-group legal-agent-rg \
  --set-env-vars "TEMPERATURE=0.2" "MAX_OUTPUT_TOKENS=16384"
```

### Scale Applications

```bash
# Manually scale backend
az containerapp update \
  --name backend-api \
  --resource-group legal-agent-rg \
  --min-replicas 2 \
  --max-replicas 20

# Enable scale-to-zero (saves costs when idle)
az containerapp update \
  --name backend-api \
  --resource-group legal-agent-rg \
  --min-replicas 0
```

### Restart an Application

```bash
az containerapp revision restart \
  --name backend-api \
  --resource-group legal-agent-rg
```

### Redeploy After Code Changes

```bash
# Just re-run the deployment script
.\deploy-azure.ps1  # Windows
./deploy-azure.sh   # Linux/Mac
```

---

## Monitoring & Troubleshooting

### Azure Portal Dashboard

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to Resource Groups → `legal-agent-rg`
3. Click on any Container App to see:
   - Real-time metrics (CPU, memory, requests)
   - Live logs
   - Revision history
   - Application insights

### Common Issues

#### Issue: "Storage account name is not available"

**Solution**: The storage account name must be globally unique. Change it in `.env.azure.local`:
```bash
AZURE_STORAGE_ACCOUNT=legalagent<yourname>storage
```

#### Issue: "CORS error when accessing frontend"

**Solution**: Update CORS origins as shown in Post-Deployment step 1.

#### Issue: "WebSocket connection fails"

**Solution**: Ensure sticky sessions are enabled:
```bash
az containerapp ingress sticky-sessions set \
  --name collab-server \
  --resource-group legal-agent-rg \
  --affinity sticky
```

#### Issue: "Out of memory errors"

**Solution**: Increase memory allocation:
```bash
az containerapp update \
  --name backend-api \
  --resource-group legal-agent-rg \
  --cpu 2.0 \
  --memory 4Gi
```

### Health Check Endpoints

- Backend: `https://<backend-url>/health`
- Frontend: `https://<frontend-url>/` (should return 200)
- Collaboration: `https://<collab-url>/health`

---

## Cost Optimization

### Estimated Monthly Costs

With **Consumption Plan** (pay-per-use):

| Usage Level | Monthly Cost |
|-------------|--------------|
| **Development/Testing** (low traffic, scale-to-zero enabled) | $10-30 |
| **Small Production** (100-500 requests/day) | $30-60 |
| **Medium Production** (1000-5000 requests/day) | $60-150 |
| **High Production** (10,000+ requests/day) | $150-500 |

**Included Free Tier (per month):**
- 180,000 vCPU-seconds
- 360,000 GiB-seconds
- 2 million requests

### Cost-Saving Tips

1. **Enable scale-to-zero** for non-production environments:
```bash
az containerapp update --name backend-api --resource-group legal-agent-rg --min-replicas 0
```

2. **Reduce resource allocation** for development:
```bash
az containerapp update --name backend-api --resource-group legal-agent-rg --cpu 0.5 --memory 1Gi
```

3. **Delete when not in use**:
```bash
az group delete --name legal-agent-rg --yes
```

4. **Monitor costs** in Azure Portal → Cost Management

---

## Custom Domains & SSL

### Add Custom Domain

1. **Configure DNS** (at your domain registrar):
```
Type: CNAME
Name: api
Value: backend-api.abc123.eastus.azurecontainerapps.io
```

2. **Add domain to Container App**:
```bash
az containerapp hostname add \
  --name backend-api \
  --resource-group legal-agent-rg \
  --hostname api.yourdomain.com
```

3. **SSL certificates are managed automatically** by Azure!

### Example Custom Domain Setup

```bash
# Backend API
az containerapp hostname add --name backend-api --resource-group legal-agent-rg --hostname api.yourdomain.com

# Frontend
az containerapp hostname add --name frontend --resource-group legal-agent-rg --hostname app.yourdomain.com

# Collaboration Server
az containerapp hostname add --name collab-server --resource-group legal-agent-rg --hostname collab.yourdomain.com
```

---

## Migration from Coolify

If you're currently running on Coolify and want to migrate to Azure:

### Step 1: Backup Your Data

```bash
# Backup SQLite database
docker cp <backend-container>:/app/data/legal_ai.db ./backup/

# Backup ChromaDB
docker cp <backend-container>:/app/data/chroma_db ./backup/

# Backup uploads
docker cp <backend-container>:/app/data/uploads ./backup/
```

### Step 2: Deploy to Azure

Follow the standard deployment steps above.

### Step 3: Restore Data to Azure Files

```bash
# Get storage credentials
STORAGE_KEY=$(az storage account keys list \
  --account-name legalagentstorage \
  --resource-group legal-agent-rg \
  --query "[0].value" --output tsv)

# Upload database
az storage file upload \
  --share-name legalagentdata \
  --source ./backup/legal_ai.db \
  --path legal_ai.db \
  --account-name legalagentstorage \
  --account-key $STORAGE_KEY

# Upload ChromaDB (directory)
az storage file upload-batch \
  --destination legalagentdata/chroma_db \
  --source ./backup/chroma_db \
  --account-name legalagentstorage \
  --account-key $STORAGE_KEY

# Upload files
az storage file upload-batch \
  --destination legalagentdata/uploads \
  --source ./backup/uploads \
  --account-name legalagentstorage \
  --account-key $STORAGE_KEY
```

### Step 4: Update DNS

Update your DNS records to point to Azure Container Apps URLs instead of Coolify.

---

## Advanced Configuration

### Environment Variables Reference

All environment variables can be updated via:

```bash
az containerapp update \
  --name <app-name> \
  --resource-group legal-agent-rg \
  --set-env-vars "KEY1=VALUE1" "KEY2=VALUE2"
```

**Backend Environment Variables:**
- `GOOGLE_API_KEY` - Google AI API key (required)
- `GEMINI_MODEL` - Model to use (default: gemini-2.5-flash)
- `TEMPERATURE` - AI creativity (0.0-1.0, default: 0.1)
- `MAX_OUTPUT_TOKENS` - Max response length (default: 32768)
- `BATCH_MODE` - Enable batch processing (default: true)
- `REQUESTS_PER_MINUTE` - Rate limit (default: 15)
- `AZURE_CORS_ORIGINS` - Comma-separated allowed origins

**Frontend Environment Variables:**
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_COLLAB_URL` - Collaboration server URL

### CI/CD Integration

Set up automatic deployments from GitHub:

```bash
# Generate deployment token
az containerapp github-action add \
  --name backend-api \
  --resource-group legal-agent-rg \
  --repo-url https://github.com/yourusername/legal-agent \
  --branch main \
  --login-with-github
```

This creates a GitHub Actions workflow that auto-deploys on push to main.

---

## Support & Resources

- **Azure Container Apps Docs**: https://learn.microsoft.com/azure/container-apps/
- **Azure CLI Reference**: https://learn.microsoft.com/cli/azure/containerapp
- **Pricing Calculator**: https://azure.microsoft.com/pricing/calculator/
- **Azure Status**: https://status.azure.com/

---

## Quick Reference Commands

```bash
# View all Container Apps
az containerapp list --resource-group legal-agent-rg --output table

# Get application URL
az containerapp show --name backend-api --resource-group legal-agent-rg --query "properties.configuration.ingress.fqdn"

# View logs (live)
az containerapp logs show --name backend-api --resource-group legal-agent-rg --follow

# View revisions
az containerapp revision list --name backend-api --resource-group legal-agent-rg --output table

# Delete everything
az group delete --name legal-agent-rg --yes
```

---

## Next Steps

1. ✅ Test your deployment thoroughly
2. ✅ Set up custom domains (optional)
3. ✅ Configure monitoring alerts in Azure Portal
4. ✅ Set up automated backups for Azure Files
5. ✅ Review and optimize costs after 1 week
6. ✅ Configure CI/CD for automatic deployments

**Congratulations! Your Legal Agent is now running on Azure!** 🎉
