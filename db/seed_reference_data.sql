BEGIN;

INSERT INTO dietary_restrictions (code, name) VALUES
  ('lactose_free', 'Lactose free'),
  ('gluten_free', 'Gluten free'),
  ('nut_free', 'Nut free'),
  ('vegan', 'Vegan'),
  ('vegetarian', 'Vegetarian'),
  ('halal', 'Halal')
ON CONFLICT (code) DO NOTHING;

INSERT INTO cuisines (code, name) VALUES
  ('russian', 'Russian'),
  ('italian', 'Italian'),
  ('asian', 'Asian'),
  ('georgian', 'Georgian'),
  ('mediterranean', 'Mediterranean'),
  ('mexican', 'Mexican')
ON CONFLICT (code) DO NOTHING;

INSERT INTO expense_categories (code, name) VALUES
  ('groceries', 'Groceries'),
  ('delivery', 'Food delivery'),
  ('cafe', 'Cafe and restaurants'),
  ('snacks', 'Snacks'),
  ('other', 'Other')
ON CONFLICT (code) DO NOTHING;

INSERT INTO recipe_tags (code, name) VALUES
  ('high_protein', 'High protein'),
  ('budget', 'Budget friendly'),
  ('quick', 'Up to 30 minutes'),
  ('meal_prep', 'Meal prep'),
  ('low_carb', 'Low carb')
ON CONFLICT (code) DO NOTHING;

INSERT INTO subscription_plans (code, name, billing_period, price_rub, trial_days, features) VALUES
  (
    'premium_monthly',
    'Premium Monthly',
    'monthly',
    199.00,
    7,
    '{"ocr_limit": "unlimited", "plan_horizon": "month", "ads": false, "pantry_tracking": true}'::jsonb
  ),
  (
    'premium_yearly',
    'Premium Yearly',
    'yearly',
    1490.00,
    7,
    '{"ocr_limit": "unlimited", "plan_horizon": "month", "ads": false, "pantry_tracking": true}'::jsonb
  )
ON CONFLICT (code) DO NOTHING;

INSERT INTO notification_templates (code, channel, title, body_template) VALUES
  ('weekly_plan_ready', 'telegram', 'Weekly plan ready', 'Your meal plan for this week is ready.'),
  ('budget_warning', 'telegram', 'Budget warning', 'You have spent {{spent_rub}} RUB out of {{limit_rub}} RUB.'),
  ('streak_reminder', 'telegram', 'Keep your streak', 'You can keep your cooking streak alive today.')
ON CONFLICT (code) DO NOTHING;

INSERT INTO badges (code, name, description, icon) VALUES
  ('first_week', 'First Week', 'Completed your first weekly plan.', 'badge-first-week'),
  ('week_no_fast_food', 'No Fast Food Week', '7 days without fast food.', 'badge-no-fast-food'),
  ('receipt_master', 'Receipt Master', 'Uploaded 20 receipts.', 'badge-receipt-master'),
  ('budget_keeper', 'Budget Keeper', 'Stayed within budget for 4 weeks.', 'badge-budget-keeper')
ON CONFLICT (code) DO NOTHING;

COMMIT;
