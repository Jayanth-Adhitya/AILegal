# AI Legal Assistant - Frontend Guide

Complete guide for the modern web interface of the AI Legal Assistant.

## Overview

The frontend is a professional, responsive web application built with Next.js 15, TypeScript, and shadcn/ui components. It provides an intuitive interface for managing policies, analyzing contracts, and viewing detailed results.

## Features

### 🎨 Modern UI/UX
- Clean, professional interface with shadcn/ui components
- Responsive design (desktop, tablet, mobile)
- Professional legal/enterprise color palette (Blue/Slate theme)
- Smooth animations and transitions
- Loading states and error handling
- Dark mode compatible (theme infrastructure ready)

### 📝 Policy Management
- **Drag-and-drop upload** - Multi-file upload with visual feedback
- **Multiple formats** - Support for TXT, MD, and PDF files
- **Searchable table** - Find policies by name or type
- **Delete with confirmation** - Prevent accidental deletions
- **Reingest capability** - Rebuild vector database after changes
- **File size display** - Show policy file sizes
- **Upload date tracking** - See when policies were added

### 🔍 Contract Analysis
- **Two-step workflow** - Upload → Analyze
- **DOCX support** - Industry-standard format
- **Real-time progress** - Live updates every 2 seconds
- **Progress indicators** - Visual progress bar with percentage
- **Status messages** - Clear communication of current step
- **Auto-redirect** - Automatic navigation to results when complete
- **Error recovery** - Clear error messages with retry options

### 📊 Analysis Results
- **Statistics Dashboard**:
  - Total clauses analyzed
  - Compliant vs. non-compliant counts
  - Compliance rate percentage
  - Risk level breakdown (Critical/High/Medium/Low)
  - Overall risk assessment

- **Clause Viewer**:
  - Filterable list (All/Non-Compliant/Critical)
  - Expandable accordions for details
  - Color-coded risk levels
  - Status badges (Compliant/Non-Compliant/Needs Review)
  - Original text display
  - Issues identified
  - Recommendations
  - Suggested alternatives
  - Policy references

- **Report Downloads**:
  - Reviewed contract with track changes (DOCX)
  - Detailed analysis report (DOCX)
  - Interactive HTML summary

### ⚙️ Settings & Configuration
- API connection status checker
- Environment configuration display
- About section with version info
- One-click connection testing

## Technical Stack

| Technology | Purpose | Version |
|------------|---------|---------|
| Next.js | React framework | 15.1.4 |
| React | UI library | 19.0.0 |
| TypeScript | Type safety | 5.x |
| Tailwind CSS | Styling | 3.4.1 |
| shadcn/ui | Component library | Latest |
| Radix UI | Headless primitives | Latest |
| Lucide React | Icons | 0.469.0 |
| Axios | HTTP client | 1.7.9 |
| TanStack Table | Data tables | 8.20.5 |

## Architecture

### App Router Structure
```
app/
├── layout.tsx              # Root layout with sidebar
├── page.tsx                # Dashboard (/)
├── policies/
│   └── page.tsx           # Policy management (/policies)
├── analyze/
│   └── page.tsx           # Contract analysis (/analyze)
├── results/
│   ├── page.tsx           # Results list (/results)
│   └── [id]/page.tsx      # Individual result (/results/:id)
└── settings/
    └── page.tsx           # Settings (/settings)
```

### Component Organization
```
components/
├── ui/                     # Reusable shadcn/ui components
│   ├── button.tsx
│   ├── card.tsx
│   ├── table.tsx
│   ├── progress.tsx
│   ├── accordion.tsx
│   ├── dialog.tsx
│   ├── badge.tsx
│   ├── input.tsx
│   ├── alert.tsx
│   └── skeleton.tsx
├── layout/                 # Layout components
│   └── sidebar.tsx
├── policies/               # Policy-specific
│   ├── policy-upload.tsx
│   └── policy-list.tsx
├── analysis/               # Analysis-specific
│   ├── contract-upload.tsx
│   └── analysis-progress.tsx
└── results/                # Results-specific
    ├── statistics-dashboard.tsx
    └── clause-viewer.tsx
```

