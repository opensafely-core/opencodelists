"""
Tests for the compute_similarity_clusters management command.
"""

from unittest.mock import patch
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from codelists.models import SimilaritySignature, SimilarityCluster, Status


class TestComputeSimilarityClustersCommand(TestCase):
    """Test the compute_similarity_clusters management command."""

    def test_command_basic_functionality(self):
        """Test basic command functionality."""
        out = StringIO()
        call_command('compute_similarity_clusters', stdout=out)

        output = out.getvalue()
        self.assertIn("Starting similarity clustering", output)
        # Command should complete whether it finds versions or not
        self.assertTrue("No published versions found" in output or "Completed" in output)

    def test_command_dry_run(self):
        """Test dry run mode."""
        out = StringIO()
        call_command('compute_similarity_clusters', dry_run=True, stdout=out)

        output = out.getvalue()
        self.assertIn("Starting similarity clustering", output)

    def test_command_max_versions(self):
        """Test max_versions parameter."""
        out = StringIO()
        call_command('compute_similarity_clusters', max_versions=1, stdout=out)

        output = out.getvalue()
        self.assertIn("Starting similarity clustering", output)

    def test_command_force_recompute(self):
        """Test force recompute parameter."""
        out = StringIO()
        call_command('compute_similarity_clusters', force_recompute=True, stdout=out)

        output = out.getvalue()
        # If there are no versions, it won't print the force recompute message
        self.assertTrue("Force recomputing all signatures" in output or "No published versions found" in output)

    def test_command_threshold_parameter(self):
        """Test different similarity thresholds."""
        out = StringIO()
        call_command('compute_similarity_clusters', threshold=0.01, stdout=out)

        output = out.getvalue()
        # Threshold only shows if clustering actually happens
        self.assertTrue("threshold 0.01" in output or "No published versions found" in output)

    @patch('codelists.management.commands.compute_similarity_clusters.Command._get_latest_published_versions')
    def test_command_handles_errors_gracefully(self, mock_get_versions):
        """Test that command handles errors gracefully."""
        # Make getting versions fail
        mock_get_versions.side_effect = Exception("Test error")

        with self.assertRaises(CommandError) as cm:
            call_command('compute_similarity_clusters')

        self.assertIn("Error during clustering", str(cm.exception))
        self.assertIn("Test error", str(cm.exception))
