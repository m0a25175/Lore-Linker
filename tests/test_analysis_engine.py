import pytest

from lore_linker.services.analysis_engine import (
    build_phrase_index,
    calculate_cosine_similarity,
    calculate_mutual_appearance,
    extract_story_terms,
    normalize_term,
)


def test_normalize_term():
    assert normalize_term("Aatrox's Embrace") == [
        "AATROXS",
        "EMBRACE",
    ]


def test_longer_phrase_is_preferred():
    dictionary = [
        {"id": 1, "term": "DEMACIA"},
        {"id": 2, "term": "KINGDOM OF DEMACIA"},
    ]

    index = build_phrase_index(dictionary)

    result = extract_story_terms(
        "The Kingdom of Demacia",
        index,
    )

    assert result == {2: 1}


def test_non_overlapping_occurrences_are_counted():
    dictionary = [
        {"id": 1, "term": "DEMACIA"},
        {"id": 2, "term": "KINGDOM OF DEMACIA"},
    ]

    index = build_phrase_index(dictionary)

    result = extract_story_terms(
        "Kingdom of Demacia and Demacia",
        index,
    )

    assert result == {
        1: 1,
        2: 1,
    }


def test_partial_word_does_not_match():
    dictionary = [
        {"id": 1, "term": "DEMACIA"},
    ]

    index = build_phrase_index(dictionary)

    result = extract_story_terms(
        "The Demacian soldier",
        index,
    )

    assert result == {}


def test_cosine_similarity_identical_vectors():
    vector = {1: 2.0, 2: 3.0}

    assert calculate_cosine_similarity(
        vector,
        vector,
    ) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    assert calculate_cosine_similarity(
        {1: 1.0},
        {2: 1.0},
    ) == pytest.approx(0.0)


def test_cosine_similarity_empty_vector():
    assert calculate_cosine_similarity(
        {},
        {1: 1.0},
    ) == 0.0


def test_mutual_appearance_score():
    stories_a = [
        {1, 2},
        {3},
    ]

    stories_b = [
        {1},
        {1, 4},
    ]

    assert calculate_mutual_appearance(
        stories_a,
        stories_b,
    ) == pytest.approx(75.0)


def test_mutual_appearance_without_shared_terms():
    assert calculate_mutual_appearance(
        [{1}],
        [{2}],
    ) == 0.0


def test_mutual_appearance_without_stories():
    assert calculate_mutual_appearance(
        [],
        [{1}],
    ) == 0.0
