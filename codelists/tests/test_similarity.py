from unittest.mock import patch

from codelists.similarity import compute_exact_jaccard


def test_version_similarity_matrix_no_similar_codelists(
    client, version_with_no_searches
):
    """Test version view when there are no similar codelists."""
    rsp = client.get(version_with_no_searches.get_absolute_url())
    assert rsp.status_code == 200

    # Check that similarity_matrix is empty in context
    assert rsp.context["similarity_matrix"] == []
    assert rsp.context["similar_codelists"] == []


@patch("codelists.views.version.find_similar_codelists")
def test_version_similarity_matrix_with_similar_codelists(
    mock_find_similar, client, version_with_no_searches, latest_published_version
):
    """Test version view with similar codelists creates similarity matrix."""
    # Mock finding similar codelists
    mock_find_similar.return_value = [(latest_published_version, 0.75)]

    # Set up some test codes for similarity computation
    version_with_no_searches.codes = ["123", "456", "789"]
    latest_published_version.codes = ["123", "456", "999"]  # 2/4 = 50% similarity

    rsp = client.get(version_with_no_searches.get_absolute_url())
    assert rsp.status_code == 200

    # Check that similar_codelists is populated
    similar_codelists = rsp.context["similar_codelists"]
    assert len(similar_codelists) == 1
    assert similar_codelists[0]["version"] == latest_published_version
    assert similar_codelists[0]["similarity"] == 75.0  # 0.75 * 100

    # Check that similarity_matrix is populated
    similarity_matrix = rsp.context["similarity_matrix"]
    assert len(similarity_matrix) == 2  # Current version + 1 similar version
    assert len(similarity_matrix[0]) == 2  # 2x2 matrix

    # Check diagonal elements (self-similarity) are 100%
    assert similarity_matrix[0][0]["similarity"] == 100.0
    assert similarity_matrix[1][1]["similarity"] == 100.0

    # Check off-diagonal elements have computed similarities
    assert (
        similarity_matrix[0][1]["similarity"] == similarity_matrix[1][0]["similarity"]
    )

    # Check that version references are correct
    assert similarity_matrix[0][0]["version_i"] == version_with_no_searches
    assert similarity_matrix[0][0]["version_j"] == version_with_no_searches
    assert similarity_matrix[0][1]["version_i"] == version_with_no_searches
    assert similarity_matrix[0][1]["version_j"] == latest_published_version


@patch("codelists.views.version.find_similar_codelists")
def test_version_similarity_matrix_multiple_similar_codelists(
    mock_find_similar,
    client,
    version_with_no_searches,
    latest_published_version,
    user_version,
):
    """Test version view with multiple similar codelists creates larger matrix."""
    # Mock finding multiple similar codelists
    mock_find_similar.return_value = [
        (latest_published_version, 0.60),
        (user_version, 0.40),
    ]

    # Set up test codes
    version_with_no_searches.codes = ["123", "456"]
    latest_published_version.codes = ["123", "789"]
    user_version.codes = ["456", "999"]

    rsp = client.get(version_with_no_searches.get_absolute_url())
    assert rsp.status_code == 200

    # Check that similar_codelists has both versions
    similar_codelists = rsp.context["similar_codelists"]
    assert len(similar_codelists) == 2

    # Check that similarity_matrix is 3x3
    similarity_matrix = rsp.context["similarity_matrix"]
    assert len(similarity_matrix) == 3  # Current + 2 similar versions
    assert all(len(row) == 3 for row in similarity_matrix)

    # Check all diagonal elements are 100%
    for i in range(3):
        assert similarity_matrix[i][i]["similarity"] == 100.0


@patch("codelists.views.version.find_similar_codelists")
def test_version_similarity_matrix_error_handling(
    mock_find_similar, client, version_with_no_searches
):
    """Test version view handles similarity computation errors gracefully."""
    # Mock find_similar_codelists to raise an exception
    mock_find_similar.side_effect = Exception("Test error")

    rsp = client.get(version_with_no_searches.get_absolute_url())
    assert rsp.status_code == 200

    # Check that empty lists are returned when error occurs
    assert rsp.context["similarity_matrix"] == []
    assert rsp.context["similar_codelists"] == []


def test_version_context_includes_similarity_data(client, version_with_no_searches):
    """Test that version view context always includes similarity fields."""
    rsp = client.get(version_with_no_searches.get_absolute_url())
    assert rsp.status_code == 200

    # Check that similarity fields are always in context
    assert "similar_codelists" in rsp.context
    assert "similarity_matrix" in rsp.context

    # Fields should be lists (empty or populated)
    assert isinstance(rsp.context["similar_codelists"], list)
    assert isinstance(rsp.context["similarity_matrix"], list)


def test_similarity_matrix_computation_accuracy():
    """Test that similarity matrix computation matches expected Jaccard values."""
    # Test the mathematical correctness of Jaccard similarity
    # Set intersections and unions
    codes1 = {"123", "456", "789"}
    codes2 = {
        "123",
        "456",
        "999",
    }  # 2 shared (123, 456), 4 total (123, 456, 789, 999) = 0.5
    codes3 = {"123", "111", "222"}  # 1 shared with codes1 (123), 5 total = 0.2

    # Manual computation
    intersection_12 = len(codes1 & codes2)  # {123, 456}
    union_12 = len(codes1 | codes2)  # {123, 456, 789, 999}
    expected_similarity_12 = intersection_12 / union_12  # 2/4 = 0.5

    intersection_13 = len(codes1 & codes3)  # {123}
    union_13 = len(codes1 | codes3)  # {123, 456, 789, 111, 222}
    expected_similarity_13 = intersection_13 / union_13  # 1/5 = 0.2

    # Test that the function computes correctly
    similarity_12 = compute_exact_jaccard(codes1, codes2)
    similarity_13 = compute_exact_jaccard(codes1, codes3)

    assert similarity_12 == expected_similarity_12  # 0.5
    assert similarity_13 == expected_similarity_13  # 0.2

    # Test symmetry
    assert compute_exact_jaccard(codes1, codes2) == compute_exact_jaccard(
        codes2, codes1
    )
    assert compute_exact_jaccard(codes1, codes3) == compute_exact_jaccard(
        codes3, codes1
    )
