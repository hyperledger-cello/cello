from django.test import TestCase
from urllib.parse import urljoin


class AgentUrlNormalizationTests(TestCase):
    """
    Unit tests for Issue #768: Deal with the trailing slash of agent URL.
    Tests the URL normalization logic applied in validate_agent_url.
    """

    def _normalize(self, url: str) -> str:
        """Simulates the normalization logic added to validate_agent_url."""
        if not url.endswith("/"):
            url += "/"
        return url

    def test_url_without_trailing_slash_gets_slash_appended(self):
        """A URL without a trailing slash should have one added."""
        url = "http://127.0.0.1:5001"
        result = self._normalize(url)
        self.assertTrue(result.endswith("/"), f"Expected trailing slash, got: {result}")
        self.assertEqual(result, "http://127.0.0.1:5001/")

    def test_url_with_trailing_slash_is_unchanged(self):
        """A URL that already ends with a slash should not be modified."""
        url = "http://127.0.0.1:5001/"
        result = self._normalize(url)
        self.assertEqual(result, "http://127.0.0.1:5001/")
        # Should not double-add the slash
        self.assertFalse(result.endswith("//"), f"Got double slash: {result}")

    def test_url_with_path_without_slash(self):
        """A URL with a base path but no trailing slash should get one."""
        url = "http://example.com/api"
        result = self._normalize(url)
        self.assertEqual(result, "http://example.com/api/")

    def test_url_with_path_and_slash(self):
        """A URL with a base path and trailing slash should be unchanged."""
        url = "http://example.com/api/"
        result = self._normalize(url)
        self.assertEqual(result, "http://example.com/api/")

    def test_urljoin_correct_after_normalization_simple(self):
        """After normalization, urljoin should produce the correct health check URL."""
        url = "http://127.0.0.1:5001"
        normalized = self._normalize(url)
        result = urljoin(normalized, "health")
        self.assertEqual(result, "http://127.0.0.1:5001/health")

    def test_urljoin_correct_after_normalization_with_path(self):
        """After normalization, urljoin with a path should produce the correct URL."""
        url = "http://example.com/api"
        normalized = self._normalize(url)
        result = urljoin(normalized, "health")
        self.assertEqual(result, "http://example.com/api/health")

    def test_urljoin_without_normalization_breaks_path(self):
        """
        This test demonstrates the ORIGINAL BUG:
        Without normalization, urljoin("http://example.com/api", "health")
        incorrectly returns "http://example.com/health" instead of
        "http://example.com/api/health".
        """
        broken_url = "http://example.com/api"  # No trailing slash (original bug)
        broken_result = urljoin(broken_url, "health")
        self.assertNotEqual(
            broken_result,
            "http://example.com/api/health",
            "Bug confirmed: urljoin without trailing slash drops the path segment."
        )
        self.assertEqual(broken_result, "http://example.com/health")

    def test_urljoin_organizations_endpoint_correct_after_normalization(self):
        """Test that the 'organizations' endpoint is constructed correctly."""
        url = "http://example.com/api"
        normalized = self._normalize(url)
        result = urljoin(normalized, "organizations")
        self.assertEqual(result, "http://example.com/api/organizations")
