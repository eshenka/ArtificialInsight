import grpc
from concurrent import futures
import time
import logging
import re
from urllib.parse import urljoin, urlparse
from collections import deque
import os

import requests
from bs4 import BeautifulSoup, ParserRejectedMarkup

import sys
sys.path.append('./rpc')

import common_pb2
import scraping_pb2
import scraping_pb2_grpc

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ScraperError(Exception):
    """Base class for scraper exceptions."""
    pass

class InvalidRegexError(ScraperError):
    """Raised for invalid regex patterns."""
    pass

class FetchError(ScraperError):
    """Raised when fetching a URL fails."""
    pass

class ParseError(ScraperError):
    """Raised when HTML parsing fails."""
    pass


class Scraper:
    """Encapsulates the web scraping logic."""

    def __init__(self, rules):
        self.rules = rules
        self.forbidden_patterns = []
        self.scrape_rules_config = []
        self._compile_rules()
        # Handle 0 values as no limit
        self.max_depth = self.rules.max_depth if self.rules.max_depth > 0 else float('inf')
        self.max_pages = self.rules.max_pages if self.rules.max_pages > 0 else float('inf')

    def _compile_rules(self):
        """   Compiles regex patterns from the rules."""
        try:
            self.forbidden_patterns = [re.compile(r.pattern) for r in self.rules.forbidden_urls]
            self.scrape_rules_config = []
            for rule in self.rules.scrape_patterns:
                self.scrape_rules_config.append({
                    'pattern': re.compile(rule.url.pattern),
                    'selector': rule.css_selector if rule.css_selector else 'main' 
                })
        except re.error as e:
            logging.error(f"Invalid regex pattern provided: {e}")
            raise InvalidRegexError(f"Invalid regex pattern: {e}") from e

    def _fetch_page(self, url):
        """Fetches content for a given URL."""
        try:
            response = requests.get(url, timeout=10, headers={'User-Agent': 'ArtificialInsightScraper/1.0'})
            response.raise_for_status()
            response.encoding = response.apparent_encoding if response.apparent_encoding else 'utf-8'
            content_type = response.headers.get('content-type', '').lower()
            if 'html' not in content_type:
                logging.info(f"Skipping non-HTML content at {url} ({content_type})")
                return None, None # 
            return response.content, response.encoding
        except requests.exceptions.Timeout:
            logging.warning(f"Timeout fetching {url}")
            raise FetchError(f"Timeout fetching {url}")
        except requests.exceptions.RequestException as e:
            logging.warning(f"Failed to fetch {url}: {e}")
            raise FetchError(f"Failed to fetch {url}: {e}") from e

    def _parse_html(self, html_bytes, encoding, url):
        """Parses HTML content using BeautifulSoup."""
        try:
            return BeautifulSoup(html_bytes, 'html.parser', from_encoding=encoding)
        except ParserRejectedMarkup as e: 
             logging.error(f"Markup rejection error parsing HTML for {url}: {e}", exc_info=True)
             raise ParseError(f"Markup rejection error parsing {url}: {e}") from e
        except Exception as e:
            logging.error(f"Error parsing HTML for {url}: {e}", exc_info=True)
            raise ParseError(f"Error parsing {url}: {e}") from e

    def _extract_content(self, soup, rule, url):
        """Extracts content based on the CSS selector."""
        selector = rule['selector']
        target_element = soup.select_one(selector)

        if not target_element:
            logging.warning(f"CSS selector '{selector}' not found at {url}. Falling back to 'body'.")
            selector = 'body'
            target_element = soup.select_one(selector)

        if target_element:
            page_text = target_element.get_text(separator='\n', strip=True)
            if page_text:
                logging.debug(f"Extracted content from {url} using selector '{selector}', length {len(page_text)}")
                return page_text
            else:
                logging.warning(f"No text content found with selector '{selector}' at {url}")
                return None
        else:
            logging.warning(f"Could not find primary selector ('{rule['selector']}') or fallback 'body' selector at {url}")
            return None

    def _find_links(self, soup, current_url, current_depth):
        """Finds and yields valid follow-up links."""
        if soup is None:
            logging.warning(f"Soup object is None before link finding for {current_url}, skipping link extraction.")
            return

        for link in soup.find_all('a', href=True):
            try:
                href = link['href']
                next_url = urljoin(current_url, href)
                parsed_url = urlparse(next_url)
                next_url = parsed_url._replace(fragment="").geturl()

                if parsed_url.scheme in ['http', 'https']:
                    is_forbidden = any(fp.match(next_url) for fp in self.forbidden_patterns)
                    if not is_forbidden:
                        should_follow = False
                        if not self.scrape_rules_config:
                            should_follow = True
                        elif any(sr['pattern'].match(next_url) for sr in self.scrape_rules_config):
                            should_follow = True

                        if should_follow:
                            yield next_url # Yield potential link to follow
            except Exception as e:
                 logging.error(f"Error processing link '{link.get('href', '')}' on page {current_url}: {e}", exc_info=False)
                 # Continue processing other links

    def perform_scrape(self, entry_url):
        """Performs the scraping process starting from the entry_url."""
        documents = []
        queue = deque([(entry_url, 0)])  # (url, depth)
        visited = {entry_url}
        page_count = 0

        while queue and page_count < self.max_pages:
            current_url, current_depth = queue.popleft()
            logging.info(f"Processing: {current_url} (Depth: {current_depth}, Pages Visited: {page_count})")

            try:
                # 1. Check depth limit
                if current_depth > self.max_depth:
                    logging.debug(f"Max depth ({self.max_depth}) reached for {current_url}")
                    continue

                # 2. Check forbidden URLs (already checked during link finding, but double-check)
                if any(pattern.match(current_url) for pattern in self.forbidden_patterns):
                    logging.info(f"Skipping forbidden URL: {current_url}")
                    continue

                page_count += 1

                # 3. Fetch page content
                try:
                    html_bytes, encoding = self._fetch_page(current_url)
                    if html_bytes is None: # Non-HTML content
                        continue
                except FetchError as e:
                    logging.warning(str(e))
                    continue # Skip this URL if fetching fails

                # 4. Parse HTML
                try:
                    soup = self._parse_html(html_bytes, encoding, current_url)
                except ParseError as e:
                    logging.error(str(e))
                    continue # Skip this URL if parsing fails

                # 5. Check if URL matches any scrape rule for content extraction
                matched_rule = None
                for rule_config in self.scrape_rules_config:
                    if rule_config['pattern'].match(current_url):
                        matched_rule = rule_config
                        break

                # 6. Extract content if rule matched
                if matched_rule:
                    try:
                        page_text = self._extract_content(soup, matched_rule, current_url)
                        if page_text:
                            doc = common_pb2.Document(
                                source=current_url,
                                content=page_text
                            )
                            documents.append(doc)
                    except Exception as extract_error:
                         logging.error(f"Error extracting content for {current_url}: {extract_error}", exc_info=True)
                         # Continue to link finding

                # 7. Find and enqueue links if depth allows further recursion
                if current_depth < self.max_depth:
                    try:
                        for next_url in self._find_links(soup, current_url, current_depth):
                             if next_url not in visited:
                                visited.add(next_url)
                                queue.append((next_url, current_depth + 1))
                                logging.debug(f"Enqueued: {next_url} (Depth: {current_depth + 1})")
                    except Exception as link_error:
                        logging.error(f"Error during link processing for {current_url}: {link_error}", exc_info=True)
                        # Continue loop even if link finding fails for the page

            except Exception as inner_loop_error:
                logging.error(f"Unexpected error processing URL {current_url}: {inner_loop_error}", exc_info=True)
                continue # Continue to the next URL in the queue

        logging.info(f"Scraping finished. Visited {page_count} pages. Found {len(documents)} documents.")
        return documents


