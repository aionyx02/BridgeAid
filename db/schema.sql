-- BridgeAid PostgreSQL schema (ADR-0003).
-- Mirrors docs/data.md. Apply with:  psql "$DATABASE_URL" -f db/schema.sql
-- Service rules are versioned and source-traceable; recommendations bind to a
-- service id. No migration tooling yet (schema.sql is the source of truth).

CREATE TABLE IF NOT EXISTS source_documents (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    url             TEXT NOT NULL UNIQUE,
    publisher       TEXT,
    last_checked_at DATE NOT NULL,
    checksum        TEXT
);

CREATE TABLE IF NOT EXISTS services (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    category     TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    description  TEXT,
    status       TEXT NOT NULL DEFAULT 'active',
    area_type    TEXT,
    area_value   TEXT
);

CREATE TABLE IF NOT EXISTS service_versions (
    service_id     TEXT NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    version        TEXT NOT NULL,
    effective_from DATE,
    effective_to   DATE,
    review_status  TEXT NOT NULL DEFAULT 'active',
    PRIMARY KEY (service_id, version)
);

CREATE TABLE IF NOT EXISTS eligibility_rules (
    id         SERIAL PRIMARY KEY,
    service_id TEXT NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    version    TEXT NOT NULL,
    rule_jsonb JSONB NOT NULL,
    source_id  INTEGER REFERENCES source_documents(id),
    UNIQUE (service_id, version)
);

CREATE TABLE IF NOT EXISTS required_documents (
    id             SERIAL PRIMARY KEY,
    service_id     TEXT NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    document_name  TEXT NOT NULL,
    condition_jsonb JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS conflict_rules (
    id                  SERIAL PRIMARY KEY,
    service_id          TEXT NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    conflict_service_id TEXT NOT NULL,
    conflict_type       TEXT NOT NULL,
    reason              TEXT NOT NULL
);

-- Anonymous conversation state; minimized fields only (see docs/security.md).
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id             TEXT PRIMARY KEY,
    channel                TEXT NOT NULL,
    extracted_profile_jsonb JSONB NOT NULL DEFAULT '{}'::jsonb,
    expires_at             TIMESTAMPTZ,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recommendation_results (
    id          SERIAL PRIMARY KEY,
    session_id  TEXT REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    result_jsonb JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Opt-in reminders only (see docs/security.md).
CREATE TABLE IF NOT EXISTS reminder_tasks (
    id            SERIAL PRIMARY KEY,
    session_id    TEXT REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    reminder_type TEXT NOT NULL,
    scheduled_at  TIMESTAMPTZ NOT NULL,
    channel       TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_services_category ON services(category);
CREATE INDEX IF NOT EXISTS idx_reminder_status_time ON reminder_tasks(status, scheduled_at);
