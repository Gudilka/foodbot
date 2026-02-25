BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE unit_enum AS ENUM ('g', 'kg', 'ml', 'l', 'pcs');
CREATE TYPE difficulty_enum AS ENUM ('easy', 'medium', 'hard');
CREATE TYPE meal_type_enum AS ENUM ('breakfast', 'lunch', 'dinner', 'snack');
CREATE TYPE plan_status_enum AS ENUM ('draft', 'active', 'completed', 'archived');
CREATE TYPE meal_item_status_enum AS ENUM ('planned', 'cooked', 'skipped', 'replaced');
CREATE TYPE shopping_list_status_enum AS ENUM ('draft', 'active', 'completed', 'archived');
CREATE TYPE shopping_item_source_enum AS ENUM ('from_plan', 'manual', 'from_receipt');
CREATE TYPE ocr_status_enum AS ENUM ('pending', 'processing', 'completed', 'failed', 'needs_review');
CREATE TYPE ocr_provider_enum AS ENUM ('yandex_vision', 'google_vision', 'manual');
CREATE TYPE period_type_enum AS ENUM ('week', 'month');
CREATE TYPE subscription_status_enum AS ENUM ('trial', 'active', 'past_due', 'canceled', 'expired');
CREATE TYPE billing_period_enum AS ENUM ('monthly', 'yearly');
CREATE TYPE payment_status_enum AS ENUM ('pending', 'paid', 'failed', 'refunded');
CREATE TYPE partner_type_enum AS ENUM ('delivery', 'healthy_brand', 'fitness_club');
CREATE TYPE commission_model_enum AS ENUM ('cpa', 'cps', 'revshare');
CREATE TYPE notification_status_enum AS ENUM ('pending', 'sent', 'failed', 'canceled');
CREATE TYPE notification_channel_enum AS ENUM ('telegram', 'push', 'email');
CREATE TYPE event_source_enum AS ENUM ('bot', 'admin', 'system', 'api');
CREATE TYPE expense_source_enum AS ENUM ('receipt', 'manual', 'adjustment');
CREATE TYPE retailer_type_enum AS ENUM ('chain_store', 'online_store', 'marketplace', 'other');
CREATE TYPE offer_context_enum AS ENUM ('shopping_list', 'recipe', 'plan', 'other');

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_user_id BIGINT NOT NULL UNIQUE,
  username TEXT,
  first_name TEXT,
  last_name TEXT,
  language_code TEXT DEFAULT 'ru',
  timezone TEXT DEFAULT 'Europe/Moscow',
  is_bot_blocked BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_profiles (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  currency CHAR(3) NOT NULL DEFAULT 'RUB',
  household_size SMALLINT NOT NULL DEFAULT 1 CHECK (household_size > 0),
  weekly_budget_rub NUMERIC(12,2) NOT NULL CHECK (weekly_budget_rub >= 0),
  diet_type TEXT,
  nutrition_goal TEXT,
  monthly_budget_rub NUMERIC(12,2) CHECK (monthly_budget_rub >= 0),
  cooking_skill SMALLINT CHECK (cooking_skill BETWEEN 1 AND 5),
  max_cook_time_min INTEGER CHECK (max_cook_time_min > 0),
  goal_kcal NUMERIC(8,2) CHECK (goal_kcal >= 0),
  goal_protein_g NUMERIC(8,2) CHECK (goal_protein_g >= 0),
  goal_fat_g NUMERIC(8,2) CHECK (goal_fat_g >= 0),
  goal_carb_g NUMERIC(8,2) CHECK (goal_carb_g >= 0),
  exclude_fast_food BOOLEAN NOT NULL DEFAULT TRUE,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE dietary_restrictions (
  id SMALLSERIAL PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_dietary_restrictions (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  restriction_id SMALLINT NOT NULL REFERENCES dietary_restrictions(id) ON DELETE RESTRICT,
  severity SMALLINT CHECK (severity BETWEEN 1 AND 3),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, restriction_id)
);

CREATE TABLE cuisines (
  id SMALLSERIAL PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_cuisine_preferences (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  cuisine_id SMALLINT NOT NULL REFERENCES cuisines(id) ON DELETE CASCADE,
  priority SMALLINT NOT NULL DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, cuisine_id)
);

CREATE TABLE ingredients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  default_unit unit_enum NOT NULL DEFAULT 'g',
  density_g_per_ml NUMERIC(10,4) CHECK (density_g_per_ml > 0),
  is_allergen BOOLEAN NOT NULL DEFAULT FALSE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ingredient_aliases (
  id BIGSERIAL PRIMARY KEY,
  ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
  alias TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE recipes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  description TEXT,
  servings NUMERIC(6,2) NOT NULL CHECK (servings > 0),
  cook_time_min INTEGER NOT NULL CHECK (cook_time_min > 0),
  difficulty difficulty_enum NOT NULL DEFAULT 'easy',
  source_type TEXT NOT NULL DEFAULT 'internal',
  source_url TEXT,
  language_code CHAR(2) NOT NULL DEFAULT 'ru',
  is_published BOOLEAN NOT NULL DEFAULT TRUE,
  avg_rating NUMERIC(3,2) CHECK (avg_rating BETWEEN 0 AND 5),
  rating_count INTEGER NOT NULL DEFAULT 0 CHECK (rating_count >= 0),
  created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE recipe_steps (
  id BIGSERIAL PRIMARY KEY,
  recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
  step_no INTEGER NOT NULL CHECK (step_no > 0),
  body TEXT NOT NULL,
  timer_seconds INTEGER CHECK (timer_seconds >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (recipe_id, step_no)
);

CREATE TABLE recipe_nutrition (
  recipe_id UUID PRIMARY KEY REFERENCES recipes(id) ON DELETE CASCADE,
  kcal NUMERIC(8,2) NOT NULL CHECK (kcal >= 0),
  protein_g NUMERIC(8,2) NOT NULL CHECK (protein_g >= 0),
  fat_g NUMERIC(8,2) NOT NULL CHECK (fat_g >= 0),
  carb_g NUMERIC(8,2) NOT NULL CHECK (carb_g >= 0),
  fiber_g NUMERIC(8,2) CHECK (fiber_g >= 0),
  sugar_g NUMERIC(8,2) CHECK (sugar_g >= 0),
  sodium_mg NUMERIC(8,2) CHECK (sodium_mg >= 0),
  calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE recipe_tags (
  id SMALLSERIAL PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL
);

CREATE TABLE recipe_tag_links (
  recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
  tag_id SMALLINT NOT NULL REFERENCES recipe_tags(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (recipe_id, tag_id)
);

CREATE TABLE recipe_ingredients (
  id BIGSERIAL PRIMARY KEY,
  recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
  ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE RESTRICT,
  qty NUMERIC(12,3) NOT NULL CHECK (qty > 0),
  unit unit_enum NOT NULL,
  is_optional BOOLEAN NOT NULL DEFAULT FALSE,
  group_name TEXT,
  note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE retailers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  retailer_type retailer_type_enum NOT NULL DEFAULT 'chain_store',
  city TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  retailer_id UUID REFERENCES retailers(id) ON DELETE SET NULL,
  external_sku TEXT,
  name TEXT NOT NULL,
  brand TEXT,
  category TEXT,
  package_size NUMERIC(10,3) CHECK (package_size > 0),
  package_unit unit_enum,
  ingredient_id UUID REFERENCES ingredients(id) ON DELETE SET NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE product_prices (
  id BIGSERIAL PRIMARY KEY,
  product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  retailer_id UUID REFERENCES retailers(id) ON DELETE SET NULL,
  city TEXT NOT NULL DEFAULT '',
  source TEXT NOT NULL DEFAULT 'parser',
  price_rub NUMERIC(12,2) NOT NULL CHECK (price_rub >= 0),
  captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE meal_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  period_type period_type_enum NOT NULL DEFAULT 'week',
  period_start_date DATE NOT NULL,
  period_end_date DATE NOT NULL,
  status plan_status_enum NOT NULL DEFAULT 'draft',
  budget_limit_rub NUMERIC(12,2) NOT NULL CHECK (budget_limit_rub >= 0),
  budget_estimated_rub NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (budget_estimated_rub >= 0),
  budget_actual_rub NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (budget_actual_rub >= 0),
  generation_prompt TEXT,
  generation_model TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, period_type, period_start_date),
  CHECK (period_end_date >= period_start_date)
);

CREATE TABLE meal_plan_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
  plan_date DATE NOT NULL,
  day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
  meal_type meal_type_enum NOT NULL,
  recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE RESTRICT,
  servings NUMERIC(6,2) NOT NULL DEFAULT 1 CHECK (servings > 0),
  estimated_cost_rub NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (estimated_cost_rub >= 0),
  status meal_item_status_enum NOT NULL DEFAULT 'planned',
  replaced_from_item_id UUID REFERENCES meal_plan_items(id) ON DELETE SET NULL,
  is_locked BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (plan_id, plan_date, meal_type)
);

CREATE TABLE cooking_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan_item_id UUID REFERENCES meal_plan_items(id) ON DELETE SET NULL,
  recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE RESTRICT,
  cooked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  servings NUMERIC(6,2) NOT NULL DEFAULT 1 CHECK (servings > 0),
  rating SMALLINT CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  time_spent_min INTEGER CHECK (time_spent_min >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE shopping_lists (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan_id UUID UNIQUE REFERENCES meal_plans(id) ON DELETE SET NULL,
  name TEXT NOT NULL DEFAULT 'Shopping list',
  status shopping_list_status_enum NOT NULL DEFAULT 'draft',
  total_estimated_rub NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (total_estimated_rub >= 0),
  total_actual_rub NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (total_actual_rub >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE shopping_list_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  shopping_list_id UUID NOT NULL REFERENCES shopping_lists(id) ON DELETE CASCADE,
  ingredient_id UUID REFERENCES ingredients(id) ON DELETE SET NULL,
  product_id UUID REFERENCES products(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  qty NUMERIC(12,3) NOT NULL CHECK (qty > 0),
  unit unit_enum NOT NULL,
  category TEXT,
  est_price_rub NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (est_price_rub >= 0),
  actual_price_rub NUMERIC(10,2) CHECK (actual_price_rub >= 0),
  source shopping_item_source_enum NOT NULL DEFAULT 'from_plan',
  is_checked BOOLEAN NOT NULL DEFAULT FALSE,
  position INTEGER NOT NULL DEFAULT 0,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (
    ingredient_id IS NOT NULL OR
    product_id IS NOT NULL OR
    length(trim(title)) > 0
  )
);

CREATE TABLE receipts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  telegram_file_id TEXT NOT NULL,
  image_url TEXT,
  retailer_id UUID REFERENCES retailers(id) ON DELETE SET NULL,
  store_name TEXT,
  purchase_datetime TIMESTAMPTZ,
  total_rub NUMERIC(12,2) CHECK (total_rub >= 0),
  currency CHAR(3) NOT NULL DEFAULT 'RUB',
  status ocr_status_enum NOT NULL DEFAULT 'pending',
  ocr_provider ocr_provider_enum,
  ocr_confidence NUMERIC(4,3) CHECK (ocr_confidence BETWEEN 0 AND 1),
  raw_ocr_json JSONB,
  processing_error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ocr_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  receipt_id UUID NOT NULL UNIQUE REFERENCES receipts(id) ON DELETE CASCADE,
  provider ocr_provider_enum NOT NULL,
  status ocr_status_enum NOT NULL DEFAULT 'pending',
  attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  provider_job_id TEXT,
  error_message TEXT,
  response_json JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (finished_at IS NULL OR finished_at >= requested_at)
);

CREATE TABLE receipt_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  receipt_id UUID NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
  line_no INTEGER NOT NULL CHECK (line_no > 0),
  raw_name TEXT NOT NULL,
  normalized_name TEXT,
  qty NUMERIC(12,3) CHECK (qty >= 0),
  unit unit_enum,
  unit_price_rub NUMERIC(10,2) CHECK (unit_price_rub >= 0),
  line_total_rub NUMERIC(12,2) NOT NULL CHECK (line_total_rub >= 0),
  discount_rub NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (discount_rub >= 0),
  vat_percent NUMERIC(5,2) CHECK (vat_percent >= 0),
  ingredient_id UUID REFERENCES ingredients(id) ON DELETE SET NULL,
  product_id UUID REFERENCES products(id) ON DELETE SET NULL,
  category TEXT,
  confidence NUMERIC(4,3) CHECK (confidence BETWEEN 0 AND 1),
  is_manual_override BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (receipt_id, line_no)
);

CREATE TABLE receipt_item_allocations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  receipt_item_id UUID NOT NULL REFERENCES receipt_items(id) ON DELETE CASCADE,
  shopping_list_item_id UUID REFERENCES shopping_list_items(id) ON DELETE SET NULL,
  allocated_qty NUMERIC(12,3) NOT NULL CHECK (allocated_qty > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (shopping_list_item_id IS NOT NULL)
);

CREATE TABLE pantry_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  ingredient_id UUID REFERENCES ingredients(id) ON DELETE SET NULL,
  source_receipt_item_id UUID REFERENCES receipt_items(id) ON DELETE SET NULL,
  product_name TEXT,
  qty NUMERIC(12,3) NOT NULL CHECK (qty >= 0),
  unit unit_enum NOT NULL,
  purchased_at DATE,
  expires_on DATE,
  price_rub NUMERIC(10,2) CHECK (price_rub >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (ingredient_id IS NOT NULL OR product_name IS NOT NULL)
);

CREATE TABLE expense_categories (
  id SMALLSERIAL PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE expenses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  category_id SMALLINT REFERENCES expense_categories(id) ON DELETE SET NULL,
  source expense_source_enum NOT NULL DEFAULT 'manual',
  entry_date DATE NOT NULL DEFAULT CURRENT_DATE,
  amount_rub NUMERIC(12,2) NOT NULL CHECK (amount_rub >= 0),
  receipt_id UUID REFERENCES receipts(id) ON DELETE SET NULL,
  note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE budget_limits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  category_id SMALLINT REFERENCES expense_categories(id) ON DELETE CASCADE,
  period_type period_type_enum NOT NULL DEFAULT 'week',
  limit_rub NUMERIC(12,2) NOT NULL CHECK (limit_rub >= 0),
  active_from DATE NOT NULL DEFAULT CURRENT_DATE,
  active_to DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (active_to IS NULL OR active_to >= active_from),
  UNIQUE (user_id, category_id, period_type, active_from)
);

CREATE TABLE weekly_user_metrics (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  week_start_date DATE NOT NULL,
  plans_generated_count INTEGER NOT NULL DEFAULT 0 CHECK (plans_generated_count >= 0),
  meals_cooked_count INTEGER NOT NULL DEFAULT 0 CHECK (meals_cooked_count >= 0),
  receipts_uploaded_count INTEGER NOT NULL DEFAULT 0 CHECK (receipts_uploaded_count >= 0),
  spent_rub NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (spent_rub >= 0),
  saved_rub NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (saved_rub >= 0),
  protein_goal_days INTEGER NOT NULL DEFAULT 0 CHECK (protein_goal_days >= 0),
  fast_food_free_days INTEGER NOT NULL DEFAULT 0 CHECK (fast_food_free_days >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, week_start_date)
);

CREATE TABLE subscription_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  billing_period billing_period_enum NOT NULL,
  price_rub NUMERIC(12,2) NOT NULL CHECK (price_rub >= 0),
  trial_days INTEGER NOT NULL DEFAULT 0 CHECK (trial_days >= 0),
  features JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan_id UUID NOT NULL REFERENCES subscription_plans(id) ON DELETE RESTRICT,
  status subscription_status_enum NOT NULL DEFAULT 'trial',
  provider TEXT NOT NULL DEFAULT 'telegram_payments',
  external_subscription_id TEXT,
  auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  current_period_start TIMESTAMPTZ NOT NULL DEFAULT now(),
  current_period_end TIMESTAMPTZ NOT NULL,
  cancel_at TIMESTAMPTZ,
  canceled_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (current_period_end >= current_period_start)
);

CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subscription_id UUID REFERENCES user_subscriptions(id) ON DELETE SET NULL,
  provider TEXT NOT NULL DEFAULT 'telegram_payments',
  external_payment_id TEXT,
  status payment_status_enum NOT NULL DEFAULT 'pending',
  amount_rub NUMERIC(12,2) NOT NULL CHECK (amount_rub >= 0),
  currency CHAR(3) NOT NULL DEFAULT 'RUB',
  paid_at TIMESTAMPTZ,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE partners (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  partner_type partner_type_enum NOT NULL,
  website_url TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE partner_offers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  partner_id UUID NOT NULL REFERENCES partners(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  cta_url TEXT NOT NULL,
  tracking_code TEXT,
  commission_model commission_model_enum NOT NULL DEFAULT 'cpa',
  default_payout_rub NUMERIC(12,2) CHECK (default_payout_rub >= 0),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE partner_clicks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  offer_id UUID NOT NULL REFERENCES partner_offers(id) ON DELETE CASCADE,
  context offer_context_enum NOT NULL DEFAULT 'other',
  clicked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  converted BOOLEAN NOT NULL DEFAULT FALSE,
  conversion_amount_rub NUMERIC(12,2) CHECK (conversion_amount_rub >= 0),
  converted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE notification_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code TEXT NOT NULL UNIQUE,
  channel notification_channel_enum NOT NULL DEFAULT 'telegram',
  title TEXT,
  body_template TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_notification_settings (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  telegram_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  push_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  email_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  sunday_plan_reminder_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  reminder_hour_local SMALLINT NOT NULL DEFAULT 18 CHECK (reminder_hour_local BETWEEN 0 AND 23),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE scheduled_notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  template_id UUID REFERENCES notification_templates(id) ON DELETE SET NULL,
  channel notification_channel_enum NOT NULL DEFAULT 'telegram',
  send_at TIMESTAMPTZ NOT NULL,
  status notification_status_enum NOT NULL DEFAULT 'pending',
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  sent_at TIMESTAMPTZ,
  error_text TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE badges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT,
  icon TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_badges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  badge_id UUID NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
  awarded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, badge_id)
);

CREATE TABLE user_streaks (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  cook_streak_days INTEGER NOT NULL DEFAULT 0 CHECK (cook_streak_days >= 0),
  no_fast_food_streak_days INTEGER NOT NULL DEFAULT 0 CHECK (no_fast_food_streak_days >= 0),
  best_cook_streak_days INTEGER NOT NULL DEFAULT 0 CHECK (best_cook_streak_days >= 0),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE recipe_feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
  rating SMALLINT CHECK (rating BETWEEN 1 AND 5),
  is_liked BOOLEAN,
  comment TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, recipe_id)
);

CREATE TABLE plan_feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan_id UUID NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
  satisfaction_score SMALLINT CHECK (satisfaction_score BETWEEN 1 AND 5),
  comment TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, plan_id)
);

CREATE TABLE event_log (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  event_name TEXT NOT NULL,
  source event_source_enum NOT NULL DEFAULT 'system',
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_users_last_seen_at ON users(last_seen_at DESC);
CREATE INDEX idx_user_profiles_currency ON user_profiles(currency);
CREATE INDEX idx_user_cuisine_preferences_priority ON user_cuisine_preferences(user_id, priority DESC);
CREATE INDEX idx_ingredients_category ON ingredients(category);
CREATE INDEX idx_ingredient_aliases_ingredient_id ON ingredient_aliases(ingredient_id);
CREATE INDEX idx_recipes_published_created ON recipes(is_published, created_at DESC);
CREATE INDEX idx_recipe_steps_recipe_id ON recipe_steps(recipe_id);
CREATE INDEX idx_recipe_tag_links_tag_id ON recipe_tag_links(tag_id);
CREATE INDEX idx_recipe_ingredients_recipe_id ON recipe_ingredients(recipe_id);
CREATE INDEX idx_recipe_ingredients_ingredient_id ON recipe_ingredients(ingredient_id);
CREATE UNIQUE INDEX idx_products_retailer_external_sku_uniq ON products(retailer_id, external_sku) WHERE external_sku IS NOT NULL;
CREATE INDEX idx_products_ingredient_id ON products(ingredient_id);
CREATE INDEX idx_product_prices_product_captured ON product_prices(product_id, captured_at DESC);
CREATE INDEX idx_product_prices_retailer_captured ON product_prices(retailer_id, captured_at DESC);
CREATE INDEX idx_meal_plans_user_period_start ON meal_plans(user_id, period_start_date DESC);
CREATE INDEX idx_meal_plan_items_plan_date ON meal_plan_items(plan_id, plan_date);
CREATE INDEX idx_meal_plan_items_recipe_id ON meal_plan_items(recipe_id);
CREATE INDEX idx_cooking_logs_user_cooked_at ON cooking_logs(user_id, cooked_at DESC);
CREATE INDEX idx_shopping_lists_user_created ON shopping_lists(user_id, created_at DESC);
CREATE INDEX idx_shopping_list_items_list_checked ON shopping_list_items(shopping_list_id, is_checked);
CREATE INDEX idx_receipts_user_purchase_time ON receipts(user_id, purchase_datetime DESC);
CREATE INDEX idx_receipts_status ON receipts(status);
CREATE INDEX idx_ocr_jobs_status_requested ON ocr_jobs(status, requested_at DESC);
CREATE INDEX idx_receipt_items_receipt_id ON receipt_items(receipt_id);
CREATE INDEX idx_receipt_items_ingredient_id ON receipt_items(ingredient_id);
CREATE INDEX idx_receipt_items_product_id ON receipt_items(product_id);
CREATE INDEX idx_pantry_items_user_expires ON pantry_items(user_id, expires_on);
CREATE INDEX idx_expenses_user_entry_date ON expenses(user_id, entry_date DESC);
CREATE INDEX idx_expenses_category_entry_date ON expenses(category_id, entry_date DESC);
CREATE INDEX idx_budget_limits_user_period_active ON budget_limits(user_id, period_type, active_from DESC);
CREATE INDEX idx_weekly_user_metrics_user_week ON weekly_user_metrics(user_id, week_start_date DESC);
CREATE INDEX idx_user_subscriptions_user_status ON user_subscriptions(user_id, status);
CREATE INDEX idx_user_subscriptions_period_end ON user_subscriptions(current_period_end);
CREATE INDEX idx_payments_user_created ON payments(user_id, created_at DESC);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_partner_clicks_offer_time ON partner_clicks(offer_id, clicked_at DESC);
CREATE INDEX idx_partner_clicks_user_time ON partner_clicks(user_id, clicked_at DESC);
CREATE INDEX idx_scheduled_notifications_user_send ON scheduled_notifications(user_id, send_at);
CREATE INDEX idx_scheduled_notifications_status_send ON scheduled_notifications(status, send_at);
CREATE INDEX idx_recipe_feedback_recipe_created ON recipe_feedback(recipe_id, created_at DESC);
CREATE INDEX idx_plan_feedback_plan_id ON plan_feedback(plan_id);
CREATE INDEX idx_event_log_user_time ON event_log(user_id, occurred_at DESC);
CREATE INDEX idx_event_log_name_time ON event_log(event_name, occurred_at DESC);
CREATE INDEX idx_event_log_payload_gin ON event_log USING GIN (payload);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
  table_name TEXT;
BEGIN
  FOREACH table_name IN ARRAY ARRAY[
    'users',
    'user_profiles',
    'ingredients',
    'recipes',
    'recipe_nutrition',
    'retailers',
    'products',
    'meal_plans',
    'meal_plan_items',
    'shopping_lists',
    'shopping_list_items',
    'receipts',
    'ocr_jobs',
    'receipt_items',
    'pantry_items',
    'subscription_plans',
    'user_subscriptions',
    'payments',
    'partners',
    'partner_offers',
    'user_notification_settings',
    'scheduled_notifications',
    'user_streaks',
    'recipe_feedback',
    'plan_feedback'
  ]
  LOOP
    EXECUTE format(
      'CREATE TRIGGER trg_%I_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION set_updated_at();',
      table_name,
      table_name
    );
  END LOOP;
END;
$$;

COMMIT;
