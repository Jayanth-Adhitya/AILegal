# Deployment Notes

## Important Changes for Production Deployment

### Environment Variables in Docker

**Key Change**: The backend Dockerfile no longer copies `.env` files into the Docker image.

#### Why?
- `.env` files should never be in Docker images (security risk)
- Environment variables should come from the deployment platform (Coolify)
- Keeps secrets out of version control and Docker layers

#### How It Works

**For Local Development:**
- Use `.env` file in project root
- Backend reads from `.env` automatically via pydantic-settings

**For Docker Compose (Local Testing):**
- Copy `.env.production.example` to `.env.production`
- Set your `GOOGLE_API_KEY` and other variables
- docker-compose.yml reads from `.env.production`
- Run: `docker-compose up -d`

**For Coolify (Production):**
- DO NOT commit `.env` or `.env.production` files
- Set all environment variables in Coolify dashboard
- Coolify injects them at runtime
- See `COOLIFY.md` for complete variable list

### Required Files

✅ **Tracked in Git** (safe to commit):
- `.env.example` - Template for local development
- `.env.production.example` - Template for Docker/production

❌ **NOT Tracked** (in .gitignore):
- `.env` - Your local development secrets
- `.env.production` - Your production secrets
- `.env.local` - Local overrides

### Quick Setup Guide

#### Local Development (without Docker)
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
python -m uvicorn src.api:app --reload
```

#### Local Docker Testing
```bash
cp .env.production.example .env.production
# Edit .env.production and add your GOOGLE_API_KEY
docker-compose up -d
```

#### Coolify Production
```bash
# 1. Push code to Git (secrets NOT included)
git add .
git commit -m "Deploy to production"
git push origin main

# 2. In Coolify dashboard:
#    - Add environment variables
#    - Deploy

# No .env files needed!
```

### Environment Variable Priority

The backend (pydantic-settings) reads in this order:
1. **Environment variables** (highest priority) - from Coolify/Docker
2. **`.env` file** (fallback) - local development only
3. **Default values** (in code) - see src/core/config.py

### Security Best Practices

✅ **DO:**
- Set secrets in Coolify environment variables
- Use `.env.example` as a template
- Keep `.env` files in `.gitignore`

❌ **DON'T:**
- Commit `.env` or `.env.production` to Git
- Copy `.env` into Docker images
- Share `.env` files (they contain secrets!)

### Troubleshooting

**Error: `"/.env": not found` during Docker build**
- ✅ **Fixed**: Removed `COPY .env .env` from Dockerfile.backend
- This is expected - environment variables come from Coolify, not files

**Backend can't find GOOGLE_API_KEY**
- Check environment variables are set in Coolify
- For local: ensure `.env` or `.env.production` exists with the key
- Run: `docker-compose config` to verify variables are loaded

**Changes to environment variables not taking effect**
- **Coolify**: Restart the service after updating variables
- **Docker Compose**: Run `docker-compose down && docker-compose up -d`
- Environment variables are read at container startup, not build time

### Files Reference

| File | Purpose | Tracked in Git? |
|------|---------|-----------------|
| `.env.example` | Template for local dev | ✅ Yes |
| `.env.production.example` | Template for Docker | ✅ Yes |
| `.env` | Local dev secrets | ❌ No (.gitignored) |
| `.env.production` | Local Docker secrets | ❌ No (.gitignored) |
| Coolify env vars | Production secrets | ❌ No (in Coolify UI) |

---

**Updated**: 2025-11-10
**Issue Fixed**: Backend Dockerfile no longer requires `.env` file
**Impact**: Production deployments now use environment variables correctly
