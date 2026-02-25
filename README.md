# FoodBOT

Telegram-first bot for registration and profile onboarding.

## Quick start

1. Install dependencies:
```bash
pip install -e ".[dev]"
```
2. Set environment variables in `.env`:
```bash
BOT_TOKEN=...
DATABASE_URL=sqlite+aiosqlite:///./foodbot.db
APP_ENV=local
LOG_LEVEL=INFO
```
3. Run bot:
```bash
python3 -m bot.main
```

On first start the bot auto-creates required tables and seeds reference data.

## PostgreSQL mode (optional)

If you want PostgreSQL instead of SQLite:

1. Set `DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname`.
2. Apply migrations:
```bash
alembic upgrade head
```

## Implemented v1 features

- `/start`: new user onboarding or existing profile view.
- `/profile`: current profile summary.
- `/edit_profile`: full profile re-onboarding in update mode.
- `/cancel`: safe cancel of onboarding.
- DB-based FSM storage (`bot_fsm_states`) for restart-safe wizard state.

## Testing

```bash
pytest -q
```
