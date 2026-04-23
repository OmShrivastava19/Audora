# Audora Frontend

> AI-powered lecture intelligence platform — React + TypeScript + Vite + Tailwind CSS v4 + Framer Motion

## Quick Start

**Prerequisites**: Backend must be running at `http://localhost:8000`

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:8501](http://localhost:8501)

## Backend Integration

- **API Base**: `/api` (proxied to `http://localhost:8000` in dev)
- **Runtime Config**: Fetched from `/api/config/public` on app startup
- **Public Config**: Firebase API key, OAuth client ID (loaded from backend)
- **Private Keys**: LLM API keys must be entered in UI per-session (never stored in frontend env)

## Stack

| Layer | Technology |
|---|---|
| Framework | React 19 + TypeScript |
| Build | Vite 8 |
| Styling | Tailwind CSS v4 (CSS-first) |
| Animation | Framer Motion 12 |
| Routing | React Router v7 |
| Server State | TanStack React Query v5 |
| Client State | Zustand v5 (persisted) |
| Icons | Lucide React |
| Upload | React Dropzone |
| Notifications | React Hot Toast |

## Project Structure

```
src/
├── api/               # API client + mock data
│   ├── client.ts      # Typed API client with mock endpoints
│   └── mock-data.ts   # Comprehensive mock data for all screens
├── components/
│   ├── layout/        # AppShell, Sidebar
│   └── ui/            # Button, Card, Badge, Input, DropZone, Progress, Tabs, etc.
├── features/
│   └── results/       # Result workspace panels
│       ├── NotesPanel.tsx
│       ├── ExamRadar.tsx
│       ├── TranscriptPanel.tsx
│       ├── CoverageHeatmap.tsx
│       ├── FlashcardsPanel.tsx
│       ├── QuizPanel.tsx
│       └── DownloadsSection.tsx
├── lib/
│   └── utils.ts       # cn(), formatting helpers, color utilities
├── pages/
│   ├── Landing.tsx    # Hero, features, CTA
│   ├── Auth.tsx       # Login + Register
│   ├── Dashboard.tsx  # Upload + generate
│   ├── Results.tsx    # Full results workspace
│   └── History.tsx    # Lecture history with search/filter
├── store/
│   ├── auth.ts        # Auth state (Zustand + persist)
│   └── app.ts         # App preferences + current result
├── types/
│   └── index.ts       # All DTOs and interfaces
├── App.tsx            # Router + providers
├── main.tsx           # Entry point
└── index.css          # Design system (Tailwind v4 theme)
```

## Pages

| Route | Page | Description |
|---|---|---|
| `/` | Landing | Hero, features, CTA |
| `/login` | Login | Email/password + Google OAuth |
| `/register` | Register | Account creation |
| `/dashboard` | Dashboard | Upload files + generate notes |
| `/results` | Results | Full workspace with all panels |
| `/history` | History | Previous generations with search |

## Design System

The design system is defined in `src/index.css` using Tailwind CSS v4's `@theme` directive:

- **Colors**: Dark academic-tech palette with `#0a0c10` base, `#4fffb0` accent, `#00c4ff` info
- **Typography**: Syne (display), Space Grotesk (body), JetBrains Mono (code)
- **Effects**: Glass cards, noise texture, gradient text, glow shadows
- **Animations**: fade-in, slide-up, scale-in, pulse-glow, shimmer

## Mock Data

All screens use realistic mock data (`src/api/mock-data.ts`) covering:
- 12 transcript segments with timestamps
- 4 structured notes with confidence scoring
- 3 exam hints with urgency levels
- 6 syllabus coverage modules
- 10 flashcards
- 10 mixed quiz items (MCQ, true/false, short answer)
- 5 lecture history entries

## Scripts

```bash
npm run dev        # Start dev server (port 8501)
npm run build      # Production build
npm run preview    # Preview production build
npm run typecheck  # Run TypeScript type checking
```

## API Integration

The `src/api/client.ts` module provides a typed API client with mock implementations.
To connect to a real backend:

1. Update the endpoint methods in `ApiClient` class
2. Remove `sleep()` calls and return real API responses
3. Set the `API_BASE` to your backend URL
4. The Vite proxy is pre-configured to forward `/api` requests

## License

MIT
