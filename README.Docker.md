# Docker Deployment Guide for AI Legal Assistant

This guide covers deploying the AI Legal Assistant using Docker and Docker Compose, including deployment to Coolify.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Google API Key (Gemini API access)

## Quick Start

### 1. Environment Setup

Copy the example environment file and configure it:

```bash
cp .env.production.example .env.production
```

Edit `.env.production` and set your configuration:
- **REQUIRED**: Set `GOOGLE_API_KEY` to your actual Google API key
- Adjust `NEXT_PUBLIC_API_URL` for your production domain
- Configure other settings as needed

### 2. Build and Run with Docker Compose

```bash
# Build the images
docker-compose build

# Start the services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the services
docker-compose down
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000

## Coolify Deployment

### Method 1: Using Docker Compose (Recommended)

1. **Push your code to a Git repository** (GitHub, GitLab, etc.)

2. **In Coolify Dashboard**:
   - Create a new project
   - Select "Docker Compose" as the deployment type
   - Connect your Git repository
   - Point to the `docker-compose.yml` file

3. **Configure Environment Variables in Coolify**:
   - Add all variables from `.env.production.example`
   - Set `NEXT_PUBLIC_API_URL` to your actual domain (e.g., `https://api.yourdomain.com`)
   - Coolify will automatically handle SSL certificates

4. **Deploy**:
   - Click "Deploy" in Coolify
   - Coolify will build and start your containers

### Method 2: Separate Services

Deploy backend and frontend as separate services:

#### Backend Service
- **Source**: Your Git repository
- **Dockerfile**: `Dockerfile.backend`
- **Port**: 8000
- **Environment Variables**: Set all backend variables
- **Volumes**: Map `/app/data` for persistent storage

#### Frontend Service
- **Source**: Your Git repository
- **Dockerfile**: `Dockerfile.frontend`
- **Port**: 3000
- **Build Args**: `NEXT_PUBLIC_API_URL=https://your-backend-url.com`
- **Environment Variables**: `NEXT_PUBLIC_API_URL`

## Architecture

```
┌─────────────┐      ┌─────────────┐      ┌──────────────┐
│   Client    │─────>│  Frontend   │─────>│   Backend    │
│  (Browser)  │      │  (Next.js)  │      │  (FastAPI)   │
└─────────────┘      └─────────────┘      └──────────────┘
                          :3000                 :8000
                                                   │
                                                   ▼
                                            ┌──────────────┐
                                            │   Volumes    │
                                            │  - uploads   │
                                            │  - outputs   │
                                            │  - policies  │
                                            │  - chroma_db │
                                            └──────────────┘
```

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API Key | `AIza...` |
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://backend:8000` |

### Optional Backend Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model to use |
| `TEMPERATURE` | `0.1` | Model temperature |
| `MAX_OUTPUT_TOKENS` | `8192` | Max output tokens |
| `BATCH_MODE` | `true` | Enable batch processing |
| `MAX_BATCH_SIZE` | `50` | Max clauses per batch |
| `REQUESTS_PER_MINUTE` | `15` | API rate limit (RPM) |

## Volume Management

The backend service uses a named volume `backend_data` that persists:
- `/app/data/uploads` - Uploaded contracts
- `/app/data/outputs` - Generated reports
- `/app/data/policies` - Company policies
- `/app/data/chroma_db` - Vector database

### Backup Data

```bash
# Create backup
docker run --rm -v legal-assistant_backend_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/legal-assistant-backup.tar.gz -C /data .

# Restore backup
docker run --rm -v legal-assistant_backend_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/legal-assistant-backup.tar.gz -C /data
```

## Troubleshooting

### Check Service Health

```bash
# Check container status
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# Check frontend health
curl http://localhost:3000

# View logs
docker-compose logs backend
docker-compose logs frontend
```

### Common Issues

**Issue**: Frontend can't connect to backend
- **Solution**: Check `NEXT_PUBLIC_API_URL` is correctly set. For Docker internal networking, use `http://backend:8000`. For external access from browser, use your public domain.

**Issue**: Backend crashes on startup
- **Solution**: Ensure `GOOGLE_API_KEY` is set correctly. Check logs with `docker-compose logs backend`

**Issue**: "Module not found" errors in frontend
- **Solution**: Rebuild the frontend image: `docker-compose build --no-cache frontend`

**Issue**: Data persists after container restart?
- **Solution**: This is expected. Data is stored in Docker volumes. To clear data, remove the volume: `docker-compose down -v`

## Production Considerations

### Security
- Use secrets management for `GOOGLE_API_KEY` (Coolify supports this)
- Enable HTTPS/SSL (Coolify handles this automatically)
- Set `API_RELOAD=false` in production (already set in Dockerfile)

### Performance
- Adjust `MAX_BATCH_SIZE` based on your API quota
- Monitor `REQUESTS_PER_MINUTE` and `REQUESTS_PER_DAY`
- Consider scaling horizontally with multiple backend instances

### Monitoring
- Enable health checks (already configured in docker-compose.yml)
- Monitor logs: `docker-compose logs -f --tail=100`
- Set up alerts in Coolify for service failures

## Building for Production

### Multi-platform Build

For ARM-based servers (like some VPS):

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t legal-assistant-backend:latest \
  -f Dockerfile.backend .

docker buildx build --platform linux/amd64,linux/arm64 \
  -t legal-assistant-frontend:latest \
  -f Dockerfile.frontend .
```

### Optimize Image Size

The Dockerfiles are already optimized with:
- Multi-stage builds (frontend)
- Minimal base images (alpine for Node, slim for Python)
- .dockerignore to exclude unnecessary files
- No cache pip installs

## Support

For issues specific to:
- **Docker setup**: Check the Troubleshooting section
- **Coolify deployment**: Refer to [Coolify documentation](https://coolify.io/docs)
- **Application bugs**: Check the main project README

## Next Steps

After deployment:
1. Upload your company policies via the Policies page
2. Click "Reingest Policies" to update the vector database
3. Start analyzing contracts!
