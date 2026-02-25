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
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/foodbot
APP_ENV=local
LOG_LEVEL=INFO
```
3. Apply migrations:
```bash
alembic upgrade head
```
4. Run bot:
```bash
python -m bot.main
```

## Implemented v1 features

- `/start`: new user onboarding or existing profile view.
- `/profile`: current profile summary.
- `/edit_profile`: full profile re-onboarding in update mode.
- `/cancel`: safe cancel of onboarding.
- PostgreSQL-based FSM storage (`bot_fsm_states`) for restart-safe wizard state.

## Testing

```bash
pytest -q
```

Integration and smoke tests require `TEST_DATABASE_URL`; without it they are skipped.
