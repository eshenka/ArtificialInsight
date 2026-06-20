# Scraping Service

This service provides a gRPC endpoint for web scraping based on defined rules.

## Technology Stack

*   **Python 3:** Core programming language.
*   **gRPC:** Framework for the RPC communication.
    *   `grpcio`: Python library for gRPC.
    *   `grpcio-tools`: Used to generate Python code from `.proto` files.
*   **Protocol Buffers:** Interface definition language used by gRPC.
*   **Web Scraping Libraries** Web Scraping Libraries:
    *   `requests`: For fetching web page content.
    *   `beautifulsoup4` or `lxml`: For parsing HTML and extracting data using CSS selectors.
    *   `re`: For matching URL patterns.

## Proto Definitions

The service interface and message structures are defined in:

*   `proto/scraping.proto`: Defines the `ScrapingService`, `ScrapeRequest`, `ScrapeResponse`, and associated rule messages.
*   `proto/common.proto`: Defines the `Document` message structure used in the response.

## Generating gRPC Code

If you modify the `.proto` files, you need to regenerate the Python gRPC code. Navigate to the project directory and run:

```bash
python -m grpc_tools.protoc -I./proto --python_out=./scraping/rpc --pyi_out=./scraping/rpc --grpc_python_out=./scraping/rpc ./proto/scraping.proto ./proto/common.proto
```

This will generate/update `scraping_pb2.py`, `scraping_pb2.pyi`, `scraping_pb2_grpc.py`, and the corresponding files for `common.proto` inside the `scraping` directory.

## Running the Server

1.  Navigate to the `scraping` directory:
    ```bash
    cd scraping
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  (Optional) Set the server port using an environment variable (defaults to 50051):
    ```bash
    # Example for Linux/macOS
    export SCRAPING_PORT=50052
    # Example for Windows CMD
    set SCRAPING_PORT=50052
    # Example for Windows PowerShell
    $env:SCRAPING_PORT="50052"
    ```
4.  Run the server:
    ```bash
    python server.py
    ```

The server will start listening on the configured port (default `50051`).

## Running the Client

A basic client script (`client.py`) is provided to test the service.

1.  Ensure the server is running (see "Running the Server").
2.  Ensure dependencies are installed (see step 2 in "Running the Server").
3.  Navigate to the `scraping` directory:
    ```bash
    cd scraping
    ```
4.  Run the client, providing the entry URL:
    ```bash
    # Basic usage
    python tests/client.py <your_entry_url>

    # Example with options
    python client.py https://example.com --max-pages 20 --max-depth 5 --port 50051
    ```

**Client Options:**

*   `entry` (Required): The starting URL.
*   `--max-pages` (Optional): Maximum pages to visit (default: 10).
*   `--max-depth` (Optional): Maximum recursion depth (default: 3).
*   `--port` (Optional): Server port to connect to (defaults to `50051` or the `SCRAPING_PORT` environment variable if set).

The client will print the source URL and a preview of the content for each scraped document, along with the time taken for the gRPC call.

## Running Tests

Unit tests are located in the `tests/` directory and use Python's built-in `unittest` framework.

1.  Ensure dependencies are installed:
    ```bash
    pip install -r requirements.txt
    ```
2.  Navigate to the `scraping` directory:
    ```bash
    cd scraping
    ```
3.  Run the tests:
    ```bash
    python -m unittest discover -s tests -p "test_*.py"
    ```
    Alternatively, run a specific test file:
    ```bash
    python -m unittest tests/test_scraper.py
    ```

## Service Methods

### `Scrape`

*   **Request:** `ScrapeRequest`
    *   `entry` (string): The starting URL for scraping.
    *   `rules` (`ScrapeRules`): Defines the scraping parameters:
        *   `max_depth` (uint32): Maximum recursion depth (optional).
        *   `max_pages` (uint32): Maximum number of pages to visit (optional).
        *   `scrape_patterns` (repeated `Rule`): List of rules defining which URLs to scrape and how.
            *   `url` (`Regex`): A regex pattern to match URLs to scrape.
            *   `css_selector` (string): The CSS selector to extract content from (defaults to `main` if empty).
        *   `forbidden_urls` (repeated `Regex`): List of regex patterns for URLs to avoid visiting.
*   **Response:** `ScrapeResponse`
    *   `documents` (repeated `common.Document`): A list of documents extracted during the scraping process. Each document likely contains the URL, extracted content, and potentially metadata.