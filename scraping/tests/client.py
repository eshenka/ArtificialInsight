import grpc
import argparse
import time
import logging
import re
import os

import sys
sys.path.append('../rpc')

import common_pb2
import scraping_pb2
import scraping_pb2_grpc

# Configure logging for the client
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run(entry_url, max_pages, max_depth, port):
    """Connects to the server, sends a scrape request, and prints the response."""
    server_address = f'localhost:{port}'
    logging.info(f"Connecting to server at {server_address}...")

    try:
        # Create a channel and stub
        with grpc.insecure_channel(server_address) as channel:
            stub = scraping_pb2_grpc.ScrapingServiceStub(channel)

            # Construct the request
            # Regex to match any URL starting with the entry URL
            # Ensure entry_url doesn't end with / before adding .* if needed
            # Use re.escape to handle special characters in the entry URL
            pattern_str = f"^{re.escape(entry_url)}.*"
            logging.info(f"Using scrape pattern: {pattern_str}")

            request = scraping_pb2.ScrapeRequest(
                entry=entry_url,
                rules=scraping_pb2.ScrapeRules(
                    max_depth=max_depth,
                    max_pages=max_pages,
                    scrape_patterns=[
                        scraping_pb2.Rule(
                            url=scraping_pb2.Regex(pattern=pattern_str),
                            # css_selector left empty to use server default ('main')
                        )
                    ],
                    forbidden_urls=[] # No forbidden URLs for this client
                )
            )

            logging.info(f"Sending Scrape request: entry='{entry_url}', max_depth={max_depth}, max_pages={max_pages}")

            # Make the RPC call and measure time
            start_time = time.perf_counter()
            response = stub.Scrape(request, timeout=300) 
            end_time = time.perf_counter()

            duration = end_time - start_time
            logging.info(f"gRPC call finished in {duration:.4f} seconds.")

            # Process the response
            print("\n--- Scraped Documents ---")
            if response.documents:
                for i, doc in enumerate(response.documents):
                    print(f"\nDocument {i+1}:")
                    print(f"  Source: {doc.source}")
                    print(f"  Content Preview (first 1000 chars):")
                    preview_content = doc.content[:1000].replace('\n', '\n  ') 
                    print(f"  {preview_content}...")
            else:
                print("No documents were returned.")

            print("\n--- End of Documents ---")

    except grpc.RpcError as e:
        status_code = e.code()
        logging.error(f"gRPC call failed with status {status_code}: {e.details()}")
        if status_code == grpc.StatusCode.UNAVAILABLE:
            print(f"\nError: Could not connect to the server at {server_address}. Please ensure the server is running.")
        elif status_code == grpc.StatusCode.DEADLINE_EXCEEDED:
            print(f"\nError: The request timed out while waiting for the server at {server_address}.")
        elif status_code == grpc.StatusCode.INVALID_ARGUMENT:
             print(f"\nError: Invalid argument provided to the server: {e.details()}")
        else:
            # Generic gRPC error
            print(f"\nError communicating with the server: {status_code} - {e.details()}")
    except Exception as e:
        # Catch other unexpected errors
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"\nAn unexpected error occurred: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='gRPC client for the Scraping Service.')
    parser.add_argument('entry', type=str, help='The starting URL for scraping.')
    parser.add_argument('--max-pages', type=int, default=10, help='Maximum number of pages to visit (default: 10).')
    parser.add_argument('--max-depth', type=int, default=3, help='Maximum recursion depth (default: 3).')
    parser.add_argument('--port', type=str, default=os.environ.get('SCRAPING_PORT', '50051'),
                        help='The server port to connect to (default: 50051 or SCRAPING_PORT env var).')

    args = parser.parse_args()

    run(args.entry, args.max_pages, args.max_depth, args.port)
