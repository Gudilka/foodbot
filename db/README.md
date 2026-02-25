# Настройка БД

По умолчанию в `v1` используется SQLite (`sqlite+aiosqlite:///./foodbot.db`) с автоинициализацией нужных таблиц и справочников при старте приложения.  
Эта папка остаётся источником истины для полной PostgreSQL-схемы расширенного продукта.

## Файлы
- `full_schema.sql`: полная PostgreSQL-схема.
- `seed_reference_data.sql`: базовые справочники (ограничения, категории, теги, планы и т.п.).

## Порядок применения SQL
1. `full_schema.sql`
2. `seed_reference_data.sql`

## Alembic миграции
- `0001_baseline_full_schema`: применяет `full_schema.sql`
- `0002_seed_reference_data`: применяет `seed_reference_data.sql`
- `0003_create_bot_fsm_states`: добавляет `bot_fsm_states` для aiogram FSM storage
- `0004_add_profile_diet_goal`: добавляет `diet_type` и `nutrition_goal` в `user_profiles`

## Поля профиля для onboarding
- `weekly_budget_rub`
- `diet_type` (`omnivore`, `vegetarian`, `vegan`, `pescatarian`, `other`)
- `nutrition_goal` (`weight_loss`, `maintenance`, `muscle_gain`, `health_support`, `medical_diet`, `other`)
- `household_size`
- `dietary_restriction_codes` через `user_dietary_restrictions`

## Покрытые доменные блоки
- Пользователи и профили
- Рецепты, ингредиенты, теги, нутрициология
- Планирование питания и cooking logs
- Списки покупок и остатки
- Чеки, OCR и распознанные позиции
- Расходы, бюджеты, weekly-метрики
- Подписки и платежи
- Партнёрские офферы и клики
- Уведомления, стрики, бейджи
- Event log продуктовой аналитики
