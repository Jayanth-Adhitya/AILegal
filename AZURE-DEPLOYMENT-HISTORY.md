# Azure Deployment Guide - Analysis History Feature

This document describes the Azure Container Apps deployment configuration for the persistent analysis history feature.

## Overview

The analysis history feature requires persistent storage for the SQLite database that stores all contract analysis results from both web uploads and Word add-in.

## Persistent Storage Configuration

### Azure Files Volume Mount

The backend container mounts an Azure Files share at `/app/data` which contains:

- **SQLite Database**: `legal_ai.db` - Stores users, sessions, and analysis history
- **ChromaDB**: Vector database for policy embeddings
- **Uploads**: Temporary contract file storage
- **Outputs**: Generated analysis reports
- **Policies**: Company policy documents

### Environment Variables

Add the following environment variable to your Azure Container App backend configuration:

```bash
DATABASE_PATH=/app/data/legal_ai.db
```

This ensures the SQLite database is stored on the persistent volume.

## Azure Container Apps Setup

### 1. Create Azure Files Share

```bash
# Create storage account (if not already created)
az storage account create \
  --name <storage-account-name> \
  --resource-group <resource-group> \
  --location <location> \
  --sku Standard_LRS

# Create file share
az storage share create \
  --name legal-ai-data \
  --account-name <storage-account-name> \
  --quota 10
```

### 2. Mount Storage in Container App

When creating or updating your container app:

```bash
az containerapp create \
  --name legal-ai-backend \
  --resource-group <resource-group> \
  --environment <container-app-env> \
  --image <your-backend-image> \
  --target-port 8000 \
  --ingress external \
  --env-vars \
    DATABASE_PATH=/app/data/legal_ai.db \
    GOOGLE_API_KEY=<your-api-key> \
    ... \
  --azure-file-volume-name legal-data \
  --azure-file-volume-account-name <storage-account-name> \
  --azure-file-volume-account-key <storage-account-key> \
  --azure-file-volume-share-name legal-ai-data \
  --azure-file-volume-mount-path /app/data
```

## Database Initialization

On first deployment, the database will be automatically created with the required schema including:

- **users** table
- **sessions** table
- **analysis_jobs** table (with `source` field for tracking web vs Word add-in)
- **negotiations** table
- **documents** and related tables

The migration script will run automatically to add the `source` field if upgrading from a previous version.

## Health Checks

The backend health check endpoint (`/health`) verifies:
- API is running
- Database is accessible
- Vector store is initialized

## Backup Recommendations

### Automated Backups

Configure Azure Files backup:

```bash
az backup protection enable-for-azurefileshare \
  --resource-group <resource-group> \
  --vault-name <recovery-services-vault> \
  --storage-account <storage-account-name> \
  --azure-file-share legal-ai-data \
  --policy-name <backup-policy>
```

### Manual Backup

The SQLite database can be backed up by copying the file:

```bash
# From the running container
kubectl exec -it <backend-pod> -- cp /app/data/legal_ai.db /tmp/backup.db
kubectl cp <backend-pod>:/tmp/backup.db ./legal_ai_backup_$(date +%Y%m%d).db
```

## Monitoring

Monitor the persistent storage:

1. **Storage Usage**: Check Azure Files metrics for capacity
2. **Database Size**: SQLite database grows with analysis history
3. **Performance**: Monitor I/O latency from Azure Files

Expected growth: ~1-5 MB per analysis (including full results JSON)

## Troubleshooting

### Database Not Persisting

Check:
1. Volume is properly mounted: `kubectl exec <pod> -- ls -la /app/data`
2. Environment variable is set: `kubectl exec <pod> -- env | grep DATABASE_PATH`
3. Permissions on mount point: Should be writable by the app user

### Slow Performance

If database operations are slow:
1. Verify WAL mode is enabled (check logs on startup)
2. Consider upgrading Azure Files tier for better IOPS
3. Monitor concurrent connections (WAL mode supports better concurrency)

## Migration from In-Memory Storage

If upgrading from the previous in-memory implementation:

1. Deploy new version with persistent storage
2. Old in-memory jobs will be lost (expected)
3. New analyses will automatically persist
4. Users will see their history grow from deployment forward

## Security Considerations

1. **Database Encryption**: Azure Files supports encryption at rest
2. **Access Control**: Use Azure RBAC for storage account access
3. **Connection Strings**: Store storage account keys in Azure Key Vault
4. **Network Security**: Use private endpoints for Azure Files if needed

## Cost Optimization

- Use **Standard** tier for Azure Files (LRS replication)
- Set appropriate quota (10-50 GB should suffice for most deployments)
- Consider lifecycle management for old uploads/outputs
- Database grows linearly with analysis count (~1MB per analysis)
