# Quick Start Guide - Frontend

Get the AI Legal Assistant frontend up and running in 5 minutes.

## Prerequisites

- Node.js 18+ installed
- Backend API running (see main project README)

## Step 1: Install Dependencies

```bash
cd frontend
npm install
```

This will install all required packages including Next.js, React, Tailwind CSS, and shadcn/ui components.

## Step 2: Configure Environment

Copy the example environment file:

```bash
cp .env.example .env.local
```

The default configuration points to `http://localhost:8000`. If your backend runs on a different URL, edit `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Step 3: Start Development Server

```bash
npm run dev
```

The frontend will start on http://localhost:3000

## Step 4: Verify Connection

1. Open http://localhost:3000 in your browser
2. Click on "Settings" in the sidebar
3. Check the API Status - it should show "Online" with a green indicator

If the status shows "Offline":
- Ensure the backend FastAPI server is running
- Check that the URL in `.env.local` is correct
- Check the browser console for error messages

## Step 5: Upload Policies

1. Click "Policies" in the sidebar
2. Drag and drop policy files (TXT, MD, or PDF)
3. Click "Upload" button
4. After upload completes, click "Reingest Policies" to build the vector database

## Step 6: Analyze a Contract

1. Click "Analyze Contract" in the sidebar
2. Upload a DOCX contract file
3. Click "Start Analysis"
4. Watch the real-time progress
5. You'll be automatically redirected to results when complete

## Step 7: View Results

The results page shows:
- Compliance statistics and metrics
- Risk overview dashboard
- Clause-by-clause analysis
- Download options for reports (Word, HTML)

## Common Commands

### Development
```bash
npm run dev          # Start development server
npm run build        # Create production build
npm run start        # Start production server
npm run lint         # Run ESLint
```

### Testing
```bash
# Manual testing checklist:
1. Upload policies
2. View policy list
3. Delete a policy
4. Reingest policies
5. Upload contract
6. Start analysis
7. View progress
8. Check results
9. Download reports
```

## Project Structure

```
frontend/
├── app/                 # Pages
│   ├── page.tsx        # Dashboard
│   ├── policies/       # Policy management
│   ├── analyze/        # Contract analysis
│   ├── results/        # Analysis results
│   └── settings/       # Settings
├── components/
│   ├── ui/             # shadcn/ui components
│   ├── layout/         # Sidebar, navigation
│   ├── policies/       # Policy components
│   ├── analysis/       # Analysis components
│   └── results/        # Results components
└── lib/
    ├── api.ts          # API client
    ├── types.ts        # TypeScript types
    └── utils.ts        # Utilities
```

## Features Overview

### Dashboard
- Quick access to all features
- Feature explanations
- Getting started guide

### Policy Management
- Drag-and-drop upload
- Search and filter
- Delete with confirmation
- Reingest vector database

### Contract Analysis
- Upload DOCX contracts
- Real-time progress (2-second polling)
- Auto-redirect to results
- Error handling

### Results
- Statistics dashboard
- Compliance rate visualization
- Risk level breakdown
- Filterable clause list
- Expandable clause details
- Download reports

### Settings
- API connection status
- Configuration info
- About section

## Troubleshooting

### Port 3000 already in use
```bash
# Use different port
PORT=3001 npm run dev
```

### Build errors
```bash
# Clear cache and reinstall
rm -rf .next node_modules
npm install
npm run build
```

### API connection fails
- Check backend is running on port 8000
- Verify `.env.local` has correct URL
- Check Settings page for connection status
- Look at browser console for CORS errors

### Styles not loading
```bash
# Rebuild Tailwind CSS
npm run dev
```

## Next Steps

- Read [README.md](./README.md) for detailed documentation
- Check [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment
- Customize colors in `app/globals.css`
- Add more shadcn/ui components as needed

## Support

If you encounter issues:
1. Check the browser console for errors
2. Verify backend is running and accessible
3. Review `.env.local` configuration
4. Ensure all dependencies are installed
5. Try clearing cache and rebuilding

## What's Running?

- **Frontend**: Next.js on http://localhost:3000
- **Backend**: FastAPI on http://localhost:8000
- **Database**: ChromaDB (embedded in backend)

All three components must be running for the full system to work.
