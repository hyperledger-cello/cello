from django.test import SimpleTestCase
from urllib.parse import urljoin

from common.utils import normalize_agent_url


class AgentUrlNormalizationTests(SimpleTestCase):
    """
    Unit tests for Issue #768: Deal with the trailing slash of agent URL.
    Tests the real normalize_agent_url utility from common.utils.
    """

    # ── Normalization ─────────────────────────────────────────────────────

    def test_url_without_trailing_slash_gets_slash_appended(self):
        self.assertEqual(normalize_agent_url("http://127.0.0.1:5001"), "http://127.0.0.1:5001/")

    def test_url_with_trailing_slash_is_unchanged(self):
        result = normalize_agent_url("http://127.0.0.1:5001/")
        self.assertEqual(result, "http://127.0.0.1:5001/")
        self.assertFalse(result.endswith("//"))

    def test_url_with_path_without_slash(self):
        self.assertEqual(normalize_agent_url("http://example.com/api"), "http://example.com/api/")

    def test_url_with_path_and_slash_unchanged(self):
        self.assertEqual(normalize_agent_url("http://example.com/api/"), "http://example.com/api/")

    def test_query_string_preserved(self):
        """Query string must not be corrupted by normalization."""
        result = normalize_agent_url("http://example.com/api?key=val")
        self.assertEqual(result, "http://example.com/api/?key=val")
        self.assertNotIn("?key=val/", result)

    def test_normalization_is_idempotent(self):
        """Applying normalize twice should not double-add the slash."""
        url = "http://example.com/api"
        self.assertEqual(normalize_agent_url(normalize_agent_url(url)), normalize_agent_url(url))

    # ── Bug Reproduction ──────────────────────────────────────────────────

    def test_bug_urljoin_without_normalization_drops_path(self):
        """Proves the original bug: urljoin drops path segment without trailing slash."""
        result = urljoin("http://example.com/api", "health")
        self.assertEqual(result, "http://example.com/health")  # Not /api/health

    # ── Fix Validation ────────────────────────────────────────────────────

    def test_fix_health_endpoint_simple(self):
        url = normalize_agent_url("http://127.0.0.1:5001")
        self.assertEqual(urljoin(url, "health"), "http://127.0.0.1:5001/health")

    def test_fix_health_endpoint_with_path(self):
        url = normalize_agent_url("http://example.com/api")
        self.assertEqual(urljoin(url, "health"), "http://example.com/api/health")

    def test_fix_organizations_endpoint(self):
        url = normalize_agent_url("http://example.com/api")
        self.assertEqual(urljoin(url, "organizations"), "http://example.com/api/organizations")
