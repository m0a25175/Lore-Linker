import sqlite3
from pathlib import Path

DATABASE_PATH = Path.home() / "LoreLinkerData" / "lore_linker.db"

def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    return connection

def initialize_database():
    schema_path = Path(__file__).with_name("schema.sql")

    schema_sql = schema_path.read_text(encoding="utf-8")

    connection = get_connection()

    try:
        connection.executescript(schema_sql)
        connection.commit()
    finally:
        connection.close()

def backup_database():
    from datetime import datetime

    backup_directory = DATABASE_PATH.parent / "backups"
    backup_directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_path = backup_directory / f"lore_linker_{timestamp}.db"

    source_connection = get_connection()
    backup_connection = sqlite3.connect(backup_path)

    try:
        source_connection.backup(backup_connection)
    finally:
        backup_connection.close()
        source_connection.close()

    return backup_path
