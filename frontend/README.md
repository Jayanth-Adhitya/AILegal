# AI Legal Assistant - Frontend

Modern Next.js frontend for the AI Legal Assistant system with shadcn/ui components.

## Features

- 📝 **Policy Management** - Upload, view, and delete company policies
- 🔍 **Contract Analysis** - Upload contracts and analyze against policies
- 📊 **Real-time Progress** - Track analysis progress with live updates
- 📈 **Rich Dashboard** - Statistics and compliance metrics
- 📄 **Detailed Reports** - Clause-by-clause analysis with recommendations
- ⬇️ **Multiple Export Formats** - Download Word and HTML reports
- 🎨 **Professional UI** - Clean, modern interface with shadcn/ui
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui (Radix UI primitives)
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Tables**: TanStack React Table

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend FastAPI server running on http://localhost:8000 (or configure via environment variable)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env.local
```

Edit `.env.local`:
```env
# For local development
NEXT_PUBLIC_API_URL=http://localhost:8000

# For production, update to your backend URL
# NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Production Build

```bash
npm run build
npm run start
```

## Project Structure

```
frontend/
├── app/                          # Next.js App Router pages
│   ├── layout.tsx               # Root layout with sidebar
│   ├── page.tsx                 # Dashboard home
│   ├── policies/                # Policy management
│   │   └── page.tsx
│   ├── analyze/                 # Contract analysis
│   │   └── page.tsx
│   ├── results/                 # Analysis results
│   │   ├── page.tsx            # Results list
│   │   └── [id]/page.tsx       # Individual result
│   └── settings/                # Settings page
│       └── page.tsx
├── components/
│   ├── ui/                      # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── table.tsx
│   │   ├── progress.tsx
│   │   ├── accordion.tsx
│   │   ├── dialog.tsx
│   │   ├── badge.tsx
│   │   ├── input.tsx
│   │   ├── alert.tsx
│   │   └── skeleton.tsx
│   ├── layout/                  # Layout components
│   │   └── sidebar.tsx
│   ├── policies/                # Policy-related components
│   │   ├── policy-upload.tsx
│   │   └── policy-list.tsx
│   ├── analysis/                # Analysis components
│   │   ├── contract-upload.tsx
│   │   └── analysis-progress.tsx
│   └── results/                 # Results components
│       ├── statistics-dashboard.tsx
│       └── clause-viewer.tsx
├── lib/
│   ├── api.ts                   # API client & endpoints
│   ├── types.ts                 # TypeScript definitions
│   └── utils.ts                 # Utility functions
└── public/                      # Static assets
```

## Pages Overview

### Dashboard (`/`)
- Welcome page with quick actions
- Feature overview and getting started guide
- Links to all major sections

### Policies (`/policies`)
- Upload multiple policy files (TXT, MD, PDF)
- View all uploaded policies in a searchable table
- Delete policies with confirmation
- Reingest policies to rebuild vector database

### Analyze Contract (`/analyze`)
- Two-step process: Upload → Analyze
- Drag-and-drop contract upload (DOCX only)
- Real-time progress tracking with polling
- Automatic redirect to results when complete

### Results (`/results/[id]`)
- Comprehensive statistics dashboard
- Compliance rate and risk overview
- Clause-by-clause analysis with filters
- Expandable accordions for detailed view
- Download reports (Word, HTML)

### Settings (`/settings`)
- API connection status
- Configuration information
- About section

## API Integration

The frontend communicates with the FastAPI backend via the `lib/api.ts` module:

### Policy API
- `uploadPolicy(file)` - Upload single policy
- `uploadPolicies(files)` - Upload multiple policies
- `getPolicies()` - List all policies
- `deletePolicy(id)` - Delete a policy
- `reingestPolicies()` - Rebuild vector database

### Contract API
- `uploadContract(file)` - Upload contract for analysis
- `analyzeContract(path)` - Start analysis job
- `getJobStatus(jobId)` - Check analysis progress
- `downloadReport(jobId, type)` - Download report
- `cancelJob(jobId)` - Cancel running analysis

### Health Check
- `checkApiHealth()` - Verify backend connectivity

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

**Note**: Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

## Customization

### Colors & Theme

The color palette is defined in `app/globals.css` with CSS variables. Current theme uses:
- **Primary**: Professional Blue (`hsl(221.2 83.2% 53.3%)`)
- **Secondary**: Slate/Gray for subtle elements
- **Success**: Green (`hsl(142.1 76.2% 36.3%)`)
- **Warning**: Yellow (`hsl(45.4 93.4% 47.5%)`)
- **Critical**: Red (`hsl(0 84.2% 60.2%)`)

To change colors, edit the CSS variables in `app/globals.css`.

### Adding Components

This project uses shadcn/ui. To add more components:

```bash
npx shadcn@latest add [component-name]
```

Example:
```bash
npx shadcn@latest add select
npx shadcn@latest add tooltip
```

## Development Tips

### Hot Reload
Next.js supports hot reload. Changes to components will update instantly.

### Type Safety
The project uses TypeScript. All API responses and component props are typed in `lib/types.ts`.

### Code Organization
- **Components**: Create reusable components in `components/`
- **Pages**: Add new routes in `app/`
- **Utilities**: Add helper functions in `lib/utils.ts`
- **API calls**: Extend `lib/api.ts` for new endpoints

## Deployment

### Vercel (Recommended)
```bash
vercel
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables for Production
Update `.env.local` or configure in your hosting platform:
```env
NEXT_PUBLIC_API_URL=https://your-backend-api.com
```

## Troubleshooting

### Cannot connect to backend
- Check that FastAPI is running on the configured URL
- Verify CORS is properly configured in the backend
- Check the Settings page for API status

### Build errors
```bash
rm -rf .next node_modules
npm install
npm run build
```

### Type errors
Ensure all dependencies are installed and types are up to date:
```bash
npm install --save-dev @types/node @types/react @types/react-dom
```

## License

This project is part of the AI Legal Assistant system.
