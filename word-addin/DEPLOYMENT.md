# Cirilla Word Add-in Deployment Guide

## Production Deployment via Coolify

### Prerequisites
- Coolify instance with Docker support
- Domain configured: `word.contract.cirilla.ai`
- SSL certificate (Coolify handles this automatically)

### Coolify Deployment Steps

The Word add-in is already configured in the main `docker-compose.coolify.yml` file at the root of the repository.

1. **Connect Repository to Coolify**
   - Go to your Coolify dashboard
   - Create a new service → Docker Compose
   - Point to the Git repository
   - Use `docker-compose.coolify.yml` as the compose file

2. **Configuration**
   - The service is named `word-addin` in the compose file
   - **Internal Port**: 3002
   - **Domain**: `word.contract.cirilla.ai` (configure in Coolify)
   - Coolify/Traefik will handle reverse proxy and HTTPS

3. **Environment Variables**
   Environment variables are already set in `docker-compose.coolify.yml`:
   - `NODE_ENV=production`
   - `PORT=3002`

4. **Deploy**
   - Push changes to Git
   - Coolify will automatically build and deploy all services
   - SSL certificate will be provisioned via Let's Encrypt
   - The `word-addin` service depends on `backend`, so it will start after backend is ready

### Post-Deployment

1. **Verify Deployment**
   - Visit `https://word.contract.cirilla.ai/taskpane.html`
   - Should see the Cirilla loading screen with yellow gradient

2. **Test Manifest**
   - Download the manifest: `https://word.contract.cirilla.ai/manifest.xml`
   - Verify all URLs point to `word.contract.cirilla.ai`

3. **Load in Word**
   - Open Microsoft Word
   - Go to **Insert** → **Get Add-ins** → **My Add-ins** → **Upload My Add-in**
   - Upload the `manifest.xml` file
   - The Cirilla add-in should appear in the ribbon

### CORS Configuration

Ensure your backend (`https://word.contract.cirilla.ai`) has CORS configured to allow:
- Origin: `https://word.contract.cirilla.ai`
- Methods: `GET, POST, OPTIONS`
- Headers: `Content-Type, Authorization`

### Troubleshooting

**Add-in doesn't load:**
- Check browser console in Word (File → Account → About Word → Enable Developer Mode)
- Verify HTTPS is working
- Check CORS headers

**Authentication fails:**
- Verify backend URL in `src/services/backend-api.ts`
- Check that cookies/sessions work across domains
- Verify CORS credentials are enabled

**Assets not loading:**
- Check that all static files are in the `dist` folder
- Verify webpack build completed successfully
- Check browser network tab for 404s

### File Structure

```
word-addin/
├── dist/                 # Built files (generated)
├── public/               # Static assets
│   ├── assets/          # Icons and logos
│   ├── taskpane.html    # Main HTML
│   └── commands.html    # Command functions
├── src/                 # Source code
│   ├── components/      # React components
│   ├── services/        # API clients
│   ├── theme.ts         # Cirilla theme
│   └── App.tsx          # Main app
├── manifest.xml         # Office Add-in manifest
├── Dockerfile          # Production build
└── docker-compose.yml  # Coolify deployment
```

### Updates

To update the add-in:
1. Push changes to Git
2. Coolify auto-deploys (if enabled)
3. Or manually trigger rebuild in Coolify
4. Users may need to reload Word to see changes

### Monitoring

- Check Coolify logs for build/runtime errors
- Monitor backend API logs for Word add-in requests
- Track user feedback for UI/UX issues
