# Quick Start Guide: Next.js Prescription Validation UI

**Feature**: 001-prescription-ui
**Target Audience**: Developers setting up local development environment
**Prerequisites**: Node.js 18+, Backend API running on `http://localhost:8000`

---

## 1. Initial Setup (5 minutes)

### Clone and Install

```bash
# Navigate to project root (assumes frontend is subdirectory)
cd medical-insurance-frontend

# Install dependencies with npm/yarn/pnpm
npm install
# or
pnpm install
# or
yarn install
```

### Environment Configuration

Create `.env.local` file in project root:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Enable React Query DevTools in production
NEXT_PUBLIC_ENABLE_DEVTOOLS=true
```

**Important**: Never commit `.env.local` to version control (add to `.gitignore`)

---

## 2. Development Server (1 minute)

```bash
# Start Next.js development server
npm run dev

# Server starts at http://localhost:3000
# Hot reload enabled (changes reflect automatically)
```

### Verify Setup

1. Open browser: `http://localhost:3000/en`
2. You should see upload page with drag-and-drop zone
3. Language toggle in header (English/العربية)
4. No console errors in browser DevTools

---

## 3. Backend Connection Test (2 minutes)

### Health Check

```bash
# Verify backend is running
curl http://localhost:8000/health

# Expected response:
# {"status": "ok", "api_version": "1.0.0"}
```

### Upload Test Flow

1. Go to `http://localhost:3000/en`
2. Drag a prescription image/PDF (<10MB)
3. File uploads → redirects to status page
4. Status updates: EXTRACTING → VALIDATING → COMPLETED
5. Results page shows:
   - Patient information
   - Medication cards with ✓/❌ badges
   - Bilingual rejection reasons
   - Transaction ID

**Troubleshooting**:
- **CORS Error**: Add `http://localhost:3000` to backend CORS allowed origins
- **Network Error**: Check backend is running on port 8000
- **No job_id**: Check browser console for API errors

---

## 4. Run Tests (5 minutes)

### Unit & Component Tests (Vitest)

```bash
# Run all tests
npm run test

# Run tests in watch mode (re-runs on file changes)
npm run test:watch

# Run tests with UI (interactive test explorer)
npm run test:ui

# Generate coverage report
npm run test:coverage
```

**Expected Output**:
```
✓ components/ui/StatusBadge.test.tsx (3)
✓ hooks/useFileUpload.test.tsx (5)
✓ lib/utils/validate.test.tsx (4)

Test Files  12 passed (12)
     Tests  58 passed (58)
  Duration  1.23s
```

### E2E Tests (Playwright)

```bash
# Install Playwright browsers (first time only)
npx playwright install

# Run E2E tests (headless)
npm run test:e2e

# Run E2E tests with UI (visual test runner)
npm run test:e2e:ui

# Run specific test file
npx playwright test tests/e2e/prescription.spec.ts
```

**Expected Output**:
```
Running 8 tests using 4 workers
✓ [chromium] › prescription.spec.ts:3 - upload and view results (5.2s)
✓ [firefox] › prescription.spec.ts:3 - upload and view results (6.1s)
✓ [chromium] › accessibility.spec.ts:7 - WCAG 2.1 AA compliance (3.4s)
```

---

## 5. Language Testing (2 minutes)

### English → Arabic Toggle

1. Go to `http://localhost:3000/en`
2. Click "العربية" in header
3. URL changes to `/ar`
4. Layout switches to RTL (right-to-left)
5. All UI text displays in Arabic

### Verify RTL Layout

- Header aligns to right
- Navigation menu opens from right
- Text alignment is right-to-left
- Upload button on right side of drop zone

**Visual Check**:
```
English (LTR):  [Logo]  Upload Prescription  [Language: AR]
Arabic (RTL):   [AR :ةغللا]  ءاودلا ةفصو ليمحت  [Logo]
```

---

## 6. File Upload Validation Test

### Valid File Types

Upload these files to verify validation:
- ✅ `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.tiff`
- ✅ `.pdf`

### Invalid File Tests

Try these to see error messages:
- ❌ `.docx`, `.txt`, `.zip` → "Invalid file type"
- ❌ File >10MB → "File must be less than 10MB"
- ❌ Multiple files → "Only one file allowed"

**Error Message Check**:
- English: "Invalid file type. Please upload JPEG, PNG, or PDF."
- Arabic: "نوع الملف غير صالح. يرجى تحميل JPEG أو PNG أو PDF."

---

## 7. Job Status Polling Test

### Observe State Transitions

1. Upload prescription
2. Watch status page poll every 2 seconds
3. Status badge updates: EXTRACTING → VALIDATING → COMPLETED
4. Auto-redirect to results when COMPLETED
5. Stop polling when COMPLETED or FAILED

**DevTools Check**:
```
Network tab should show:
GET /result/PAT-xxxxx (every 2s during processing)
GET /result/PAT-xxxxx (stops after COMPLETED)
```

---

## 8. Accessibility Testing (3 minutes)

### Keyboard Navigation

1. Go to upload page
2. Press `Tab` key repeatedly
3. Verify focus order: Header → Language Toggle → Upload Zone → Footer
4. Press `Enter` on Upload Zone to open file picker
5. Navigate results page with `Tab` (Patient Info → Medication Cards → Footer)

### Screen Reader Test (Optional)

