-- Retention: delete unused trial leads older than 24 months.
DELETE FROM trial_leads
WHERE created_at < datetime('now', '-24 months')
  AND id NOT IN (SELECT id FROM trial_leads WHERE downloaded_at IS NOT NULL);
