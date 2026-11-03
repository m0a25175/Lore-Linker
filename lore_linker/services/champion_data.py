import json
import sqlite3
import urllib.request

from lore_linker.services.database import get_connection

DDRAGON_VERSIONS_URL = (
    "https://ddragon.leagueoflegends.com/api/versions.json"
)


def get_latest_version():
    request = urllib.request.Request(
        DDRAGON_VERSIONS_URL,
        headers={"User-Agent": "LoreLinker/1.0"},
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        versions = json.loads(response.read().decode("utf-8"))

    if not versions:
        raise ValueError("Data Dragon version list is empty.")

    return versions[0]

def get_champion_list(version, language):
    url = (
        f"https://ddragon.leagueoflegends.com/cdn/"
        f"{version}/data/{language}/champion.json"
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "LoreLinker/1.0"},
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data["data"]

def get_champion_detail(version, language, champion_id):
    url = (
        f"https://ddragon.leagueoflegends.com/cdn/"
        f"{version}/data/{language}/champion/"
        f"{champion_id}.json"
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "LoreLinker/1.0"},
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    champion = data["data"].get(champion_id)

    if champion is None:
        raise ValueError(
            f"Champion not found: {champion_id}"
        )

    return champion

def validate_champion_detail(champion):
    required_fields = [
        "id",
        "name",
        "title",
        "lore",
    ]

    missing_fields = [
        field
        for field in required_fields
        if not champion.get(field)
    ]

    if missing_fields:
        return False, missing_fields

    return True, []

def build_champion_records(version):
    english_list = get_champion_list(version, "en_US")
    japanese_list = get_champion_list(version, "ja_JP")

    if set(english_list.keys()) != set(japanese_list.keys()):
        raise ValueError(
            "English and Japanese champion IDs do not match."
        )

    records = []

    for champion_id in sorted(english_list.keys()):
        english = get_champion_detail(
            version,
            "en_US",
            champion_id,
        )

        japanese = get_champion_detail(
            version,
            "ja_JP",
            champion_id,
        )

        en_valid, en_missing = validate_champion_detail(english)
        ja_valid, ja_missing = validate_champion_detail(japanese)

        if not en_valid or not ja_valid:
            raise ValueError(
                f"Invalid champion data: {champion_id}; "
                f"English missing: {en_missing}; "
                f"Japanese missing: {ja_missing}"
            )

        records.append({
            "champion_id": champion_id,
            "name_en": english["name"],
            "name_ja": japanese["name"],
            "title_en": english["title"],
            "title_ja": japanese["title"],
            "lore_en": english["lore"],
            "lore_ja": japanese["lore"],
        })

    return records

def insert_champion_records(records):
    connection = get_connection()

    inserted_count = 0
    skipped_count = 0

    try:
        for record in records:
            existing = connection.execute(
                """
                SELECT champion_id
                FROM champions
                WHERE champion_id = ?
                """,
                (record["champion_id"],),
            ).fetchone()

            if existing:
                skipped_count += 1
                continue

            connection.execute(
                """
                INSERT INTO champions (
                    champion_id,
                    name_en,
                    name_ja,
                    title_en,
                    title_ja,
                    lore_en,
                    lore_ja
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["champion_id"],
                    record["name_en"],
                    record["name_ja"],
                    record["title_en"],
                    record["title_ja"],
                    record["lore_en"],
                    record["lore_ja"],
                ),
            )

            inserted_count += 1

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return inserted_count, skipped_count

def get_registered_champions():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                champion_id,
                name_en,
                name_ja,
                title_en,
                title_ja,
                lore_en,
                lore_ja,
                aliases_json,
                created_at,
                updated_at
            FROM champions
            ORDER BY name_en COLLATE NOCASE
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()
