# AI Legal Assistant - Word Add-in

Microsoft Word Add-in for AI-powered contract analysis, compliance review, redlining, and clause suggestions.

## Features

- **Document Analysis**: One-click analysis of entire contract documents
- **Compliance Review**: Check clauses against company policies and legal requirements
- **Track Changes**: Apply AI suggestions as tracked revisions in Word
- **Inline Comments**: Add compliance issue comments directly in the document
- **Navigate to Issues**: Click on any issue to jump to that clause in Word
- **Batch Operations**: Apply multiple suggestions at once

## Prerequisites

- Node.js 16.x or higher
- Microsoft Word 2019 or later (supports WordApi 1.6)
- Running backend server (FastAPI on port 8000)

## Quick Start

### 1. Install Dependencies

```bash
cd word-addin
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

This starts a webpack dev server at `https://localhost:3001` with HTTPS enabled.

### 3. Sideload the Add-in in Word

#### Windows

1. Open Word
2. Go to **Insert** > **Add-ins** > **My Add-ins**
3. Click **Upload My Add-in**
4. Browse to `word-addin/manifest.xml`
5. Click **Upload**

#### Mac

1. Open Word
2. Go to **Insert** > **Add-ins** > **My Add-ins**
3. Click the **...** menu
4. Select **Upload My Add-in**
5. Choose `word-addin/manifest.xml`

### 4. Start Backend Server

Make sure your FastAPI backend is running:

```bash
cd .. # Go to project root
python -m uvicorn src.api:app --reload --port 8000
```

### 5. Use the Add-in

1. Open a contract document in Word
2. Click **"AI Legal Assistant"** in the Home tab (or **Insert** > **Add-ins**)
3. Sign in with your account
4. Click **"Analyze Document"**
5. Review issues, apply suggestions, add comments

## Project Structure

```
word-addin/
├── manifest.xml              # Office Add-in manifest
├── package.json              # Node dependencies
├── tsconfig.json             # TypeScript configuration
├── webpack.config.js         # Build configuration
├── public/
│   ├── taskpane.html         # HTML entry point
│   └── assets/               # Icons and images
└── src/
    ├── index.tsx             # React entry point
    ├── App.tsx               # Main application component
    ├── components/
    │   ├── AuthPanel.tsx     # Authentication UI
    │   ├── AnalysisPanel.tsx # Main analysis interface
    │   ├── ClauseCard.tsx    # Individual clause display
    │   ├── SummaryStats.tsx  # Analysis summary
    │   ├── Header.tsx        # App header
    │   └── ErrorBanner.tsx   # Error notifications
    ├── services/
    │   ├── word-api.ts       # Office JS API wrapper
    │   └── backend-api.ts    # Backend API client
    └── types/
        └── analysis.ts       # TypeScript interfaces
```

## Development

### Building for Production

```bash
npm run build
```

Output will be in the `dist/` folder.

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## Deployment

### Option 1: Centralized Deployment (Enterprise)

1. Build the production bundle
2. Host static files on your web server
3. Update manifest.xml with production URLs
4. Deploy via Microsoft 365 Admin Center

### Option 2: Sideloading (Development/Testing)

Use the sideloading process described above for local testing.

### Option 3: AppSource (Public Distribution)

Submit to Microsoft AppSource for public distribution (requires certification).

## Configuration

### Environment Variables

Update the `API_BASE_URL` in `src/services/backend-api.ts`:

```typescript
const API_BASE_URL = 'https://your-production-url.com';
```

### Manifest URLs

Update URLs in `manifest.xml` for production deployment:

- `SourceLocation`: Your hosted taskpane.html
- `AppDomains`: Your production domains
- `Icon URLs`: Your icon hosting locations

## Troubleshooting

### Add-in Not Loading

- Ensure HTTPS is enabled for the dev server
- Check that certificates are trusted
- Verify Word meets minimum version requirements

### Authentication Issues

- Backend must have CORS configured for add-in origin
- Cookies may not work in iframe; use Authorization header

### Track Changes Not Working

- Requires WordApi 1.6 or higher
- Ensure Word version supports `changeTrackingMode`

### API Errors

- Check backend is running on correct port
- Verify CORS origins include add-in domain
- Check network tab for detailed error messages

## Requirements

### Office Requirements

- WordApi 1.6 minimum requirement set
- Supported on:
  - Word 2019+
  - Word for Mac 16.x+
  - Word Online
  - Microsoft 365

### Backend API Endpoints

The add-in uses these backend endpoints:

- `POST /api/auth/login` - User authentication
- `GET /api/auth/me` - Session validation
- `POST /api/word-addin/analyze-text` - Document analysis
- `POST /api/analyze/clause` - Single clause analysis

## License

MIT License - See main project LICENSE file.
