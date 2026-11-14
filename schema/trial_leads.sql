-- D1 migration — ClinixOS 7-day trial leads
-- The API also creates this table lazily on first request, so the page works
-- even if this migration has not been applied yet.

CREATE TABLE IF NOT EXISTS trial_leads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name TEXT NOT NULL,
  phone_raw TEXT NOT NULL,
  phone_e164 TEXT NOT NULL,
  clinic TEXT DEFAULT '',
  email TEXT DEFAULT '',
  consent INTEGER NOT NULL DEFAULT 0,
  consent_at TEXT,
  source TEXT DEFAULT '',
  utm_source TEXT DEFAULT '',
  utm_medium TEXT DEFAULT '',
  utm_campaign TEXT DEFAULT '',
  page_url TEXT DEFAULT '',
  ip_hash TEXT,
  user_agent TEXT,
  created_at TEXT NOT NULL,
  downloaded_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_trial_leads_created ON trial_leads(created_at);
CREATE INDEX IF NOT EXISTS idx_trial_leads_phone ON trial_leads(phone_e164);