**Windows (NVDA)**:
```bash
# Install NVDA: https://www.nvaccess.org/download/
# Press Ctrl+Alt+N to start
# Navigate page with Tab/Arrow keys
# NVDA should announce: "Upload prescription, button" "Language toggle, English"
```

**macOS (VoiceOver)**:
```bash
# Press Cmd+F5 to enable VoiceOver
# Press Ctrl+Option+Arrow to navigate
# VoiceOver should announce page structure and labels
```

### Contrast Check

Run automated accessibility audit:
```bash
npm run test:e2e -- --grep "accessibility"
```

**Expected**: 0 WCAG 2.1 AA violations

---

## 9. Common Development Tasks

### Add New Translation

Edit `messages/en.json` and `messages/ar.json`:

```json
// messages/en.json
{
  "upload": {
    "new_key": "New feature text"
  }
}

// messages/ar.json
{
  "upload": {
    "new_key": "نص الميزة الجديدة"
  }
}
```

Use in component:
```typescript
import { useTranslations } from 'next-intl';

export function MyComponent() {
  const t = useTranslations('upload');
  return <p>{t('new_key')}</p>;
}
```

### Add New API Endpoint

1. Define Zod schema in `types/api.ts`
2. Create React Query hook in `lib/api/queries.ts`
3. Use hook in component

Example:
```typescript
// types/api.ts
export const NewResponseSchema = z.object({
  field: z.string()
});

// lib/api/queries.ts
export function useNewEndpoint() {
  return useQuery({
    queryKey: ['newEndpoint'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/new`);
      return NewResponseSchema.parse(await res.json());
    }
  });
}

// component
const { data } = useNewEndpoint();
```

### Debug React Query

Enable DevTools in browser:
1. Open app in browser
2. React Query DevTools panel appears in bottom-right
3. Click to expand and see:
   - Active queries
   - Query cache
   - Fetch status
   - Refetch interval

---

## 10. Production Build Test

### Build for Production

```bash
# Create optimized production build
npm run build

# Expected output:
# ✓ Compiled successfully
# ✓ Linting and checking validity of types
# ✓ Collecting page data
# ✓ Generating static pages (8/8)
# ✓ Finalizing page optimization
```

### Test Production Server

```bash
# Start production server
npm run start

# Server runs at http://localhost:3000
# No hot reload (production mode)
```

### Verify Production Optimizations

1. Check bundle size:
   ```
   ┌ ○ /en                    2.1 kB          180 kB
   ├ ○ /ar                    2.1 kB          180 kB
   ├ ● /prescriptions/[jobId] 3.5 kB          185 kB
   ```

2. Run Lighthouse audit:
   - Performance: >90
   - Accessibility: 100
   - Best Practices: >90
   - SEO: >90

---

## 11. Troubleshooting

### Issue: "Module not found: Can't resolve 'next-intl'"

**Solution**:
```bash
# Delete node_modules and lockfile
rm -rf node_modules package-lock.json
# Reinstall dependencies
npm install
```

### Issue: "CORS policy blocked request to http://localhost:8000"

**Solution**: Update backend CORS configuration

```python
# Backend: src/api/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### Issue: "Hydration error: Text content does not match"

**Solution**: Check for server/client mismatches
- Ensure dates are formatted consistently
- Use `suppressHydrationWarning` for dynamic content
- Verify no browser extensions modifying DOM

### Issue: "PDF viewer not loading"

**Solution**: Check Web Worker CDN URL
```typescript
// components/features/prescription/PDFViewer.tsx
<Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
```

### Issue: Vitest tests fail with "ReferenceError: TextEncoder is not defined"

**Solution**: Add to `vitest.config.ts`
```typescript
export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts']
  }
});
```

---

## 12. Next Steps

After completing quickstart:

1. **Review Architecture**: Read `research.md` for design decisions
2. **Explore Data Model**: See `data-model.md` for TypeScript types
3. **Check Constitution**: Verify compliance with `.specify/memory/constitution.md`
4. **Run Full Test Suite**: `npm run test && npm run test:e2e`
5. **Deploy Preview**: Push to Vercel/Netlify for preview URL

---

## Development URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend Dev | http://localhost:3000 | Next.js dev server |
| Backend API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Vitest UI | http://localhost:51204 | Test explorer |
| React Query DevTools | (overlay in app) | Query debugging |

---

## Useful Commands

```bash
# Development
npm run dev           # Start dev server
npm run lint          # Run ESLint
npm run format        # Run Prettier

# Testing
npm run test          # Run Vitest tests
npm run test:e2e      # Run Playwright E2E
npm run test:coverage # Generate coverage report

# Production
npm run build         # Build for production
npm run start         # Start production server
npm run analyze       # Analyze bundle size

# Type Checking
npm run type-check    # Run TypeScript compiler (no emit)
```

---

## Helpful Resources

- **Next.js Docs**: https://nextjs.org/docs
- **next-intl Guide**: https://next-intl.dev/docs/getting-started/app-router
- **TanStack Query**: https://tanstack.com/query/latest/docs/framework/react/overview
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Vitest**: https://vitest.dev/guide/
- **Playwright**: https://playwright.dev/docs/intro

---

**Setup Time**: ~15 minutes
**First Test**: ~5 minutes
**Quickstart Complete**: You're ready to build! 🚀
