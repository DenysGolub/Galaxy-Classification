PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id TEXT UNIQUE NOT NULL, 
    ra REAL NOT NULL, 
    dec REAL NOT NULL,
    survey_source TEXT NOT NULL, 
    image_path TEXT,
    image_data BLOB, 
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fov REAL 
);

-- Classification results table
CREATE TABLE IF NOT EXISTS classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER NOT NULL,
    model_version TEXT NOT NULL, 
    predicted_class TEXT NOT NULL, 
    confidence REAL NOT NULL, 
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_manual_override BOOLEAN DEFAULT FALSE,
    manual_class TEXT, 
    FOREIGN KEY (observation_id) REFERENCES observations(id)
);

CREATE TABLE IF NOT EXISTS astronomical_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER NOT NULL,
    catalog_source TEXT NOT NULL, 
    object_type TEXT, 
    flux_g REAL,
    flux_r REAL,
    redshift REAL,
    u_magnitude REAL,
    g_magnitude REAL,
    r_magnitude REAL,
    i_magnitude REAL,
    z_magnitude REAL,
    metadata_json TEXT, 
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (observation_id) REFERENCES observations(id)
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    title TEXT 
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL, 
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens_used INTEGER, 
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);

CREATE TABLE IF NOT EXISTS model_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_version TEXT NOT NULL,
    accuracy REAL,
    precision REAL,
    recall REAL,
    f1_score REAL,
    test_dataset TEXT,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER NOT NULL,
    original_prediction TEXT,
    user_correction TEXT NOT NULL,
    feedback_type TEXT, x
    comments TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (observation_id) REFERENCES observations(id)
);

CREATE INDEX IF NOT EXISTS idx_observations_ra_dec ON observations(ra, dec);
CREATE INDEX IF NOT EXISTS idx_observations_created ON observations(captured_at);
CREATE INDEX IF NOT EXISTS idx_classifications_observation ON classifications(observation_id);
CREATE INDEX IF NOT EXISTS idx_classifications_confidence ON classifications(confidence);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_metadata_observation ON astronomical_metadata(observation_id);

CREATE VIEW IF NOT EXISTS recent_observations AS
SELECT
    o.observation_id,
    o.ra,
    o.dec,
    o.survey_source,
    c.predicted_class,
    c.confidence,
    c.classified_at
FROM observations o
LEFT JOIN classifications c ON o.id = c.observation_id
WHERE c.id IS NOT NULL
ORDER BY c.classified_at DESC
LIMIT 50;

CREATE VIEW IF NOT EXISTS classification_stats AS
SELECT
    predicted_class,
    COUNT(*) as count,
    AVG(confidence) as avg_confidence,
    MIN(confidence) as min_confidence,
    MAX(confidence) as max_confidence
FROM classifications
GROUP BY predicted_class
ORDER BY count DESC;
