"""
Codelist similarity computation using MinHash and LSH.

This module implements a hybrid approach for computing codelist similarity:
- Runtime: MinHash signatures with LSH for efficient candidate matching
- Nightly: Exact Jaccard computation for accurate clustering
"""

import hashlib
import random
from collections import defaultdict
from typing import Set, List, Tuple, Dict, Optional

import numpy as np
from django.conf import settings


class MinHashSignature:
    """MinHash signature for efficient set similarity estimation."""

    def __init__(self, num_hashes: int = 128):
        """
        Initialize MinHash with specified number of hash functions.

        Args:
            num_hashes: Number of hash functions to use (default 128)
        """
        self.num_hashes = num_hashes
        # Generate random coefficients for hash functions
        random.seed(42)  # For reproducible signatures
        self.hash_funcs = [
            (random.randint(1, 2**32 - 1), random.randint(0, 2**32 - 1))
            for _ in range(num_hashes)
        ]

    def compute_signature(self, codes: Set[str]) -> List[int]:
        """
        Compute MinHash signature for a set of codes.

        Args:
            codes: Set of code strings

        Returns:
            MinHash signature as list of integers
        """
        if not codes:
            return [2**32 - 1] * self.num_hashes

        # Convert codes to integers using hash function
        code_hashes = [self._string_hash(code) for code in codes]

        signature = []
        for a, b in self.hash_funcs:
            # Apply hash function: (a * x + b) mod p where p is a large prime
            min_hash = min((a * x + b) % (2**32 - 5) for x in code_hashes)
            signature.append(min_hash)

        return signature

    def estimate_jaccard(self, sig1: List[int], sig2: List[int]) -> float:
        """
        Estimate Jaccard similarity from MinHash signatures.

        Args:
            sig1: First MinHash signature
            sig2: Second MinHash signature

        Returns:
            Estimated Jaccard similarity (0.0 to 1.0)
        """
        if len(sig1) != len(sig2):
            raise ValueError("Signatures must have same length")

        matches = sum(1 for a, b in zip(sig1, sig2) if a == b)
        return matches / len(sig1)

    def _string_hash(self, s: str) -> int:
        """Convert string to integer hash."""
        return int(hashlib.md5(s.encode()).hexdigest(), 16) % (2**32)


class LSHIndex:
    """Locality Sensitive Hashing index for fast similarity search."""

    def __init__(self, num_bands: int = 16, band_size: int = 8):
        """
        Initialize LSH index.

        Args:
            num_bands: Number of bands to use
            band_size: Size of each band (num_bands * band_size should equal signature length)
        """
        self.num_bands = num_bands
        self.band_size = band_size
        self.signature_length = num_bands * band_size
        # Each band maps to a set of codelist version IDs
        self.buckets: List[Dict[int, Set[int]]] = [
            defaultdict(set) for _ in range(num_bands)
        ]
        self.signatures: Dict[int, List[int]] = {}

    def add(self, codelist_version_id: int, signature: List[int]):
        """
        Add a codelist version and its signature to the index.

        Args:
            codelist_version_id: ID of the codelist version
            signature: MinHash signature
        """
        if len(signature) != self.signature_length:
            raise ValueError(f"Signature length must be {self.signature_length}")

        self.signatures[codelist_version_id] = signature

        # Add to each band bucket
        for band_idx in range(self.num_bands):
            start = band_idx * self.band_size
            end = start + self.band_size
            band = tuple(signature[start:end])
            band_hash = hash(band)
            self.buckets[band_idx][band_hash].add(codelist_version_id)

    def query(self, signature: List[int], threshold: float = 0.5) -> List[Tuple[int, float]]:
        """
        Find similar codelist versions using LSH.

        Args:
            signature: MinHash signature to query with
            threshold: Minimum similarity threshold

        Returns:
            List of (codelist_version_id, estimated_similarity) tuples
        """
        if len(signature) != self.signature_length:
            raise ValueError(f"Signature length must be {self.signature_length}")

        # Collect candidate matches from all bands
        candidates = set()
        for band_idx in range(self.num_bands):
            start = band_idx * self.band_size
            end = start + self.band_size
            band = tuple(signature[start:end])
            band_hash = hash(band)
            candidates.update(self.buckets[band_idx].get(band_hash, set()))

        # Compute actual similarity estimates for candidates
        minhash = MinHashSignature(self.signature_length)
        results = []
        for candidate_id in candidates:
            candidate_sig = self.signatures[candidate_id]
            similarity = minhash.estimate_jaccard(signature, candidate_sig)
            if similarity >= threshold:
                results.append((candidate_id, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def remove(self, codelist_version_id: int):
        """Remove a codelist version from the index."""
        if codelist_version_id not in self.signatures:
            return

        signature = self.signatures[codelist_version_id]
        del self.signatures[codelist_version_id]

        # Remove from all band buckets
        for band_idx in range(self.num_bands):
            start = band_idx * self.band_size
            end = start + self.band_size
            band = tuple(signature[start:end])
            band_hash = hash(band)
            self.buckets[band_idx][band_hash].discard(codelist_version_id)


def compute_exact_jaccard(codes1: Set[str], codes2: Set[str]) -> float:
    """
    Compute exact Jaccard similarity between two sets of codes.

    Args:
        codes1: First set of codes
        codes2: Second set of codes

    Returns:
        Jaccard similarity (0.0 to 1.0)
    """
    if not codes1 and not codes2:
        return 1.0

    intersection = len(codes1 & codes2)
    union = len(codes1 | codes2)

    return intersection / union if union > 0 else 0.0


def compute_pairwise_jaccard_matrix(codelist_versions: List[int]) -> np.ndarray:
    """
    Compute exact pairwise Jaccard similarity matrix for codelist versions.

    Args:
        codelist_versions: List of codelist version IDs

    Returns:
        Symmetric similarity matrix as numpy array
    """
    from .models import CodelistVersion

    n = len(codelist_versions)
    matrix = np.zeros((n, n))

    # Cache code sets to avoid repeated computation
    code_sets = {}
    for i, clv_id in enumerate(codelist_versions):
        try:
            clv = CodelistVersion.objects.get(id=clv_id)
            code_sets[i] = set(clv.codes)
        except CodelistVersion.DoesNotExist:
            code_sets[i] = set()

    # Compute pairwise similarities
    for i in range(n):
        matrix[i, i] = 1.0  # Self-similarity
        for j in range(i + 1, n):
            similarity = compute_exact_jaccard(code_sets[i], code_sets[j])
            matrix[i, j] = similarity
            matrix[j, i] = similarity  # Symmetric

    return matrix


def cluster_by_similarity(similarity_matrix: np.ndarray,
                         codelist_version_ids: List[int],
                         threshold: float = 0.3) -> List[List[int]]:
    """
    Cluster codelist versions based on similarity matrix using simple threshold clustering.

    Args:
        similarity_matrix: Pairwise similarity matrix
        codelist_version_ids: List of codelist version IDs corresponding to matrix rows
        threshold: Similarity threshold for clustering

    Returns:
        List of clusters, where each cluster is a list of codelist version IDs
    """
    n = len(codelist_version_ids)
    visited = [False] * n
    clusters = []

    for i in range(n):
        if visited[i]:
            continue

        # Start new cluster
        cluster = [codelist_version_ids[i]]
        visited[i] = True

        # Find all similar items
        for j in range(i + 1, n):
            if not visited[j] and similarity_matrix[i, j] >= threshold:
                cluster.append(codelist_version_ids[j])
                visited[j] = True

        clusters.append(cluster)

    return clusters
