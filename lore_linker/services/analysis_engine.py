import json
import math
import re
from itertools import combinations

from lore_linker.services.database import get_connection


DEFAULT_THRESHOLD = 10.0
COMMON_WORD_WEIGHT = 0.7
MUTUAL_APPEARANCE_WEIGHT = 0.3


def normalize_term(term):
    """辞書用語と本文を照合するために正規化する。"""
    if not isinstance(term, str):
        return ""

    term = term.upper()
    term = re.sub(r"['’`]", "", term)
    return re.findall(r"[A-Z0-9]+", term)


def build_phrase_index(dictionary_terms):
    """
    辞書用語を先頭トークン別に整理する。
    同じ開始位置では長いフレーズを優先する。
    """
    index = {}

    for item in dictionary_terms:
        tokens = normalize_term(item["term"])

        if not tokens:
            continue

        index.setdefault(tokens[0], []).append(
            (tuple(tokens), item["id"])
        )

    for first_token in index:
        index[first_token].sort(
            key=lambda item: len(item[0]),
            reverse=True,
        )

    return index


def extract_story_terms(text, phrase_index):
    """
    本文から辞書用語を抽出する。
    長いフレーズを優先し、同じ範囲を二重計上しない。
    """
    tokens = normalize_term(text)
    counts = {}

    position = 0

    while position < len(tokens):
        candidates = phrase_index.get(tokens[position], [])
        matched = None

        for phrase, term_id in candidates:
            end = position + len(phrase)

            if tuple(tokens[position:end]) == phrase:
                matched = (phrase, term_id)
                break

        if matched:
            phrase, term_id = matched
            counts[term_id] = counts.get(term_id, 0) + 1
            position += len(phrase)
        else:
            position += 1

    return counts


