# Database Setup

Runtime default in `v1` is SQLite (`sqlite+aiosqlite:///./foodbot.db`) with auto-bootstrap of required onboarding tables and reference dictionaries at app startup.
This folder remains the PostgreSQL full-schema source of truth for extended domains.

## Files
- `full_schema.sql`: full PostgreSQL schema for MVP + growth features.
- `seed_reference_data.sql`: baseline reference data (restrictions, categories, tags, plans, templates, badges).

## Apply order
1. `full_schema.sql`
2. `seed_reference_data.sql`

## Alembic
- `0001_baseline_full_schema`: applies `full_schema.sql`
- `0002_seed_reference_data`: applies `seed_reference_data.sql`
- `0003_create_bot_fsm_states`: adds `bot_fsm_states` table for aiogram FSM storage

## Domain blocks covered
- Core users and profiles
- Recipes, ingredients, tags, nutrition
- Meal planning and cooking logs
- Shopping lists and pantry leftovers
- Receipts, OCR jobs, parsed receipt items
- Expenses, budgets, weekly metrics
- Subscriptions and payments
- Partner offers and affiliate clicks
- Notifications, streaks, badges
- Product analytics event log