class ScrapingServiceServicer(scraping_pb2_grpc.ScrapingServiceServicer):
    """Provides methods that implement functionality of scraping service."""

    def Scrape(self, request, context):
        """
        Handles the Scrape RPC call using the Scraper class.
        """
        logging.info(f"Received Scrape request for entry: {request.entry}")
        logging.info(f"Rules: max_depth={request.rules.max_depth}, max_pages={request.rules.max_pages}, "
                     f"scrape_patterns={len(request.rules.scrape_patterns)}, forbidden_urls={len(request.rules.forbidden_urls)}")

        try:
            scraper = Scraper(request.rules)
            documents = scraper.perform_scrape(request.entry)
            return scraping_pb2.ScrapeResponse(documents=documents)

        except InvalidRegexError as e:
            logging.error(f"Invalid regex in request: {e}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return scraping_pb2.ScrapeResponse()
        except Exception as e:
            logging.error(f"Unexpected error during scraping process: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal scraping error: {e}")
            return scraping_pb2.ScrapeResponse() # Return empty on internal errors


def serve():
    """Starts the gRPC server."""
    port = os.environ.get('SCRAPING_PORT', '50051')
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    try:
        scraping_pb2_grpc.add_ScrapingServiceServicer_to_server(ScrapingServiceServicer(), server)
    except AttributeError:
         logging.error("Failed to add Servicer. Ensure scraping_pb2_grpc.py is generated correctly.")
         logging.error("Run: python -m grpc_tools.protoc -I../proto --python_out=rpc --pyi_out=rpc --grpc_python_out=rpc ./proto/scraping.proto ./proto/common.proto")
         return 

    server.add_insecure_port('[::]:' + port)
    logging.info(f"Server starting on port {port}...")
    server.start()
    logging.info("Server started.")
    try:
        while True:
            time.sleep(86400)  # Keep the server running
    except KeyboardInterrupt:
        logging.info("Server stopping...")
        server.stop(0)
        logging.info("Server stopped.")

if __name__ == '__main__':
    serve()