def rebuild_story_terms():
    """
    英語として登録された全ストーリーを再解析し、
    story_termsを最新状態に再構築する。
    """
    connection = get_connection()

    try:
        stories = connection.execute(
            """
            SELECT id, body
            FROM stories
            WHERE language_status = 'accepted'
            ORDER BY id
            """
        ).fetchall()

        dictionary_terms = connection.execute(
            """
            SELECT id, term
            FROM dictionary_terms
            ORDER BY id
            """
        ).fetchall()

        phrase_index = build_phrase_index(dictionary_terms)

        records = []

        for story in stories:
            counts = extract_story_terms(
                story["body"],
                phrase_index,
            )

            for term_id, occurrence_count in counts.items():
                records.append((
                    story["id"],
                    term_id,
                    occurrence_count,
                ))

        connection.execute("BEGIN")

        connection.execute("DELETE FROM story_terms")

        if records:
            connection.executemany(
                """
                INSERT INTO story_terms (
                    story_id,
                    term_id,
                    occurrence_count
                )
                VALUES (?, ?, ?)
                """,
                records,
            )

        connection.commit()

        return {
            "success": True,
            "analyzed_stories": len(stories),
            "matched_story_terms": len(records),
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def calculate_cosine_similarity(vector_a, vector_b):
    """2つのTF-IDFベクトルのコサイン類似度。"""
    common_terms = set(vector_a) & set(vector_b)

    dot_product = sum(
        vector_a[term] * vector_b[term]
        for term in common_terms
    )

    norm_a = math.sqrt(
        sum(value * value for value in vector_a.values())
    )
    norm_b = math.sqrt(
        sum(value * value for value in vector_b.values())
    )

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def calculate_mutual_appearance(
    stories_a,
    stories_b,
):
    """
    相手と共通する用語が1つ以上登場するストーリーの割合。
    双方向の平均を返す。
    """
    if not stories_a or not stories_b:
        return 0.0

    terms_a = set().union(*stories_a)
    terms_b = set().union(*stories_b)

    shared_terms = terms_a & terms_b

    if not shared_terms:
        return 0.0

    matched_a = sum(
        1 for story_terms in stories_a
        if story_terms & shared_terms
    )

    matched_b = sum(
        1 for story_terms in stories_b
        if story_terms & shared_terms
    )

    ratio_a = matched_a / len(stories_a)
    ratio_b = matched_b / len(stories_b)

    return ((ratio_a + ratio_b) / 2) * 100


def analyze_network(selected_champions, threshold=DEFAULT_THRESHOLD):
    """
    選択されたチャンピオンの共起ネットワークを分析し、
    最新の分析結果をanalysis_stateに保存する。
    """
    if not isinstance(selected_champions, list) or not selected_champions:
        raise ValueError("Please select at least one champion.")

    if not isinstance(threshold, (int, float)):
        raise ValueError("Threshold must be a number.")

    if not math.isfinite(threshold) or not 0 <= threshold <= 100:
        raise ValueError("Threshold must be between 0 and 100.")

    selected_ids = list(dict.fromkeys(selected_champions))

    if any(
        not isinstance(champion_id, str) or not champion_id.strip()
        for champion_id in selected_ids
    ):
        raise ValueError("Invalid champion selection.")

    rebuild_result = rebuild_story_terms()

    connection = get_connection()

    try:
        placeholders = ",".join("?" for _ in selected_ids)

        champions = connection.execute(
            f"""
            SELECT champion_id, name_en
            FROM champions
            WHERE champion_id IN ({placeholders})
            ORDER BY name_en COLLATE NOCASE
            """,
            selected_ids,
        ).fetchall()

        if len(champions) != len(selected_ids):
            raise ValueError("One or more selected champions were not found.")

        stories = connection.execute(
            f"""
            SELECT id, champion_id, title
            FROM stories
            WHERE language_status = 'accepted'
              AND champion_id IN ({placeholders})
            ORDER BY id
            """,
            selected_ids,
        ).fetchall()

        term_rows = connection.execute(
            f"""
            SELECT
                st.story_id,
                s.champion_id,
                st.term_id,
                st.occurrence_count
            FROM story_terms st
            JOIN stories s ON s.id = st.story_id
            WHERE s.language_status = 'accepted'
              AND s.champion_id IN ({placeholders})
            """,
            selected_ids,
        ).fetchall()

        champion_by_id = {
            row["champion_id"]: row["name_en"]
            for row in champions
        }

        story_ids_by_champion = {
            champion_id: []
            for champion_id in selected_ids
        }

        story_terms_by_id = {}
        term_frequency = {
            champion_id: {}
            for champion_id in selected_ids
        }

        for story in stories:
            story_ids_by_champion[story["champion_id"]].append(
                story["id"]
            )
            story_terms_by_id[story["id"]] = set()

        for row in term_rows:
            champion_id = row["champion_id"]
            term_id = row["term_id"]

            story_terms_by_id[row["story_id"]].add(term_id)

            frequencies = term_frequency[champion_id]
            frequencies[term_id] = (
                frequencies.get(term_id, 0)
                + row["occurrence_count"]
            )

        # IDFは選択されたチャンピオンを対象に計算する。
        champion_count = len(selected_ids)
        document_frequency = {}

        for frequencies in term_frequency.values():
            for term_id in frequencies:
                document_frequency[term_id] = (
                    document_frequency.get(term_id, 0) + 1
                )

        tfidf_vectors = {}

        for champion_id, frequencies in term_frequency.items():
            vector = {}

            for term_id, frequency in frequencies.items():
                tf = 1 + math.log(1 + frequency)

                df = document_frequency[term_id]
                idf = math.log(
                    (champion_count + 1) / (df + 1)
                ) + 1

                vector[term_id] = tf * idf

            tfidf_vectors[champion_id] = vector

        # ノード生成
        nodes = []

        for champion in champions:
            champion_id = champion["champion_id"]

            nodes.append({
                "champion_id": champion_id,
                "name": champion["name_en"],
                "story_count": len(
                    story_ids_by_champion[champion_id]
                ),
                "term_count": len(
                    term_frequency[champion_id]
                ),
            })

        # エッジ生成
        edges = []

        for champion_a, champion_b in combinations(
            selected_ids, 2
        ):
            score_s = calculate_cosine_similarity(
                tfidf_vectors[champion_a],
                tfidf_vectors[champion_b],
            ) * 100

            stories_a = [
                story_terms_by_id[story_id]
                for story_id in story_ids_by_champion[champion_a]
            ]

            stories_b = [
                story_terms_by_id[story_id]
                for story_id in story_ids_by_champion[champion_b]
            ]

            score_d = calculate_mutual_appearance(
                stories_a,
                stories_b,
            )

            score_r = (
                COMMON_WORD_WEIGHT * score_s
                + MUTUAL_APPEARANCE_WEIGHT * score_d
            )

            if score_r < threshold:
                continue

            shared_term_ids = (
                set(term_frequency[champion_a])
                & set(term_frequency[champion_b])
            )

            shared_terms = []

            if shared_term_ids:
                term_placeholders = ",".join(
                    "?" for _ in shared_term_ids
                )

                rows = connection.execute(
                    f"""
                    SELECT term
                    FROM dictionary_terms
                    WHERE id IN ({term_placeholders})
                    ORDER BY term COLLATE NOCASE
                    """,
                    list(shared_term_ids),
                ).fetchall()

                shared_terms = [
                    row["term"] for row in rows
                ]

            edges.append({
                "source": champion_a,
                "target": champion_b,
                "score": round(score_r, 4),
                "common_word_score": round(score_s, 4),
                "mutual_appearance_score": round(score_d, 4),
                "shared_terms": shared_terms,
            })

        edges.sort(
            key=lambda edge: (
                -edge["score"],
                edge["source"],
                edge["target"],
            )
        )

        result = {
            "success": True,
            "threshold": float(threshold),
            "selected_champions": selected_ids,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "rebuild": rebuild_result,
        }

        connection.execute(
            """
            INSERT INTO analysis_state (
                id,
                selected_champions_json,
                threshold,
                result_json,
                updated_at
            )
            VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                selected_champions_json = excluded.selected_champions_json,
                threshold = excluded.threshold,
                result_json = excluded.result_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                json.dumps(selected_ids),
                float(threshold),
                json.dumps(result, ensure_ascii=False),
            ),
        )

        connection.commit()

        return result

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_latest_analysis():
    """最新の分析条件と結果を取得する。"""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                selected_champions_json,
                threshold,
                result_json,
                updated_at
            FROM analysis_state
            WHERE id = 1
            """
        ).fetchone()

        if row is None:
            return None

        return {
            "selected_champions": json.loads(
                row["selected_champions_json"]
            ),
            "threshold": row["threshold"],
            "result": (
                json.loads(row["result_json"])
                if row["result_json"]
                else None
            ),
            "updated_at": row["updated_at"],
        }

    finally:
        connection.close()
