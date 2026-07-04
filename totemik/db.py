"""SQLite connection and schema setup for totemik."""

import sqlite3


def get_connection(db_path="habits.db"):
    """Open and return a configured SQLite connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # read rows by column name
    conn.execute("PRAGMA foreign_keys = ON")  # let ON DELETE CASCADE fire
    return conn


def init_db(conn):
    """Create the three tables."""
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS habits (
        id          INTEGER PRIMARY KEY,
        name        TEXT NOT NULL UNIQUE,
        period      TEXT NOT NULL,
        category    TEXT NOT NULL,
        created_at  TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS completions (
        id           INTEGER PRIMARY KEY,
        habit_id     INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
        completed_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS categories (
        name   TEXT PRIMARY KEY,
        level  INTEGER NOT NULL DEFAULT 1,
        points REAL NOT NULL DEFAULT 0.0
    );
    """)
    conn.commit()
