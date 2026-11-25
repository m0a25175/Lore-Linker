import sqlite3

from lore_linker.services.database import get_connection

def get_dictionary_terms():
    """
    Retrieve all registered dictionary terms.
    """
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                dictionary_terms.id,
                dictionary_terms.term,
                dictionary_terms.created_at,
                COUNT(story_terms.story_id) AS usage_count
            FROM dictionary_terms
            LEFT JOIN story_terms
                ON dictionary_terms.id = story_terms.term_id
            GROUP BY
                dictionary_terms.id,
                dictionary_terms.term,
                dictionary_terms.created_at
            ORDER BY dictionary_terms.term COLLATE NOCASE
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()

def get_dictionary_term_by_id(term_id):
    """
    Retrieve one dictionary term by its database ID.
    """
    if not isinstance(term_id, int) or term_id <= 0:
        raise ValueError("Invalid dictionary term ID.")

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                term,
                created_at
            FROM dictionary_terms
            WHERE id = ?
            """,
            (term_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()

def add_dictionary_term(term):
    """
    Add a new dictionary term.
    """
    if not isinstance(term, str) or not term.strip():
        raise ValueError("Dictionary term is required.")

    normalized_term = term.strip().upper()

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO dictionary_terms (term)
            VALUES (?)
            """,
            (normalized_term,),
        )

        connection.commit()
        term_id = cursor.lastrowid

        row = connection.execute(
            """
            SELECT
                id,
                term,
                created_at
            FROM dictionary_terms
            WHERE id = ?
            """,
            (term_id,),
        ).fetchone()

        return dict(row)

    except sqlite3.IntegrityError:
        raise ValueError(
            f"Dictionary term already exists: {normalized_term}"
        )

    finally:
        connection.close()

def update_dictionary_term(term_id, term):
    """
    Update an existing dictionary term.
    """
    if not isinstance(term_id, int) or term_id <= 0:
        raise ValueError("Invalid dictionary term ID.")

    if not isinstance(term, str) or not term.strip():
        raise ValueError("Dictionary term is required.")

    normalized_term = term.strip().upper()

    existing_term = get_dictionary_term_by_id(term_id)

    if existing_term is None:
        raise ValueError(f"Dictionary term not found: {term_id}")

    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE dictionary_terms
            SET term = ?
            WHERE id = ?
            """,
            (normalized_term, term_id),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT
                id,
                term,
                created_at
            FROM dictionary_terms
            WHERE id = ?
            """,
            (term_id,),
        ).fetchone()

        return dict(row)

    except sqlite3.IntegrityError:
        raise ValueError(
            f"Dictionary term already exists: {normalized_term}"
        )

    finally:
        connection.close()

def delete_dictionary_term(term_id):
    """
    Delete one dictionary term by its database ID.
    """
    if not isinstance(term_id, int) or term_id <= 0:
        raise ValueError("Invalid dictionary term ID.")

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM dictionary_terms
            WHERE id = ?
            """,
            (term_id,),
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()

def get_dictionary_term_usage_count(term_id):
    """
    Count how many stories use a dictionary term.
    """
    if not isinstance(term_id, int) or term_id <= 0:
        raise ValueError("Invalid dictionary term ID.")

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT COUNT(*) AS usage_count
            FROM story_terms
            WHERE term_id = ?
            """,
            (term_id,),
        ).fetchone()

        return row["usage_count"]

    finally:
        connection.close()

def get_dictionary_overview():
    """
    Retrieve dictionary statistics.
    """
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_terms,
                SUM(
                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM story_terms
                            WHERE story_terms.term_id = dictionary_terms.id
                        )
                        THEN 1
                        ELSE 0
                    END
                ) AS used_terms
            FROM dictionary_terms
            """
        ).fetchone()

        return {
            "total_terms": row["total_terms"],
            "used_terms": row["used_terms"] or 0,
            "unused_terms": (
                row["total_terms"] - (row["used_terms"] or 0)
            ),
        }

    finally:
        connection.close()

def add_dictionary_terms_bulk(terms):
    """
    Register multiple dictionary terms in one transaction.
    Existing terms are skipped.
    """
    if not isinstance(terms, list):
        raise ValueError("Terms must be provided as a list.")

    normalized_terms = []

    for term in terms:
        if not isinstance(term, str) or not term.strip():
            continue

        normalized = term.strip().upper()

        if len(normalized) > 200:
            continue

        if normalized not in normalized_terms:
            normalized_terms.append(normalized)

    if not normalized_terms:
        raise ValueError("No valid dictionary terms were provided.")

    connection = get_connection()

    try:
        inserted_terms = []
        skipped_terms = []

        for term in normalized_terms:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO dictionary_terms (term)
                VALUES (?)
                """,
                (term,),
            )

            if cursor.rowcount == 1:
                inserted_terms.append(term)
            else:
                skipped_terms.append(term)

        connection.commit()

        return {
            "inserted_count": len(inserted_terms),
            "skipped_count": len(skipped_terms),
            "inserted_terms": inserted_terms,
            "skipped_terms": skipped_terms,
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()