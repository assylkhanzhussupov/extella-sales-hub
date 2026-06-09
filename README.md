# Extella Sales Hub

AI-powered B2B sales management platform for Extella team.

## Modules

| Module | Status | Description |
|--------|--------|-------------|
| M4: ROP Commander | In Progress | Telegram -> B24 task creation |
| M3: Sales Shadow | Planned | Cron monitoring -> Telegram alerts |
| M1: Client Deep Dive | Planned | Auto-profiling via goszakup.gov.kz |
| M2: RAG Knowledge Base | Planned | Supabase pgvector knowledge assistant |

## Stack

- **Backend:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL + pgvector)
- **Hosting:** Railway (auto-deploy from GitHub)
- **CRM:** Bitrix24
- **Messaging:** Telegram Bot API

## Deploy

Push to `main` -> Railway auto-deploys.

## Environment Variables

See `.env.example` for all required variables.
