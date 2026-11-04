import hashlib
import re
import sqlite3

from lore_linker.services.database import get_connection
from lore_linker.services.language_detector import classify_language

def normalize_story_body(body):
    """
    Normalize story body for duplicate detection.
    """
    if not isinstance(body, str):
        raise ValueError("Story body must be a string.")

    normalized = body.strip()
    normalized = re.sub(r"\s+", " ", normalized)

    if not normalized:
        raise ValueError("Story body cannot be empty.")

    return normalized

def generate_content_hash(body):
    """
    Generate SHA-256 hash from normalized story body.
    """
    normalized_body = normalize_story_body(body)

    return hashlib.sha256(
        normalized_body.encode("utf-8")
    ).hexdigest()

def find_story_duplicates(content_hash, source_url=None):
    """
    Find existing stories with the same URL or content hash.
    """
    connection = get_connection()

    try:
        if source_url:
            rows = connection.execute(
                """
                SELECT
                    stories.id,
                    stories.title,
                    stories.champion_id,
                    champions.name_en AS champion_name,
                    stories.source_url
                FROM stories
                JOIN champions
                    ON stories.champion_id = champions.champion_id
                WHERE stories.content_hash = ?
                    OR stories.source_url = ?
                ORDER BY stories.id
                """,
                (content_hash, source_url),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT
                    stories.id,
                    stories.title,
                    stories.champion_id,
                    champions.name_en AS champion_name,
                    stories.source_url
                FROM stories
                JOIN champions
                    ON stories.champion_id = champions.champion_id
                WHERE stories.content_hash = ?
                ORDER BY stories.id
                """,
                (content_hash,),
            ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()

def get_champion_id(champion_name):
    """
    Find champion ID by English or Japanese champion name.
    """
    if not isinstance(champion_name, str) or not champion_name.strip():
        raise ValueError("Champion name is required.")

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT champion_id
            FROM champions
            WHERE name_en = ? COLLATE NOCASE
                OR name_ja = ?
            """,
            (champion_name.strip(), champion_name.strip()),
        ).fetchone()

        if row is None:
            raise ValueError(
                f"Champion not found: {champion_name}"
            )

        return row["champion_id"]

    finally:
        connection.close()

def register_story(
    champion_name,
    title,
    body,
    source_url=None,
    registration_method="url",
    allow_duplicate=False,
):
    """
    Register a story linked to one champion.
    """
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Story title is required.")

    if not isinstance(body, str) or not body.strip():
        raise ValueError("Story body is required.")

    if registration_method not in ("url", "manual"):
        raise ValueError("Invalid registration method.")

    if registration_method == "url":
        if not isinstance(source_url, str) or not source_url.strip():
            raise ValueError("Source URL is required.")

    champion_id = get_champion_id(champion_name)
    content_hash = generate_content_hash(body)

    language_status, language_reason = classify_language(body)

    duplicates = find_story_duplicates(
        content_hash,
        source_url,
    )

    if duplicates and not allow_duplicate:
        return {
            "success": False,
            "duplicate": True,
            "existing_stories": duplicates,
        }

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO stories (
                champion_id,
                title,
                body,
                source_url,
                registration_method,
                content_hash,
                language_status,
                language_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                champion_id,
                title.strip(),
                body,
                source_url.strip() if source_url else None,
                registration_method,
                content_hash,
                language_status,
                language_reason,
            ),
        )

        connection.commit()
        story_id = cursor.lastrowid

    finally:
        connection.close()

    return {
        "success": True,
        "duplicate": bool(duplicates),
        "story_id": story_id,
        "champion_id": champion_id,
        "title": title.strip(),
        "language_status": language_status,
        "language_reason": language_reason,
    }

def get_stories(champion_name=None):
    """
    Retrieve registered stories.
    If champion_name is supplied, filter by that champion.
    """
    connection = get_connection()

    try:
        if champion_name:
            champion_id = get_champion_id(champion_name)

            rows = connection.execute(
                """
                SELECT
                    id,
                    champion_id,
                    title,
                    body,
                    source_url,
                    registration_method,
                    language_status,
                    language_reason,
                    created_at,
                    updated_at
                FROM stories
                WHERE champion_id = ?
                ORDER BY id
                """,
                (champion_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT
                    id,
                    champion_id,
                    title,
                    body,
                    source_url,
                    registration_method,
                    language_status,
                    language_reason,
                    created_at,
                    updated_at
                FROM stories
                ORDER BY id
                """
            ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()

def get_story_by_id(story_id):
    """
    Retrieve one story by its database ID.
    """
    if not isinstance(story_id, int) or story_id <= 0:
        raise ValueError("Invalid story ID.")

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                champion_id,
                title,
                body,
                source_url,
                registration_method,
                content_hash,
                language_status,
                language_reason,
                created_at,
                updated_at
            FROM stories
            WHERE id = ?
            """,
            (story_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()

def update_story(
    story_id,
    champion_name,
    title,
    body,
    source_url=None,
    registration_method="url",
    allow_duplicate=False,
):
    """
    Update an existing story.
    """
    if not isinstance(story_id, int) or story_id <= 0:
        raise ValueError("Invalid story ID.")

    if not isinstance(title, str) or not title.strip():
        raise ValueError("Story title is required.")

    if not isinstance(body, str) or not body.strip():
        raise ValueError("Story body is required.")

    if registration_method not in ("url", "manual"):
        raise ValueError("Invalid registration method.")

    if registration_method == "url":
        if not isinstance(source_url, str) or not source_url.strip():
            raise ValueError("Source URL is required.")

    existing_story = get_story_by_id(story_id)

    if existing_story is None:
        raise ValueError(f"Story not found: {story_id}")

    champion_id = get_champion_id(champion_name)
    content_hash = generate_content_hash(body)

    duplicates = [
        story
        for story in find_story_duplicates(
            content_hash,
            source_url,
        )
        if story["id"] != story_id
    ]

    if duplicates and not allow_duplicate:
        return {
            "success": False,
            "duplicate": True,
            "existing_stories": duplicates,
        }

    if body == existing_story["body"]:
        language_status = existing_story["language_status"]
        language_reason = existing_story["language_reason"]
    else:
        language_status, language_reason = classify_language(body)

    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE stories
            SET
                champion_id = ?,
                title = ?,
                body = ?,
                source_url = ?,
                registration_method = ?,
                content_hash = ?,
                language_status = ?,
                language_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                champion_id,
                title.strip(),
                body,
                source_url.strip() if source_url else None,
                registration_method,
                content_hash,
                language_status,
                language_reason,
                story_id,
            ),
        )

        connection.commit()

    finally:
        connection.close()

    return {
        "success": True,
        "duplicate": bool(duplicates),
        "story_id": story_id,
        "champion_id": champion_id,
        "title": title.strip(),
        "language_status": language_status,
        "language_reason": language_reason,
    }

def delete_story(story_id):
    """
    Delete one story by its database ID.
    """
    if not isinstance(story_id, int) or story_id <= 0:
        raise ValueError("Invalid story ID.")

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM stories
            WHERE id = ?
            """,
            (story_id,),
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()
