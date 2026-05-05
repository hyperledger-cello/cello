import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from django.test import SimpleTestCase
from common.utils import safe_urljoin


class SafeUrljoinTests(SimpleTestCase):
    """
    Unit tests for Issue #768: Deal with the trailing slash of agent URL.

    The fix uses safe_urljoin() instead of urllib.parse.urljoin() to correctly
    preserve path segments in the base URL regardless of whether the user
    stored the agent_url with or without a trailing slash.
    """

    def test_base_without_slash_health_endpoint(self):
        """safe_urljoin correctly handles base URL without trailing slash."""
        self.assertEqual(
            safe_urljoin("http://127.0.0.1:5001", "health"),
            "http://127.0.0.1:5001/health"
        )

    def test_base_with_slash_health_endpoint(self):
        """safe_urljoin works correctly when base URL already has trailing slash."""
        self.assertEqual(
            safe_urljoin("http://127.0.0.1:5001/", "health"),
            "http://127.0.0.1:5001/health"
        )

    def test_base_with_path_without_slash(self):
        """safe_urljoin preserves path segment when base has no trailing slash."""
        self.assertEqual(
            safe_urljoin("http://example.com/api", "health"),
            "http://example.com/api/health"
        )

    def test_base_with_path_and_slash(self):
        """safe_urljoin works correctly when base path already ends with slash."""
        self.assertEqual(
            safe_urljoin("http://example.com/api/", "health"),
            "http://example.com/api/health"
        )

    def test_organizations_endpoint(self):
        self.assertEqual(
            safe_urljoin("http://example.com/api", "organizations"),
            "http://example.com/api/organizations"
        )

    def test_nodes_status_endpoint(self):
        self.assertEqual(
            safe_urljoin("http://example.com/api", "nodes/status"),
            "http://example.com/api/nodes/status"
        )

    def test_channels_endpoint(self):
        self.assertEqual(
            safe_urljoin("http://example.com/api", "channels"),
            "http://example.com/api/channels"
        )

    def test_chaincodes_install_endpoint(self):
        self.assertEqual(
            safe_urljoin("http://example.com/api", "chaincodes/install"),
            "http://example.com/api/chaincodes/install"
        )

    def test_original_urljoin_bug(self):
        """Documents the original bug: stdlib urljoin drops path segments."""
        from urllib.parse import urljoin
        # This is the bug: /api is silently dropped
        self.assertEqual(urljoin("http://example.com/api", "health"), "http://example.com/health")
        # safe_urljoin fixes it
        self.assertEqual(safe_urljoin("http://example.com/api", "health"), "http://example.com/api/health")
