# Changelog

## v1.0.0 — 2026-04-25

### Core Engine
- Claude-powered ITGC evidence assessment pipeline (Sonnet 4.6 for assessment, Haiku 4.5 for metadata)
- 58 Vodafone ITGC controls across 10 domains (IAM, Endpoint, Network, HR, Asset Mgmt, CHG, VUL, BCK, INC, Physical)
- Structured `AssessmentResult` model with audit opinion, draft findings, evidence inventory, requirement assessment tables
- Prompt caching for ~90% input cost reduction on repeated control assessments
- CLI (Click) with 4 commands: assess, batch, list-controls, summary
- FastAPI REST API with 9 endpoints including multi-file upload, batch JSON, batch PDF
- Report generation: JSON, Rich CLI tables, and paginated PDF (reportlab)

### Frontend (Next.js 16 + React 19)
- Dashboard with animated stat cards, domain breakdown, verdict distribution
- Controls library with search and domain filtering
- Control detail view showing D and E statements
- Assessment runner with single, batch, and XLSX modes
- Multi-file evidence upload with drag-and-drop
- Per-statement D/E evidence targeting
- Assessment history page with expandable audit detail cards
- Framer Motion spring animations, glassmorphism design system, Outfit font
- Top navigation with animated pill indicator

### Developer Experience
- Makefile with install, demo, test, lint, and API targets
- pytest suite with 4 test modules, mocked Claude client
- Comprehensive README with architecture diagrams and API docs
- MIT License

