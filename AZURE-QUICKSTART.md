# Azure Deployment - Quick Start Guide

Get your Legal Agent running on Azure in under 30 minutes!

## Prerequisites Checklist

- [ ] Azure account ([Sign up for free](https://azure.microsoft.com/free/))
- [ ] Azure CLI installed ([Install guide](https://docs.microsoft.com/cli/azure/install-azure-cli))
- [ ] Docker Desktop running
- [ ] Google AI API key ([Get one here](https://aistudio.google.com/app/apikey))

## 5-Step Deployment

### Step 1: Configure Your Environment (5 minutes)

```bash
# Copy the environment template
cp .env.azure .env.azure.local

# Edit the file and add your values:
# - GOOGLE_API_KEY (required)
# - AZURE_SUBSCRIPTION_ID (get via: az account list)
# - AZURE_STORAGE_ACCOUNT (make it unique, e.g., legalagent<yourname>)
```

**Minimum required configuration:**
```bash
GOOGLE_API_KEY=your_google_api_key_here
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=legal-agent-rg
AZURE_LOCATION=eastus
AZURE_CONTAINER_ENV=legal-agent-env
AZURE_STORAGE_ACCOUNT=legalagent<yourname>storage
AZURE_STORAGE_SHARE_NAME=legalagentdata
AZURE_APP_BACKEND=backend-api
AZURE_APP_FRONTEND=frontend
AZURE_APP_COLLAB=collab-server
AZURE_APP_WORD=word-addin
```

### Step 2: Login to Azure (1 minute)

```bash
az login
az account set --subscription <your-subscription-id>
```

### Step 3: Deploy! (15-20 minutes)

#### Windows (PowerShell):
```powershell
.\deploy-azure.ps1
```

#### Linux/Mac (Bash):
```bash
chmod +x deploy-azure.sh
./deploy-azure.sh
```

The script automatically:
- ✅ Creates all Azure resources
- ✅ Builds and deploys 4 container apps
- ✅ Configures HTTPS and WebSocket support
- ✅ Sets up persistent storage

**Grab a coffee ☕ - this takes 15-20 minutes!**

### Step 4: Save Your URLs (1 minute)

After deployment, you'll see:

```
==================================================
  Deployment Complete!
==================================================

Your Legal Agent is now running on Azure:

  Frontend:             https://frontend.xyz123.eastus.azurecontainerapps.io
  Backend API:          https://backend-api.xyz123.eastus.azurecontainerapps.io
  Collaboration Server: https://collab-server.xyz123.eastus.azurecontainerapps.io
  Word Add-in:          https://word-addin.xyz123.eastus.azurecontainerapps.io
```

**Copy these URLs!** You need them for the next step.

### Step 5: Configure CORS (2 minutes)

Update backend to allow your Azure frontend URLs:

```bash
# Replace with YOUR actual URLs from Step 4
az containerapp update \
  --name backend-api \
  --resource-group legal-agent-rg \
  --set-env-vars "AZURE_CORS_ORIGINS=https://frontend.xyz123.eastus.azurecontainerapps.io,https://collab-server.xyz123.eastus.azurecontainerapps.io,https://word-addin.xyz123.eastus.azurecontainerapps.io"
```

## Test Your Deployment

1. **Open your frontend URL** in a browser
2. **Create an account** (register as a new user)
3. **Upload a test contract** (.docx file)
4. **Wait for AI analysis** to complete
5. **Success!** 🎉

## Common First-Time Issues

### "Storage account name not available"
Your storage account name must be globally unique. In `.env.azure.local`, change:
```bash
AZURE_STORAGE_ACCOUNT=legalagent<YOURNAME>storage  # Use your name or random string
```

### "CORS error when loading frontend"
Make sure you completed Step 5 with your actual URLs (not the example URLs).

### "Deployment script not found"
Make sure you're in the project root directory:
```bash
cd "C:\Files\JaziriX\Legal Agent"
```

## What Did This Cost?

With the **free tier** included:
- **First month**: Likely $0 (covered by $200 free credit)
- **After free credit**: $10-30/month for light usage
- **Scale-to-zero enabled**: You only pay when it's running!

See `README.AZURE.md` for detailed cost optimization.

## Next Steps

### Upload Company Policies

Your AI needs company policies to review contracts against:

```bash
# Using Azure CLI
az storage file upload-batch \
  --destination legalagentdata/policies \
  --source ./Data/policies \
  --account-name legalagent<yourname>storage
```

Or use [Azure Storage Explorer](https://azure.microsoft.com/features/storage-explorer/) (GUI tool).

### Set Up Custom Domain (Optional)

Instead of `*.azurecontainerapps.io`, use your own domain:

1. Add CNAME record: `app.yourdomain.com` → `frontend.xyz123.eastus.azurecontainerapps.io`
2. Run:
```bash
az containerapp hostname add \
  --name frontend \
  --resource-group legal-agent-rg \
  --hostname app.yourdomain.com
```

SSL is automatically managed!

### Enable Auto-Deployment from GitHub (Optional)

```bash
az containerapp github-action add \
  --name backend-api \
  --resource-group legal-agent-rg \
  --repo-url https://github.com/yourusername/legal-agent \
  --branch main \
  --login-with-github
```

## Useful Commands

```bash
# View logs
az containerapp logs show --name backend-api --resource-group legal-agent-rg --follow

# Restart app
az containerapp revision restart --name backend-api --resource-group legal-agent-rg

# Update environment variable
az containerapp update --name backend-api --resource-group legal-agent-rg --set-env-vars "KEY=VALUE"

# Scale up
az containerapp update --name backend-api --resource-group legal-agent-rg --max-replicas 20

# Delete everything (careful!)
az group delete --name legal-agent-rg --yes
```

## Get Help

- **Full documentation**: See `README.AZURE.md`
- **Azure support**: https://portal.azure.com → Help + support
- **Check service status**: https://status.azure.com/

## Troubleshooting

**Something went wrong?**

1. Check the logs:
```bash
az containerapp logs show --name backend-api --resource-group legal-agent-rg
```

2. Verify environment variables:
```bash
az containerapp show --name backend-api --resource-group legal-agent-rg --query "properties.template.containers[0].env"
```

3. Test health endpoint:
```bash
curl https://backend-api.xyz123.eastus.azurecontainerapps.io/health
```

Still stuck? Check `README.AZURE.md` for detailed troubleshooting.

---

**That's it! You're now running on Azure!** 🚀
