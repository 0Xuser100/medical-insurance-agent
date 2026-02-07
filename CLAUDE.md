# medical-insurance-agent Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-07

## Active Technologies
- Files stored in `uploads/` directory, asynchronous job tracking (002-fix-photo-upload)
- TypeScript 5.7 with Next.js 15.5 (App Router) - Frontend; Python 3.11+ with FastAPI - Backend + @tanstack/react-query 5.x (frontend API client), FastAPI 0.100+ (backend) (002-fix-photo-upload)

- TypeScript 5.7 with Next.js 15.5 (App Router) (001-prescription-ui)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

npm test; npm run lint

## Code Style

TypeScript 5.7 with Next.js 15.5 (App Router): Follow standard conventions

## Recent Changes
- 002-fix-photo-upload: Fixed HTTP 405 errors during job status polling by updating frontend endpoint from `/job/{job_id}` to `/result/{job_id}` to match backend API
- 002-fix-photo-upload: Created contract tests for GET /result/{job_id} endpoint (9 tests validating ResultResponse schema)
- 002-fix-photo-upload: Added integration tests verifying correct endpoint usage in job status polling
- 002-fix-photo-upload: Added TypeScript 5.7 with Next.js 15.5 (App Router) - Frontend; Python 3.11+ with FastAPI - Backend + @tanstack/react-query 5.x (frontend API client), FastAPI 0.100+ (backend)
- 002-fix-photo-upload: Added Files stored in `uploads/` directory, asynchronous job tracking

- 001-prescription-ui: Added TypeScript 5.7 with Next.js 15.5 (App Router)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
