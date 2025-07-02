"""
Service layer for codelist similarity operations.

This module provides high-level functions for computing and managing
codelist similarity using the models and algorithms defined in similarity.py.
"""

from typing import List, Tuple, Optional, Dict, Set
from django.db import transaction, models
from django.core.cache import cache
from django.utils import timezone

from .models import (
    CodelistVersion,
    SimilaritySignature,
    SimilarityCluster,
    SimilarityClusterMembership,
    Status
)
from .similarity import MinHashSignature, LSHIndex, compute_exact_jaccard


# Global LSH index instance (will be loaded from database on first use)
_lsh_index = None


def get_lsh_index() -> LSHIndex:
    """Get the global LSH index, loading it from the database if needed."""
    global _lsh_index

    if _lsh_index is None:
        _lsh_index = LSHIndex(num_bands=16, band_size=8)
        _load_lsh_index()

    return _lsh_index


def _load_lsh_index():
    """Load all existing signatures into the LSH index."""
    global _lsh_index

    signatures = SimilaritySignature.objects.all()
    for sig in signatures:
        _lsh_index.add(sig.version.id, sig.signature)


def compute_and_store_signature(version: CodelistVersion) -> SimilaritySignature:
    """
    Compute MinHash signature for a codelist version and store it.

    Args:
        version: CodelistVersion instance

    Returns:
        Created or updated SimilaritySignature instance
    """
    codes = set(version.codes)

    minhash = MinHashSignature(num_hashes=128)
    signature = minhash.compute_signature(codes)

    # Store or update signature
    sig_obj, created = SimilaritySignature.objects.update_or_create(
        version=version,
        defaults={'signature': signature}
    )

    # Update LSH index
    lsh_index = get_lsh_index()
    lsh_index.add(version.id, signature)

    return sig_obj


def find_similar_codelists(version: CodelistVersion,
                          threshold: float = 0.3,
                          max_results: int = 10) -> List[Tuple[CodelistVersion, float]]:
    """
    Find similar codelists using LSH for efficiency.

    Args:
        version: CodelistVersion to find similarities for
        threshold: Minimum similarity threshold (0.0 to 1.0)
        max_results: Maximum number of results to return

    Returns:
        List of (CodelistVersion, similarity_score) tuples, sorted by similarity
    """
    # Get or compute signature for the input version
    try:
        sig_obj = version.similarity_signature
        signature = sig_obj.signature
    except SimilaritySignature.DoesNotExist:
        sig_obj = compute_and_store_signature(version)
        signature = sig_obj.signature

    # Find candidates using LSH
    lsh_index = get_lsh_index()
    candidates = lsh_index.query(signature, threshold=threshold)

    # Filter out the input version itself and get latest versions only
    results = []
    seen_codelists = {version.codelist.id}

    for candidate_id, similarity in candidates[:max_results * 2]:  # Get extra to account for filtering
        try:
            candidate_version = CodelistVersion.objects.get(id=candidate_id)

            # Skip if it's the same codelist or we've already seen this codelist
            if candidate_version.codelist.id in seen_codelists:
                continue

            # Only include latest published versions
            if not _is_latest_published_version(candidate_version):
                continue

            results.append((candidate_version, similarity))
            seen_codelists.add(candidate_version.codelist.id)

            if len(results) >= max_results:
                break

        except CodelistVersion.DoesNotExist:
            # Clean up stale index entry
            lsh_index.remove(candidate_id)
            continue

    # If LSH didn't find enough candidates, try cluster-based search as fallback
    if len(results) < max_results:
        results.extend(_find_similar_by_cluster(version, threshold, max_results - len(results), seen_codelists))

    # Sort by similarity descending and limit results
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:max_results]


def _find_similar_by_cluster(version: CodelistVersion,
                            threshold: float,
                            max_results: int,
                            seen_codelists: set) -> List[Tuple[CodelistVersion, float]]:
    """
    Find similar codelists by looking at cluster membership as fallback.

    Args:
        version: CodelistVersion to find similarities for
        threshold: Minimum similarity threshold
        max_results: Maximum number of results to return
        seen_codelists: Set of codelist IDs already seen

    Returns:
        List of (CodelistVersion, similarity_score) tuples
    """
    from .similarity import compute_exact_jaccard

    results = []
    version_codes = set(version.codes or [])

    # Get all clusters this version belongs to
    memberships = version.cluster_memberships.all()

    for membership in memberships:
        cluster = membership.cluster

        # Get other members of the same cluster
        other_memberships = (
            cluster.memberships
            .exclude(version=version)
            .select_related('version', 'version__codelist')
        )

        for other_membership in other_memberships:
            other_version = other_membership.version

            # Skip if we've already seen this codelist
            if other_version.codelist.id in seen_codelists:
                continue

            # Only include latest published versions
            if not _is_latest_published_version(other_version):
                continue

            # Compute exact similarity
            other_codes = set(other_version.codes or [])
            similarity = compute_exact_jaccard(version_codes, other_codes)

            if similarity >= threshold:
                results.append((other_version, similarity))
                seen_codelists.add(other_version.codelist.id)

                if len(results) >= max_results:
                    return results

    return results