### Library Organization
```
lib/
├── api.ts                  # API client & endpoints
├── types.ts                # TypeScript type definitions
└── utils.ts                # Helper functions
```

## API Integration

### Endpoints Used

#### Policy API
- `POST /api/policies/upload` - Upload policy file
- `GET /api/policies` - List all policies
- `DELETE /api/policies/{id}` - Delete policy
- `POST /api/policies/reingest` - Rebuild vector database

#### Contract API
- `POST /api/contracts/upload` - Upload contract
- `POST /api/contracts/analyze` - Start analysis
- `GET /api/contracts/status/{job_id}` - Check progress
- `GET /api/contracts/download/{job_id}/{type}` - Download report
- `POST /api/contracts/cancel/{job_id}` - Cancel analysis

#### Health Check
- `GET /health` - Backend health status

### Polling Strategy
The frontend uses a polling mechanism to track analysis progress:
- Polls every 2 seconds
- Automatically stops on completion or failure
- Updates progress bar in real-time
- Displays current status messages
- Auto-redirects to results page

## Color Palette

Professional legal/enterprise theme:

| Color | HSL | Usage |
|-------|-----|-------|
| **Primary (Blue)** | `221.2 83.2% 53.3%` | Buttons, links, active states |
| **Secondary (Slate)** | `210 40% 96.1%` | Backgrounds, subtle elements |
| **Success (Green)** | `142.1 76.2% 36.3%` | Compliant status, success messages |
| **Warning (Yellow)** | `45.4 93.4% 47.5%` | Needs review, warnings |
| **Critical (Red)** | `0 84.2% 60.2%` | Non-compliant, errors |

Customize in `app/globals.css` by modifying CSS variables.

## Key Features Implementation

### Drag-and-Drop Upload
```typescript
// Handles drag events and file validation
const handleDrop = useCallback((e: React.DragEvent) => {
  e.preventDefault();
  const files = Array.from(e.dataTransfer.files).filter(
    file => ['.txt', '.md', '.pdf'].some(ext =>
      file.name.toLowerCase().endsWith(ext)
    )
  );
  // Process files...
}, []);
```

### Real-time Progress Tracking
```typescript
// Polls backend every 2 seconds
useEffect(() => {
  const pollInterval = setInterval(async () => {
    const status = await contractApi.getJobStatus(jobId);
    setStatus(status);
    if (status.status === 'completed') {
      clearInterval(pollInterval);
      router.push(`/results/${jobId}`);
    }
  }, 2000);
  return () => clearInterval(pollInterval);
}, [jobId]);
```

### File Download
```typescript
// Creates blob and triggers download
const handleDownload = async (reportType) => {
  const blob = await contractApi.downloadReport(jobId, reportType);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `report_${reportType}.docx`;
  link.click();
  window.URL.revokeObjectURL(url);
};
```

## User Workflows

### Workflow 1: Initial Setup
1. Start backend server
2. Start frontend server
3. Navigate to Policies page
4. Upload company policies (PDF/TXT/MD)
5. Click "Reingest Policies" to build vector database
6. Ready to analyze contracts!

### Workflow 2: Contract Analysis
1. Navigate to "Analyze Contract" page
2. Drag and drop DOCX contract file
3. Click "Start Analysis"
4. Watch real-time progress
5. Automatically redirected to results
6. Review statistics and clause details
7. Download reports as needed

### Workflow 3: Policy Management
1. Navigate to "Policies" page
2. Search/filter existing policies
3. Upload new policies as needed
4. Delete outdated policies
5. Reingest to update vector database

## Performance Considerations

### Optimizations Applied
- **Code Splitting**: Automatic with Next.js App Router
- **Image Optimization**: Next.js Image component (when used)
- **CSS Optimization**: Tailwind CSS purges unused styles
- **Bundle Size**: Modular imports, tree-shaking enabled
- **Loading States**: Skeleton screens prevent layout shift
- **Error Boundaries**: Graceful error handling

