-- Append-only within a cooperating witness SQLite process.
-- Same-UID or host-root mutation remains outside this SQL-trigger guarantee.
PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS witness_meta (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    realm_id TEXT NOT NULL,
    store_id TEXT NOT NULL,
    epoch INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS witness_head (
    sequence INTEGER PRIMARY KEY,
    payload_json TEXT NOT NULL,
    signature TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS witness_head_no_update
BEFORE UPDATE ON witness_head BEGIN
    SELECT RAISE(ABORT, 'witness_head UPDATE forbidden');
END;
CREATE TRIGGER IF NOT EXISTS witness_head_no_delete
BEFORE DELETE ON witness_head BEGIN
    SELECT RAISE(ABORT, 'witness_head DELETE forbidden');
END;
CREATE TABLE IF NOT EXISTS advance_requests (
    request_id TEXT PRIMARY KEY,
    request_digest TEXT NOT NULL,
    assigned_sequence INTEGER NOT NULL REFERENCES witness_head(sequence)
);
