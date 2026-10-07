from sentence_transformers import SentenceTransformer, util


def find_duplicates(issues: list[dict], threshold: float = 0.88) -> dict[int, int]:
    """Embed issue titles with all-MiniLM-L6-v2, compute pairwise cosine similarity.

    Returns {duplicate_issue_number: canonical_issue_number} for all pairs above threshold.
    Canonical = the issue with the smaller number.
    Issues list must have at least 2 items; returns {} for 0 or 1 issues.
    """
    if len(issues) < 2:
        return {}

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    titles = [issue["title"] for issue in issues]
    embeddings = model.encode(titles, convert_to_tensor=True)
    matrix = util.cos_sim(embeddings, embeddings)

    duplicates: dict[int, int] = {}
    for i in range(len(issues)):
        for j in range(i + 1, len(issues)):
            if float(matrix[i][j]) > threshold:
                num_i = issues[i]["number"]
                num_j = issues[j]["number"]
                canonical = min(num_i, num_j)
                duplicate = max(num_i, num_j)
                # Keep lowest canonical if already mapped
                if duplicate in duplicates:
                    duplicates[duplicate] = min(duplicates[duplicate], canonical)
                else:
                    duplicates[duplicate] = canonical

    return duplicates


def annotate_duplicates(
    triage_results: list[dict],
    issues: list[dict],
    threshold: float = 0.88,
) -> list[dict]:
    """Add duplicate_of: int | None to each triage result dict.

    Calls find_duplicates, then mutates and returns triage_results.
    """
    dup_map = find_duplicates(issues, threshold=threshold)
    for result in triage_results:
        result["duplicate_of"] = dup_map.get(result["number"])
    return triage_results