### Recommended Improvements
- Add React Query for caching API responses
- Implement virtual scrolling for large clause lists
- Add service worker for offline capability
- Enable Progressive Web App (PWA) features
- Add analytics and error tracking (Sentry)

## Security Features

### Client-Side Security
- Environment variables for API URLs
- No sensitive data in client code
- HTTPS enforced in production
- CORS handled by backend
- File type validation on upload
- Size limits on uploads

### Best Practices
- TypeScript for type safety
- Input sanitization
- Error messages don't expose internals
- Secure token handling (if authentication added)

## Testing Strategy

### Manual Testing Checklist
- [ ] Dashboard loads correctly
- [ ] Sidebar navigation works
- [ ] Policy upload (single file)
- [ ] Policy upload (multiple files)
- [ ] Policy list displays correctly
- [ ] Policy search/filter works
- [ ] Policy deletion with confirmation
- [ ] Reingest policies succeeds
- [ ] Contract upload validates DOCX
- [ ] Analysis starts successfully
- [ ] Progress updates in real-time
- [ ] Redirect to results works
- [ ] Statistics display correctly
- [ ] Clause filters work
- [ ] Clause expansion works
- [ ] Report downloads succeed
- [ ] Settings page shows API status
- [ ] Responsive on mobile
- [ ] Error handling works

### Automated Testing (Future)
```bash
# Install testing libraries
npm install --save-dev @testing-library/react @testing-library/jest-dom jest
npm install --save-dev @playwright/test  # For E2E tests
```

## Deployment Options

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

**Quick options:**
- **Vercel** (Easiest): `vercel`
- **Docker**: `docker build -t legal-frontend .`
- **Traditional**: `npm run build && npm start`

## Environment Configuration

### Development (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Production
```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

**Important**: Variables must start with `NEXT_PUBLIC_` to be accessible in the browser.

## Customization Guide

### Change Colors
Edit `app/globals.css`:
```css
:root {
  --primary: 221.2 83.2% 53.3%;  /* Your color here */
}
```

### Add New Page
1. Create `app/newpage/page.tsx`
2. Add route to sidebar in `components/layout/sidebar.tsx`

### Add shadcn/ui Component
```bash
npx shadcn@latest add [component-name]
```

### Modify API Client
Edit `lib/api.ts` to add new endpoints or modify existing ones.

## Troubleshooting

### Common Issues

**CORS Errors**
- Check backend CORS configuration
- Verify API URL in `.env.local`
- Check browser console for details

**Build Fails**
```bash
rm -rf .next node_modules
npm install
npm run build
```

**Slow Performance**
- Check network tab for slow API calls
- Enable caching in API client
- Consider pagination for large lists

**Styles Not Working**
- Ensure Tailwind config is correct
- Check `globals.css` imports
- Restart dev server

## Future Enhancements

### Planned Features
- [ ] User authentication & authorization
- [ ] Analysis history with search
- [ ] Batch contract processing
- [ ] Export to multiple formats (PDF, Excel)
- [ ] Comparison between contracts
- [ ] Custom policy templates
- [ ] Role-based access control
- [ ] Audit trail logging
- [ ] Advanced filtering & sorting
- [ ] Dark mode toggle

### Architecture Improvements
- [ ] Add React Query for state management
- [ ] Implement WebSocket for real-time updates
- [ ] Add unit and E2E tests
- [ ] Set up CI/CD pipeline
- [ ] Add Storybook for component documentation
- [ ] Implement analytics tracking
- [ ] Add error monitoring (Sentry)

## Support & Resources

### Documentation
- [README.md](./README.md) - Main documentation
- [QUICKSTART.md](./QUICKSTART.md) - 5-minute setup guide
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment instructions

### External Resources
- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com)
- [Tailwind CSS](https://tailwindcss.com)
- [TypeScript](https://www.typescriptlang.org)

### Getting Help
1. Check browser console for errors
2. Review API logs in backend
3. Verify environment variables
4. Check Settings page for API status
5. Review this guide and other documentation

## License

Part of the AI Legal Assistant project.

---

**Built with ❤️ using Next.js, TypeScript, and shadcn/ui**