def _is_latest_published_version(version: CodelistVersion) -> bool:
    """Check if a version is the latest published version of its codelist."""
    latest_published = (
        CodelistVersion.objects
        .filter(codelist=version.codelist, status=Status.PUBLISHED)
        .order_by('-created_at')
        .first()
    )
    return latest_published and latest_published.id == version.id


def assign_to_cluster(version: CodelistVersion,
                     threshold: float = 0.3) -> Optional[SimilarityCluster]:
    """
    Assign a codelist version to an existing cluster or create a new one.

    Args:
        version: CodelistVersion to assign
        threshold: Minimum similarity threshold for cluster assignment

    Returns:
        SimilarityCluster instance or None if no suitable cluster found
    """
    similar_codelists = find_similar_codelists(version, threshold=threshold, max_results=5)

    if not similar_codelists:
        # Create new temporary cluster
        cluster = SimilarityCluster.objects.create(
            name=f"Cluster for {version.codelist.name} ({timezone.now().strftime('%Y-%m-%d')})"
        )
        _add_to_cluster(version, cluster, 1.0)
        return cluster

    # Find the best matching cluster
    best_cluster = None
    best_similarity = 0.0

    for similar_version, similarity in similar_codelists:
        # Check if this version is in any clusters
        memberships = similar_version.cluster_memberships.all()
        for membership in memberships:
            if similarity > best_similarity:
                best_cluster = membership.cluster
                best_similarity = similarity

    if best_cluster and best_similarity >= threshold:
        _add_to_cluster(version, best_cluster, best_similarity)
        return best_cluster

    # No suitable cluster found, create new one
    cluster = SimilarityCluster.objects.create(
        name=f"Cluster for {version.codelist.name} ({timezone.now().strftime('%Y-%m-%d')})"
    )
    _add_to_cluster(version, cluster, 1.0)
    return cluster


def _add_to_cluster(version: CodelistVersion,
                   cluster: SimilarityCluster,
                   similarity: float):
    """Add a version to a cluster."""
    SimilarityClusterMembership.objects.update_or_create(
        cluster=cluster,
        version=version,
        defaults={'similarity_to_centroid': similarity}
    )


def get_cluster_members(cluster: SimilarityCluster) -> List[Tuple[CodelistVersion, float]]:
    """Get all members of a cluster with their similarity scores."""
    memberships = (
        cluster.memberships
        .select_related('version', 'version__codelist')
        .order_by('-similarity_to_centroid')
    )

    return [(m.version, m.similarity_to_centroid) for m in memberships]


def invalidate_lsh_index():
    """Invalidate the global LSH index to force reloading."""
    global _lsh_index
    _lsh_index = None
    cache.delete('similarity_lsh_index_loaded')


def bulk_compute_signatures(version_ids: List[int]) -> int:
    """
    Compute signatures for multiple versions efficiently.

    Args:
        version_ids: List of CodelistVersion IDs

    Returns:
        Number of signatures computed
    """
    versions = CodelistVersion.objects.filter(id__in=version_ids)

    computed_count = 0
    for version in versions:
        try:
            compute_and_store_signature(version)
            computed_count += 1
        except Exception as e:
            # Log error but continue with other versions
            print(f"Error computing signature for version {version.id}: {e}")

    return computed_count


def cleanup_stale_clusters():
    """Remove clusters that have no members or only one member."""
    # Remove clusters with no members
    empty_clusters = SimilarityCluster.objects.filter(memberships__isnull=True)
    empty_count = empty_clusters.count()
    empty_clusters.delete()

    # Remove clusters with only one member (convert to holding clusters)
    singleton_clusters = (
        SimilarityCluster.objects
        .annotate(member_count=models.Count('memberships'))
        .filter(member_count=1)
    )
    singleton_count = singleton_clusters.count()
    singleton_clusters.delete()

    return empty_count + singleton_count
