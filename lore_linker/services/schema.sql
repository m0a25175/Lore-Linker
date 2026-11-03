PRAGMA foreign_keys = ON;

-- Champions
CREATE TABLE IF NOT EXISTS champions (
    champion_id TEXT PRIMARY KEY,
    name_en TEXT NOT NULL,
    name_ja TEXT,
    title_en TEXT,
    title_ja TEXT,
    lore_en TEXT,
    lore_ja TEXT,
    aliases_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Stories
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    champion_id TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    source_url TEXT,
    registration_method TEXT NOT NULL
        CHECK (registration_method IN ('url', 'manual')),
    content_hash TEXT NOT NULL,
    language_status TEXT NOT NULL
        CHECK (language_status IN ('accepted', 'excluded')),
    language_reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (champion_id)
        REFERENCES champions(champion_id)
);

-- Story duplicate detection indexes
CREATE INDEX IF NOT EXISTS idx_stories_source_url
ON stories(source_url);

CREATE INDEX IF NOT EXISTS idx_stories_content_hash
ON stories(content_hash);

CREATE INDEX IF NOT EXISTS idx_stories_champion_id
ON stories(champion_id);

-- Dictionary Terms
CREATE TABLE IF NOT EXISTS dictionary_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL COLLATE NOCASE UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Story Term Frequencies
CREATE TABLE IF NOT EXISTS story_terms (
    story_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,
    occurrence_count INTEGER NOT NULL
        CHECK (occurrence_count >= 0),

    PRIMARY KEY (story_id, term_id),

    FOREIGN KEY (story_id)
        REFERENCES stories(id)
        ON DELETE CASCADE,

    FOREIGN KEY (term_id)
        REFERENCES dictionary_terms(id)
        ON DELETE CASCADE
);

-- Latest Analysis State
CREATE TABLE IF NOT EXISTS analysis_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    selected_champions_json TEXT NOT NULL DEFAULT '[]',
    threshold REAL NOT NULL DEFAULT 10,
    result_json TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);