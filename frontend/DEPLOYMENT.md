# Deployment Guide

Complete guide for deploying the AI Legal Assistant frontend.

## Prerequisites

- Node.js 18+ installed
- Backend FastAPI server deployed and accessible
- Domain name (optional, for production)

## Local Development

1. **Install Dependencies**
```bash
cd frontend
npm install
```

2. **Configure Environment**
```bash
cp .env.example .env.local
```

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. **Run Development Server**
```bash
npm run dev
```

Visit http://localhost:3000

## Production Deployment

### Option 1: Vercel (Recommended)

Vercel is the easiest deployment option for Next.js applications.

1. **Install Vercel CLI**
```bash
npm install -g vercel
```

2. **Deploy**
```bash
cd frontend
vercel
```

3. **Configure Environment Variables**

In Vercel Dashboard:
- Go to Project Settings → Environment Variables
- Add:
  - `NEXT_PUBLIC_API_URL` = `https://your-backend-url.com`

4. **Redeploy**
```bash
vercel --prod
```

### Option 2: Docker

1. **Create Dockerfile**

Already included in the project. Build the image:

```bash
cd frontend
docker build -t legal-assistant-frontend .
```

2. **Run Container**
```bash
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=https://your-backend-url.com \
  legal-assistant-frontend
```

3. **Docker Compose**

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  backend:
    build: ./
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
```

Run:
```bash
docker-compose up -d
```

### Option 3: Traditional Server (Ubuntu/Debian)

1. **Install Node.js**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

2. **Clone & Build**
```bash
cd /var/www
git clone <your-repo>
cd frontend
npm install
npm run build
```

3. **Install PM2**
```bash
sudo npm install -g pm2
```

4. **Start Application**
```bash
pm2 start npm --name "legal-frontend" -- start
pm2 save
pm2 startup
```

5. **Configure Nginx**

Create `/etc/nginx/sites-available/legal-assistant`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/legal-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

6. **SSL with Let's Encrypt**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Option 4: AWS Amplify

1. **Connect Repository**
- Go to AWS Amplify Console
- Choose "Host web app"
- Connect your Git repository

2. **Configure Build Settings**

Build settings (auto-detected for Next.js):
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm install
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: .next
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```

3. **Environment Variables**
- Add `NEXT_PUBLIC_API_URL` in Amplify Console

### Option 5: Netlify

1. **Install Netlify CLI**
```bash
npm install -g netlify-cli
```

2. **Deploy**
```bash
cd frontend
netlify deploy --prod
```

3. **Configure**
- Add `NEXT_PUBLIC_API_URL` in Netlify Dashboard
- Set build command: `npm run build`
- Set publish directory: `.next`

## Backend CORS Configuration

**IMPORTANT**: Your FastAPI backend must allow CORS requests from your frontend domain.

Update your backend `src/api.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",  # Local development
    "https://your-frontend-domain.com",  # Production
    "https://your-vercel-app.vercel.app",  # If using Vercel
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Or allow all origins (not recommended for production):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Environment Variables Checklist

### Development (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Production
```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

**Note**: All environment variables starting with `NEXT_PUBLIC_` are exposed to the browser.

## Performance Optimization

### Enable Caching
In `next.config.ts`:
```typescript
const nextConfig: NextConfig = {
  // ... existing config
  poweredByHeader: false,
  compress: true,
  images: {
    domains: ['your-domain.com'],
  },
};
```

### Enable Static Generation (if applicable)
For pages that don't change often:
```typescript
export const dynamic = 'force-static';
```

## Monitoring

### Vercel Analytics
Already included with Vercel deployment.

### Custom Monitoring
Add error tracking:
```bash
npm install @sentry/nextjs
```

Initialize in `app/layout.tsx`.

## Health Checks

### Frontend Health
```bash
curl http://localhost:3000
```

### API Connection
Check Settings page in the UI or:
```bash
curl ${NEXT_PUBLIC_API_URL}/health
```

## Troubleshooting

### Build Fails
```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

### CORS Errors
- Check backend CORS configuration
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check browser console for specific error

### Environment Variables Not Working
- Ensure variables start with `NEXT_PUBLIC_`
- Restart dev server after changing .env.local
- In production, redeploy after updating env vars

### 404 on Direct URL Access
Configure your hosting platform to handle Next.js routes:

**Nginx**:
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

**Vercel**: Automatically handled

## Security Checklist

- [ ] Use HTTPS in production
- [ ] Set proper CORS origins in backend
- [ ] Don't expose sensitive data in `NEXT_PUBLIC_` variables
- [ ] Keep dependencies updated: `npm audit`
- [ ] Set security headers in `next.config.ts`
- [ ] Enable rate limiting on backend
- [ ] Use environment-specific API URLs

## Scaling

### Horizontal Scaling
Deploy multiple instances behind a load balancer.

### CDN
Use Vercel Edge Network, Cloudflare, or AWS CloudFront for static assets.

### Database
If adding persistent storage, consider:
- PostgreSQL for relational data
- Redis for caching
- S3 for file storage

## Backup Strategy

### Code
- Use Git version control
- Regular commits to remote repository

### Environment Variables
- Document all variables
- Store securely (not in code)
- Use secret management tools

## Updates & Maintenance

### Update Dependencies
```bash
npm update
npm audit fix
```

### Update Next.js
```bash
npm install next@latest react@latest react-dom@latest
```

### Check for Breaking Changes
Review Next.js release notes before major updates.

## Cost Estimation

### Vercel
- **Hobby**: Free (100GB bandwidth, unlimited requests)
- **Pro**: $20/month (1TB bandwidth, unlimited requests)

### AWS
- **EC2 t3.small**: ~$15/month
- **Amplify**: ~$0.01 per build minute + $0.15/GB served

### DigitalOcean
- **Droplet (1GB RAM)**: $6/month

## Support

For issues or questions:
1. Check frontend logs
2. Verify backend connectivity
3. Review environment variables
4. Check CORS configuration
5. Test API endpoints directly

## Next Steps

After deployment:
1. Test all features (upload, analyze, download)
2. Check Settings page for API status
3. Monitor logs for errors
4. Set up SSL certificate
5. Configure domain DNS
6. Add monitoring/analytics
