import unittest
from unittest.mock import patch, MagicMock, call
import re
import os
import sys
import requests 
from bs4 import BeautifulSoup 

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../rpc')))

try:
    from server import Scraper, InvalidRegexError, FetchError, ParseError
    import scraping_pb2
    import common_pb2
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Ensure you are running tests from the 'scraping' directory or have adjusted PYTHONPATH.")
    sys.exit(1)


# Helper function to create mock responses
def create_mock_response(content_bytes, status_code=200, content_type='text/html; charset=utf-8', encoding='utf-8', apparent_encoding='utf-8'):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.headers = {'content-type': content_type}
    mock_resp.content = content_bytes
    mock_resp.encoding = encoding
    mock_resp.apparent_encoding = apparent_encoding
    # Mock raise_for_status
    if status_code >= 400:
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(f"{status_code} Error")
    else:
        mock_resp.raise_for_status.return_value = None
    return mock_resp

class TestScraper(unittest.TestCase):

    def setUp(self):
        # Basic rules used in multiple tests
        self.base_rules = scraping_pb2.ScrapeRules(
            max_depth=2,
            max_pages=5,
            scrape_patterns=[
                scraping_pb2.Rule(url=scraping_pb2.Regex(pattern=r"https://example.com/page/\d+"), css_selector="article"),
                scraping_pb2.Rule(url=scraping_pb2.Regex(pattern=r"https://example.com/main"), css_selector="main") # Default selector test
            ],
            forbidden_urls=[
                scraping_pb2.Regex(pattern=r"https://example.com/forbidden.*")
            ]
        )
        self.entry_url = "https://example.com/main"

    def test_invalid_regex_compilation(self):
        """Test that invalid regex patterns raise InvalidRegexError."""
        invalid_rules = scraping_pb2.ScrapeRules(
            scrape_patterns=[scraping_pb2.Rule(url=scraping_pb2.Regex(pattern="["))] # Invalid regex
        )
        with self.assertRaisesRegex(InvalidRegexError, "Invalid regex pattern"):
            Scraper(invalid_rules)

    @patch('server.requests.get')
    def test_basic_scrape_and_link_following(self, mock_get):
        """Test basic scraping, content extraction, and following valid links."""
        # Mock responses for different URLs
        mock_responses = {
            "https://example.com/main": create_mock_response(
                b'<html><body><main>Main content <a href="/page/1">Link 1</a> <a href="/forbidden">Forbidden</a></main></body></html>'
            ),
            "https://example.com/page/1": create_mock_response(
                b'<html><body><article>Page 1 content <a href="https://external.com">External</a> <a href="/page/2">Link 2</a></article></body></html>'
            ),
             "https://example.com/page/2": create_mock_response(
                b'<html><body><article>Page 2 content</article></body></html>'
            ),
        }
        mock_get.side_effect = lambda url, **kwargs: mock_responses.get(url, create_mock_response(b'', 404))

        scraper = Scraper(self.base_rules)
        documents = scraper.perform_scrape(self.entry_url)

        # Assertions
        self.assertEqual(len(documents), 3)
        self.assertEqual(documents[0].source, "https://example.com/main")
        self.assertIn("Main content", documents[0].content)
        self.assertEqual(documents[1].source, "https://example.com/page/1")
        self.assertIn("Page 1 content", documents[1].content)
        self.assertEqual(documents[2].source, "https://example.com/page/2")
        self.assertIn("Page 2 content", documents[2].content)

        # Check calls to requests.get
        expected_calls = [
            call("https://example.com/main", timeout=10, headers=unittest.mock.ANY),
            call("https://example.com/page/1", timeout=10, headers=unittest.mock.ANY),
            call("https://example.com/page/2", timeout=10, headers=unittest.mock.ANY),
        ]
        mock_get.assert_has_calls(expected_calls, any_order=False) # Order matters due to BFS
        self.assertEqual(mock_get.call_count, 3) # Forbidden link should not be fetched

    @patch('server.requests.get')
    def test_max_depth_limit(self, mock_get):
        """Test that scraping stops at max_depth."""
        rules = scraping_pb2.ScrapeRules(
            max_depth=1, # Limit depth
            max_pages=10,
            scrape_patterns=[scraping_pb2.Rule(url=scraping_pb2.Regex(pattern=r"https://example.com/.*"))]
        )
        mock_responses = {
            "https://example.com/level0": create_mock_response(b'<html><body><main>Level 0 <a href="/level1">L1</a></main></body></html>'),
            "https://example.com/level1": create_mock_response(b'<html><body><main>Level 1 <a href="/level2">L2</a></main></body></html>'),
            "https://example.com/level2": create_mock_response(b'<html><body><main>Level 2</main></body></html>'), # Should not be reached
        }
        mock_get.side_effect = lambda url, **kwargs: mock_responses.get(url, create_mock_response(b'', 404))

        scraper = Scraper(rules)
        documents = scraper.perform_scrape("https://example.com/level0")

        self.assertEqual(len(documents), 2) # Only level 0 and level 1
        self.assertEqual(documents[0].source, "https://example.com/level0")
        self.assertEqual(documents[1].source, "https://example.com/level1")
        mock_get.assert_has_calls([
            call("https://example.com/level0", timeout=10, headers=unittest.mock.ANY),
            call("https://example.com/level1", timeout=10, headers=unittest.mock.ANY),
        ], any_order=False)
        self.assertEqual(mock_get.call_count, 2)

    @patch('server.requests.get')
    def test_max_pages_limit(self, mock_get):
        """Test that scraping stops at max_pages."""
        rules = scraping_pb2.ScrapeRules(
            max_depth=5,
            max_pages=2, # Limit pages
            scrape_patterns=[scraping_pb2.Rule(url=scraping_pb2.Regex(pattern=r"https://example.com/.*"))]
        )
        mock_responses = {
            "https://example.com/p1": create_mock_response(b'<html><body><main>Page 1 <a href="/p2">P2</a> <a href="/p3">P3</a></main></body></html>'),
            "https://example.com/p2": create_mock_response(b'<html><body><main>Page 2</main></body></html>'),
            "https://example.com/p3": create_mock_response(b'<html><body><main>Page 3</main></body></html>'), # Should not be reached
        }
        mock_get.side_effect = lambda url, **kwargs: mock_responses.get(url, create_mock_response(b'', 404))

        scraper = Scraper(rules)
        documents = scraper.perform_scrape("https://example.com/p1")

        self.assertEqual(len(documents), 2) # Only p1 and p2
        self.assertEqual(documents[0].source, "https://example.com/p1")
        self.assertEqual(documents[1].source, "https://example.com/p2")
        mock_get.assert_has_calls([
            call("https://example.com/p1", timeout=10, headers=unittest.mock.ANY),
            call("https://example.com/p2", timeout=10, headers=unittest.mock.ANY),
        ], any_order=False)
        self.assertEqual(mock_get.call_count, 2)

    @patch('server.requests.get')
    def test_forbidden_url(self, mock_get):
        """Test that forbidden URLs are not fetched or processed."""
        mock_responses = {
            "https://example.com/main": create_mock_response(
                b'<html><body><main>Main content <a href="/page/1">Link 1</a> <a href="/forbidden">Forbidden Link</a></main></body></html>'
            ),
            "https://example.com/page/1": create_mock_response(
                b'<html><body><article>Page 1 content</article></body></html>'
            ),
             # No entry for /forbidden, as it shouldn't be called
        }
        mock_get.side_effect = lambda url, **kwargs: mock_responses.get(url, create_mock_response(b'', 404))

        scraper = Scraper(self.base_rules)
        documents = scraper.perform_scrape(self.entry_url)

        self.assertEqual(len(documents), 2)
        mock_get.assert_has_calls([
            call("https://example.com/main", timeout=10, headers=unittest.mock.ANY),
            call("https://example.com/page/1", timeout=10, headers=unittest.mock.ANY),
        ], any_order=False)
        # Ensure forbidden URL was never requested
        for mock_call in mock_get.call_args_list:
            self.assertNotIn("forbidden", mock_call.args[0])
        self.assertEqual(mock_get.call_count, 2)


    @patch('server.requests.get')
    def test_fetch_error_handling(self, mock_get):
        """Test that fetching errors (timeout, HTTP error) are handled gracefully."""
        # Define rules specific to this test to ensure error URLs are processed
        fetch_error_rules = scraping_pb2.ScrapeRules(
            max_depth=2,
            max_pages=5,
            scrape_patterns=[
                scraping_pb2.Rule(url=scraping_pb2.Regex(pattern=r"https://example.com/main"), css_selector="main"),
                scraping_pb2.Rule(url=scraping_pb2.Regex(pattern=r"https://example.com/page/.*"), css_selector="article") # Match all /page/ URLs
            ],
            forbidden_urls=[]
        )

        mock_responses = {
            "https://example.com/main": create_mock_response(
                b'<html><body><main>Main content <a href="/page/1">OK</a> <a href="/page/error">Error</a> <a href="/page/timeout">Timeout</a></main></body></html>'
            ),
            "https://example.com/page/1": create_mock_response(
                b'<html><body><article>Page 1 content</article></body></html>'
            ),
            # Error and Timeout URLs will be handled by the side_effect
        }
        def side_effect(url, **kwargs):
            if url == "https://example.com/page/error":
                # Simulate HTTP 500 error
                return create_mock_response(b'', 500)
            if url == "https://example.com/page/timeout":
                raise requests.exceptions.Timeout("Request timed out")
            return mock_responses.get(url, create_mock_response(b'', 404))

        mock_get.side_effect = side_effect

        scraper = Scraper(fetch_error_rules) # Use the specific rules
        documents = scraper.perform_scrape(self.entry_url)

        # Only main and page/1 should yield documents
        self.assertEqual(len(documents), 2)
        self.assertEqual(documents[0].source, "https://example.com/main")
        self.assertEqual(documents[1].source, "https://example.com/page/1")

        # Check all attempts were made
        self.assertEqual(mock_get.call_count, 4) # main, page/1, page/error, page/timeout

    @patch('server.requests.get')
    @patch('server.BeautifulSoup')
    def test_parse_error_handling(self, mock_bs, mock_get):
        """Test that HTML parsing errors are handled gracefully."""
         # Define rules specific to this test
        parse_error_rules = scraping_pb2.ScrapeRules(
            max_depth=2,
            max_pages=5,
            scrape_patterns=[
                scraping_pb2.Rule(url=scraping_pb2.Regex(pattern=r"https://example.com/main"), css_selector="main"),
                scraping_pb2.Rule(url=scraping_pb2.Regex(pattern=r"https://example.com/page/.*"), css_selector="article") # Match all /page/ URLs
            ],
            forbidden_urls=[]
        )
        mock_responses = {
            "https://example.com/main": create_mock_response(
                b'<html><body><main>Main content <a href="/page/good">Good</a> <a href="/page/bad">Bad Parse</a></main></body></html>'
            ),
            "https://example.com/page/good": create_mock_response(
                b'<html><body><article>Good Page</article></body></html>'
            ),
            "https://example.com/page/bad": create_mock_response(
                b'<html><body><article>This will cause error</article>' # Malformed
            ),
        }
        mock_get.side_effect = lambda url, **kwargs: mock_responses.get(url, create_mock_response(b'', 404))

        # Make BeautifulSoup raise an error for the bad page
        real_bs = BeautifulSoup
        def bs_side_effect(markup, parser, from_encoding):
            if b"This will cause error" in markup:
                raise ValueError("Simulated parsing error")
            # Use **kwargs to handle potential future changes in BS constructor
            return real_bs(markup, parser, from_encoding=from_encoding)
        mock_bs.side_effect = bs_side_effect

        scraper = Scraper(parse_error_rules) # Use the specific rules
        documents = scraper.perform_scrape(self.entry_url)

        # Only main and good page should yield documents
        self.assertEqual(len(documents), 2)
        self.assertEqual(documents[0].source, "https://example.com/main")
        self.assertEqual(documents[1].source, "https://example.com/page/good")
        self.assertEqual(mock_get.call_count, 3) # main, good, bad

    @patch('server.requests.get')
    def test_css_selector_fallback(self, mock_get):
        """Test fallback to 'body' if specified selector is not found."""
        rules = scraping_pb2.ScrapeRules(
            scrape_patterns=[
                scraping_pb2.Rule(url=scraping_pb2.Regex(pattern=r".*"), css_selector="#nonexistent")
            ]
        )
        mock_get.return_value = create_mock_response(
            b'<html><head><title>Test</title></head><body><p>Body content</p></body></html>'
        )

        scraper = Scraper(rules)
        documents = scraper.perform_scrape("https://example.com/test")

        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].source, "https://example.com/test")
        self.assertIn("Body content", documents[0].content) # Content should be from body
        self.assertNotIn("Test", documents[0].content) # Should not include head title
        mock_get.assert_called_once_with("https://example.com/test", timeout=10, headers=unittest.mock.ANY)

    @patch('server.requests.get')
    def test_no_scrape_rules(self, mock_get):
        """Test behavior when no scrape_patterns are provided (should follow all non-forbidden links)."""
        rules = scraping_pb2.ScrapeRules(
            max_depth=1,
            max_pages=5,
            scrape_patterns=[], # No specific patterns
            forbidden_urls=[scraping_pb2.Regex(pattern=r".*/forbidden")]
        )
        mock_responses = {
            "https://example.com/start": create_mock_response(b'<html><body>Start <a href="/page1">1</a> <a href="/page2">2</a> <a href="/forbidden">F</a></body></html>'),
            "https://example.com/page1": create_mock_response(b'<html><body>Page 1</body></html>'),
            "https://example.com/page2": create_mock_response(b'<html><body>Page 2</body></html>'),
        }
        mock_get.side_effect = lambda url, **kwargs: mock_responses.get(url, create_mock_response(b'', 404))

        scraper = Scraper(rules)
        documents = scraper.perform_scrape("https://example.com/start")

        # No documents should be created as no rules matched for content extraction
        self.assertEqual(len(documents), 0)
        # But links should have been followed up to depth 1
        mock_get.assert_has_calls([
            call("https://example.com/start", timeout=10, headers=unittest.mock.ANY),
            call("https://example.com/page1", timeout=10, headers=unittest.mock.ANY),
            call("https://example.com/page2", timeout=10, headers=unittest.mock.ANY),
        ], any_order=True) # Order depends on queue pop
        self.assertEqual(mock_get.call_count, 3) # Forbidden not called


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

