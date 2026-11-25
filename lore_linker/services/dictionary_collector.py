import re
from collections import defaultdict
from functools import lru_cache

import spacy

from lore_linker.services.champion_data import get_registered_champions
from lore_linker.services.dictionary_manager import get_dictionary_terms
from lore_linker.services.story_manager import get_stories


@lru_cache(maxsize=1)
def get_nlp():
    try:
        return spacy.load("en_core_web_sm")
    except OSError as error:
        raise RuntimeError(
            "spaCy English model 'en_core_web_sm' is not installed."
        ) from error


IGNORED_SINGLE_WORDS = {
    "A", "AN", "THE",
    "AND", "OR", "BUT",
    "HE", "SHE", "IT", "THEY",
    "HIS", "HER", "ITS", "THEIR",
    "THIS", "THAT", "THESE", "THOSE",
    "WHO", "WHAT", "WHEN", "WHERE",
    "WHICH", "WHILE", "AFTER", "BEFORE",
    "WITH", "FROM", "INTO", "ONTO",
    "ABOUT", "OVER", "UNDER",
    "VERY", "JUST", "ALSO",
    "HAVE", "HAS", "HAD",
    "WAS", "WERE", "ARE", "IS", "BE",
    "DO", "DOES", "DID",
    "CAN", "COULD", "WOULD", "SHOULD",
    "WILL", "SHALL", "MAY", "MIGHT",
    "NOT", "NO", "YES",
    "ONE", "TWO", "THREE",
    "FIRST", "SECOND", "THIRD",
}

# 辞書候補として採用する固有表現ラベル
ACCEPTED_ENTITY_LABELS = {
    "PERSON",
    "NORP",
    "FAC",
    "ORG",
    "GPE",
    "LOC",
    "PRODUCT",
    "EVENT",
    "WORK_OF_ART",
    "LAW",
    "LANGUAGE",
}


def normalize_candidate(term):
    """
    候補語を辞書登録用の形式に正規化する。
    """
    if not isinstance(term, str):
        return ""

    term = term.strip().upper()

    # アポストロフィは削除する
    term = re.sub(r"['’`]", "", term)

    # 英字・数字以外の記号を空白に変換
    term = re.sub(r"[^A-Z0-9]+", " ", term)

    # 連続する空白を整理
    term = re.sub(r"\s+", " ", term).strip()

    # 先頭の冠詞を除去
    term = re.sub(r"^(THE|A|AN)\s+", "", term)

    return term


def _is_valid_candidate(term):
    if not term:
        return False

    words = term.split()

    # 長すぎる名詞句は除外
    if len(words) > 4:
        return False

    # 一般的すぎる単独語は除外
    if len(words) == 1:
        if term in IGNORED_SINGLE_WORDS:
            return False

    # 数字だけの候補は除外
    if not any(character.isalpha() for character in term):
        return False

    return True


def _extract_from_document(nlp, text):
    """
    固有名詞を含む名詞句と、対象ラベルの固有表現を抽出する。
    同じ文章内で同じ範囲が重複した場合は一度だけ数える。
    """
    if not isinstance(text, str) or not text.strip():
        return {}

    doc = nlp(text)

    # (開始位置, 終了位置) -> 正規化候補
    extracted_spans = {}

    # 固有名詞を含む名詞句
    for chunk in doc.noun_chunks:
        if not any(token.pos_ == "PROPN" for token in chunk):
            continue

        normalized = normalize_candidate(chunk.text)

        if _is_valid_candidate(normalized):
            extracted_spans[(chunk.start, chunk.end)] = normalized

    # 固有表現
    for entity in doc.ents:
        if entity.label_ not in ACCEPTED_ENTITY_LABELS:
            continue

        normalized = normalize_candidate(entity.text)

        if _is_valid_candidate(normalized):
            extracted_spans[(entity.start, entity.end)] = normalized

    counts = defaultdict(int)

    for term in extracted_spans.values():
        counts[term] += 1

    return dict(counts)


def collect_dictionary_candidates():
    """
    登録済みチャンピオン情報と英語ストーリーから
    辞書登録候補を抽出する。

    データベースへの書き込みは行わない。
    """
    nlp = get_nlp()

    champions = get_registered_champions()
    stories = get_stories()
    dictionary_terms = get_dictionary_terms()

    existing_terms = {
        normalize_candidate(item["term"])
        for item in dictionary_terms
    }

    candidates = {}

    def add_text(text, source_type, source_name):
        extracted = _extract_from_document(nlp, text)

        for term, count in extracted.items():
            if term in existing_terms:
                continue

            if term not in candidates:
                candidates[term] = {
                    "term": term,
                    "occurrence_count": 0,
                    "sources": set(),
                    "source_types": set(),
                }

            candidate = candidates[term]
            candidate["occurrence_count"] += count
            candidate["sources"].add(source_name)
            candidate["source_types"].add(source_type)

    # チャンピオン情報
    for champion in champions:
        champion_name = champion["name_en"]

        for field in ("name_en", "title_en", "lore_en"):
            text = champion.get(field)

            if not text:
                continue

            add_text(text, "champion", champion_name)

    # 英語として登録されたストーリー
    for story in stories:
        if story.get("language_status") != "accepted":
            continue

        story_title = story.get("title") or "Untitled Story"
        champion_name = story.get("champion_id") or "Unknown Champion"
        source_name = f"{champion_name}: {story_title}"

        add_text(
            story.get("body", ""),
            "story",
            source_name,
        )

        add_text(
            story_title,
            "story",
            source_name,
        )

    result = []

    for candidate in candidates.values():
        result.append({
            "term": candidate["term"],
            "occurrence_count": candidate["occurrence_count"],
            "source_types": sorted(candidate["source_types"]),
            "sources": sorted(candidate["sources"]),
        })

    result.sort(
        key=lambda item: (
            -item["occurrence_count"],
            item["term"],
        )
    )

    return {
        "success": True,
        "total_candidates": len(result),
        "candidates": result,
    }
