# UI — ITGC Evidence Analyser Frontend

Next.js 16 + React 19 frontend for the AI ITGC Evidence Analyser. Provides a modern dashboard, controls library, assessment runner, and assessment history view backed by the FastAPI backend.

## Quick Start

```bash
npm install
npm run dev
```

The dev server starts at `http://localhost:3000`. Requires the backend API at `http://localhost:8001`.

## Pages

| Route | Description |
|---|---|
| `/` | Dashboard — stat cards, domain breakdown, verdict distribution, quick actions |
| `/controls` | Controls Library — searchable list of 58 Vodafone ITGC controls with domain filters |
| `/controls/[id]` | Control Detail — D and E statements with link to assess |
| `/assess` | Assessment Runner — single, batch, and XLSX upload modes with multi-file support |
| `/assessments` | Assessment History — expandable cards with full audit findings, evidence inventory, and assessor notes |

## Tech Stack

- **Next.js 16.2** (App Router, Turbopack)
- **React 19.2**
- **Tailwind CSS v4** — `@tailwindcss/postcss`
- **Framer Motion 12** — spring animations, staggered entry, animated layout transitions
- **Lucide React** — icon library
- **Outfit** (Google Fonts) — primary typeface
- **Geist Mono** — monospace font

## Design System

- Dark theme with noise grain texture and ambient light orbs
- Glassmorphism cards with `backdrop-filter: blur(16px)` and inner border highlights
- Spotlight hover effects via radial gradient masks
- Spring-based motion (stiffness: 400, damping: 30) on all interactive elements
- Staggered entry animations (0.06s delay between children)

## Project Structure

```
ui/
├── app/
│   ├── globals.css          # Design system, CSS variables, animations
│   ├── layout.tsx           # Root layout with TopNav
│   ├── page.tsx             # Dashboard
│   ├── _components/
│   │   ├── TopNav.tsx       # Animated top navigation bar
│   │   ├── VerdictBadge.tsx # PASS/PARTIAL/FAIL/INSUFFICIENT_EVIDENCE badge
│   │   └── RiskBadge.tsx    # CRITICAL/HIGH/MEDIUM/LOW/INFORMATIONAL badge
│   ├── assess/
│   │   └── page.tsx         # Assessment runner
│   ├── assessments/
│   │   └── page.tsx         # Assessment history
│   └── controls/
│       ├── page.tsx         # Controls library
│       └── [id]/
│           └── page.tsx     # Control detail
└── public/                  # Static assets
```

## API Connection

All API calls target `http://localhost:8001/api/v1`. Assessment results are persisted to `localStorage` under the key `assessment_results`.
