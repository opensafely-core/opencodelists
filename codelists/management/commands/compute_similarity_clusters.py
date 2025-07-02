"""
Django management command for nightly similarity clustering.

This command computes exact Jaccard similarities between all published
codelist versions and updates the clustering and LSH index.
"""

import time
from typing import List, Dict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from codelists.models import (
    CodelistVersion,
    SimilaritySignature,
    SimilarityCluster,
    SimilarityClusterMembership,
    Status
)
from codelists.similarity import (
    compute_pairwise_jaccard_matrix,
    cluster_by_similarity,
    MinHashSignature
)
from codelists.similarity_service import (
    bulk_compute_signatures,
    invalidate_lsh_index,
    cleanup_stale_clusters
)


class Command(BaseCommand):
    help = 'Compute similarity clusters for all published codelist versions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.3,
            help=(
                'Minimum Jaccard similarity (0.0-1.0) for clustering codelists together. '
                'Jaccard = |intersection| / |union| of codes. '
                'Lower values (e.g., 0.1) create larger, looser clusters. '
                'Higher values (e.g., 0.5) create smaller, tighter clusters. '
                'Default: 0.3 (30%% code overlap required)'
            )
        )
        parser.add_argument(
            '--max-versions',
            type=int,
            default=None,
            help='Maximum number of versions to process (for testing)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform dry run without saving results'
        )
        parser.add_argument(
            '--force-recompute',
            action='store_true',
            help='Force recomputation of all signatures'
        )

    def handle(self, *args, **options):
        start_time = time.time()

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting similarity clustering at {timezone.now()}"
            )
        )

        threshold = options['threshold']
        max_versions = options['max_versions']
        dry_run = options['dry_run']
        force_recompute = options['force_recompute']

        try:
            # Step 1: Get latest published versions
            versions = self._get_latest_published_versions(max_versions)
            self.stdout.write(f"Found {len(versions)} published codelist versions")

            if not versions:
                self.stdout.write("No published versions found")
                return

            # Step 2: Compute/update signatures
            self._compute_signatures(versions, force_recompute, dry_run)

            # Step 3: Compute exact similarity matrix
            self.stdout.write("Computing pairwise similarity matrix...")
            version_ids = [v.id for v in versions]
            similarity_matrix = compute_pairwise_jaccard_matrix(version_ids)

            # Step 4: Perform clustering
            self.stdout.write(f"Clustering with threshold {threshold}...")
            clusters = cluster_by_similarity(similarity_matrix, version_ids, threshold)

            self.stdout.write(f"Found {len(clusters)} clusters")
            for i, cluster in enumerate(clusters):
                self.stdout.write(f"  Cluster {i+1}: {len(cluster)} versions")

            # Step 5: Update database
            if not dry_run:
                self._update_clusters(clusters, versions, similarity_matrix, version_ids)

                # Step 6: Cleanup and refresh index
                removed_count = cleanup_stale_clusters()
                self.stdout.write(f"Removed {removed_count} stale clusters")

                invalidate_lsh_index()
                self.stdout.write("Refreshed LSH index")

            elapsed = time.time() - start_time
            self.stdout.write(
                self.style.SUCCESS(
                    f"Completed in {elapsed:.2f} seconds"
                )
            )

        except Exception as e:
            raise CommandError(f"Error during clustering: {e}")

    def _get_latest_published_versions(self, max_versions: int = None) -> List[CodelistVersion]:
        """Get the latest published version for each codelist."""
        # Get all published versions, ordered by codelist and creation date
        published_versions = (
            CodelistVersion.objects
            .filter(status=Status.PUBLISHED)
            .select_related('codelist')
            .order_by('codelist_id', '-created_at')
        )

        # Keep only the latest version per codelist
        latest_versions = {}
        for version in published_versions:
            codelist_id = version.codelist.id
            if codelist_id not in latest_versions:
                latest_versions[codelist_id] = version

        versions = list(latest_versions.values())

        if max_versions:
            versions = versions[:max_versions]

        return versions

    def _compute_signatures(self, versions: List[CodelistVersion],
                          force_recompute: bool, dry_run: bool):
        """Compute MinHash signatures for all versions."""
        if force_recompute:
            self.stdout.write("Force recomputing all signatures...")
            if not dry_run:
                # Delete existing signatures
                SimilaritySignature.objects.filter(
                    version__in=versions
                ).delete()

        # Find versions that need signatures
        existing_sigs = set(
            SimilaritySignature.objects
            .filter(version__in=versions)
            .values_list('version_id', flat=True)
        )

        versions_needing_sigs = [
            v for v in versions
            if v.id not in existing_sigs
        ]

        if versions_needing_sigs:
            self.stdout.write(
                f"Computing signatures for {len(versions_needing_sigs)} versions..."
            )

            if not dry_run:
                computed = bulk_compute_signatures([v.id for v in versions_needing_sigs])
                self.stdout.write(f"Computed {computed} signatures")
        else:
            self.stdout.write("All signatures are up to date")

    def _update_clusters(self, clusters: List[List[int]],
                        versions: List[CodelistVersion],
                        similarity_matrix, version_ids: List[int]):
        """Update the cluster database with new clustering results."""
        self.stdout.write("Updating cluster database...")

        # Create mapping from version ID to version object
        version_map = {v.id: v for v in versions}
        id_to_index = {vid: i for i, vid in enumerate(version_ids)}

        with transaction.atomic():
            # Clear existing clusters and memberships
            SimilarityClusterMembership.objects.filter(
                version__in=versions
            ).delete()

            # Create new clusters
            for cluster_idx, cluster_version_ids in enumerate(clusters):
                if len(cluster_version_ids) < 2:
                    continue  # Skip singleton clusters

                # Create cluster with descriptive name
                cluster_versions = [version_map[vid] for vid in cluster_version_ids]
                coding_systems = set(v.codelist.coding_system_id for v in cluster_versions)

                if len(coding_systems) == 1:
                    cluster_name = f"{list(coding_systems)[0]} Cluster {cluster_idx + 1}"
                else:
                    cluster_name = f"Mixed Cluster {cluster_idx + 1}"

                cluster = SimilarityCluster.objects.create(name=cluster_name)

                # Add memberships with similarity to centroid
                centroid_idx = self._find_centroid(cluster_version_ids, similarity_matrix, id_to_index)
                centroid_version_id = cluster_version_ids[centroid_idx]
                centroid_matrix_idx = id_to_index[centroid_version_id]

                for version_id in cluster_version_ids:
                    version = version_map[version_id]
                    matrix_idx = id_to_index[version_id]

                    # Similarity to centroid
                    similarity = similarity_matrix[centroid_matrix_idx, matrix_idx]

                    SimilarityClusterMembership.objects.create(
                        cluster=cluster,
                        version=version,
                        similarity_to_centroid=similarity
                    )

        self.stdout.write(f"Created {len([c for c in clusters if len(c) >= 2])} clusters")

    def _find_centroid(self, cluster_version_ids: List[int],
                      similarity_matrix, id_to_index: Dict[int, int]) -> int:
        """Find the centroid (most similar to all others) in a cluster."""
        indices = [id_to_index[vid] for vid in cluster_version_ids]

        best_idx = 0
        best_avg_similarity = 0

        for i, idx in enumerate(indices):
            # Compute average similarity to all other cluster members
            similarities = [similarity_matrix[idx, other_idx] for other_idx in indices if other_idx != idx]
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0

            if avg_similarity > best_avg_similarity:
                best_avg_similarity = avg_similarity
                best_idx = i

        return best_idx
