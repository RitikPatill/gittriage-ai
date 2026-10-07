import numpy as np
import pytest
from unittest.mock import MagicMock, patch


ISSUES = [
    {"number": 10, "title": "App crashes on login"},
    {"number": 20, "title": "App crashes on login page"},
    {"number": 30, "title": "Add dark mode support"},
]


def _make_fake_model(embeddings: np.ndarray):
    fake_model = MagicMock()
    fake_model.encode.return_value = embeddings
    return fake_model


def _make_tensor(matrix: list[list[float]]):
    """Return a simple mock tensor that supports float(t[i][j]) indexing."""
    import torch
    return torch.tensor(matrix)


def test_find_duplicates_above_threshold():
    """Two issues whose mock embeddings yield cosine > 0.88 → lower number is canonical."""
    from gittriage.dedup import find_duplicates

    embeddings = np.array([[1.0, 0.0], [0.98, 0.2], [0.0, 1.0]])
    sim_matrix = _make_tensor([
        [1.0, 0.95, 0.0],
        [0.95, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ])

    with patch("gittriage.dedup.SentenceTransformer", return_value=_make_fake_model(embeddings)), \
         patch("gittriage.dedup.util.cos_sim", return_value=sim_matrix):
        result = find_duplicates(ISSUES, threshold=0.88)

    # issue 20 is duplicate of issue 10 (lower number)
    assert result == {20: 10}


def test_find_duplicates_below_threshold():
    """Two issues whose mock embeddings yield cosine <= 0.88 → empty dict returned."""
    from gittriage.dedup import find_duplicates

    embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])
    sim_matrix = _make_tensor([
        [1.0, 0.5],
        [0.5, 1.0],
    ])

    issues = ISSUES[:2]
    with patch("gittriage.dedup.SentenceTransformer", return_value=_make_fake_model(embeddings)), \
         patch("gittriage.dedup.util.cos_sim", return_value=sim_matrix):
        result = find_duplicates(issues, threshold=0.88)

    assert result == {}


def test_find_duplicates_single_issue():
    """One issue → returns {} without calling the model's encode."""
    from gittriage.dedup import find_duplicates

    fake_model = MagicMock()
    with patch("gittriage.dedup.SentenceTransformer", return_value=fake_model):
        result = find_duplicates([ISSUES[0]], threshold=0.88)

    assert result == {}
    fake_model.encode.assert_not_called()


def test_annotate_duplicates_sets_field():
    """duplicate_of is correct for dup issue, None for canonical."""
    from gittriage.dedup import annotate_duplicates

    triage_results = [
        {"number": 10, "label": "bug", "priority": 3, "draft_reply": None},
        {"number": 20, "label": "bug", "priority": 2, "draft_reply": None},
        {"number": 30, "label": "feature", "priority": 1, "draft_reply": None},
    ]

    embeddings = np.array([[1.0, 0.0], [0.98, 0.2], [0.0, 1.0]])
    sim_matrix = _make_tensor([
        [1.0, 0.95, 0.0],
        [0.95, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ])

    with patch("gittriage.dedup.SentenceTransformer", return_value=_make_fake_model(embeddings)), \
         patch("gittriage.dedup.util.cos_sim", return_value=sim_matrix):
        annotated = annotate_duplicates(triage_results, ISSUES, threshold=0.88)

    assert all("duplicate_of" in r for r in annotated)
    canonical = next(r for r in annotated if r["number"] == 10)
    dup = next(r for r in annotated if r["number"] == 20)
    other = next(r for r in annotated if r["number"] == 30)

    assert canonical["duplicate_of"] is None
    assert dup["duplicate_of"] == 10
    assert other["duplicate_of"] is None


def test_annotate_duplicates_no_dups():
    """All pairs below threshold → all duplicate_of are None."""
    from gittriage.dedup import annotate_duplicates

    triage_results = [
        {"number": 10, "label": "bug", "priority": 3, "draft_reply": None},
        {"number": 30, "label": "feature", "priority": 1, "draft_reply": None},
    ]
    issues = [ISSUES[0], ISSUES[2]]

    embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])
    sim_matrix = _make_tensor([
        [1.0, 0.1],
        [0.1, 1.0],
    ])

    with patch("gittriage.dedup.SentenceTransformer", return_value=_make_fake_model(embeddings)), \
         patch("gittriage.dedup.util.cos_sim", return_value=sim_matrix):
        annotated = annotate_duplicates(triage_results, issues, threshold=0.88)

    assert all(r["duplicate_of"] is None for r in annotated)
