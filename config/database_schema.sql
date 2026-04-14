-- Galaxy Classification Database Schema
-- SQLite database for storing galaxy observations, classifications, and user interactions

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Users table (for future multi-user support)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    preferences TEXT -- JSON string for user preferences
);

-- Galaxy observations table
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id TEXT UNIQUE NOT NULL, -- e.g., "GCI-J1951-0258"
    ra REAL NOT NULL, -- Right Ascension in degrees
    dec REAL NOT NULL, -- Declination in degrees
    survey_source TEXT NOT NULL, -- "DESI DR10", "SDSS9", etc.
    image_path TEXT, -- Path to stored image file
    image_data BLOB, -- Optional: store image directly as blob
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fov REAL, -- Field of view in degrees
    created_by INTEGER, -- User ID (nullable for now)
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Classification results table
CREATE TABLE IF NOT EXISTS classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER NOT NULL,
    model_version TEXT NOT NULL, -- e.g., "best_0.8200.pth"
    predicted_class TEXT NOT NULL, -- "Disturbed / Merging", "Smooth", "Spiral", "Edge-on"
    confidence REAL NOT NULL, -- 0.0 to 1.0
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_manual_override BOOLEAN DEFAULT FALSE,
    manual_class TEXT, -- If manually corrected
    corrected_by INTEGER, -- User who made the correction
    FOREIGN KEY (observation_id) REFERENCES observations(id),
    FOREIGN KEY (corrected_by) REFERENCES users(id)
);

-- Astronomical metadata from external catalogs
CREATE TABLE IF NOT EXISTS astronomical_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER NOT NULL,
    catalog_source TEXT NOT NULL, -- "NOIRLab TAP", "Legacy Survey", etc.
    object_type TEXT, -- "GALAXY", "STAR", "QUASAR", etc.
    flux_g REAL,
    flux_r REAL,
    redshift REAL,
    u_magnitude REAL,
    g_magnitude REAL,
    r_magnitude REAL,
    i_magnitude REAL,
    z_magnitude REAL,
    metadata_json TEXT, -- Additional JSON metadata
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (observation_id) REFERENCES observations(id)
);

-- Chat conversations table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    user_id INTEGER,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    title TEXT, -- Optional session title
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Individual chat messages
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL, -- "user" or "assistant"
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens_used INTEGER, -- For tracking API usage
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);

-- Model performance tracking
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

-- User feedback and corrections
CREATE TABLE IF NOT EXISTS user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER NOT NULL,
    user_id INTEGER,
    original_prediction TEXT,
    user_correction TEXT NOT NULL,
    feedback_type TEXT, -- "correction", "confirmation", "uncertain"
    comments TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (observation_id) REFERENCES observations(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_observations_ra_dec ON observations(ra, dec);
CREATE INDEX IF NOT EXISTS idx_observations_created ON observations(captured_at);
CREATE INDEX IF NOT EXISTS idx_classifications_observation ON classifications(observation_id);
CREATE INDEX IF NOT EXISTS idx_classifications_confidence ON classifications(confidence);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_metadata_observation ON astronomical_metadata(observation_id);

-- Views for common queries
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