# ArtificialInsight Controller

The Controller acts as the central orchestration component of the ArtificialInsight system. It coordinates the interaction between different services (LLMs, Scraping, UserDB, and VectorDB) to provide Retrieval-Augmented Generation (RAG) capabilities.

## Core Functionality

The controller implements two primary methods:

### 1. CreatePipeline

Creates a new RAG pipeline by:
1. Saving user information to the database
2. Generating a unique access token
3. Scraping documentation from the provided URL
4. Storing the scraped documents in the vector database

### 2. AnswerPrompt

Processes user queries by:
1. Authenticating the user via the provided token
2. Retrieving relevant documents from the vector database
3. Sending the prompt and retrieved documents to the LLM service
4. Returning the generated answer to the user

## Method Call Sequences

### CreatePipeline Sequence

1. Receive `CreatePipelineRequest` with user info, description, language preference, entry URL, and scraping rules
2. Create new user in UserDB service (via `CreateUser` RPC)
3. Call Scraping service to obtain documents (via `Scrape` RPC)
4. Create new collection in VectorDB service (via `CreateCollection` RPC)
5. Return the generated token to the client in `CreatePipelineResponse`

### AnswerPrompt Sequence

1. Receive `AnswerPromptRequest` with user token and prompt
2. Validate user token with UserDB service (via `GetUser` RPC)
3. Increment user request count (via `UpdateUserRequestCount` RPC)
4. Search for relevant documents in VectorDB (via `Search` RPC)
5. Request answer generation from LLM service (via `GenerateAnswer` RPC)
6. Log the completed request
7. Return the generated answer to the client in `AnswerPromptResponse`

## Technical Stack

- **Language**: Python 3.8+
- **Framework**: gRPC
- **Dependencies**:
  - `grpcio` - For gRPC communication
  - `protobuf` - For protocol buffer serialization
  - `uuid` - For token generation

## Logging

All operations are logged for observability and debugging:
- Request timestamps and durations
- User tokens (anonymized where appropriate)
- Operation outcomes (success/failure)
- Standard Python logging is used

## Configuration

The controller can be configured via environment variables:
- Service endpoints for LLM, Scraping, UserDB, and VectorDB services
- Authentication settings
- Logging verbosity levels
- Service timeouts:
  - `DEFAULT_TIMEOUT` - Default timeout for service calls (30 seconds)
  - `SCRAPING_TIMEOUT` - Timeout for scraping operations (120 seconds)
  - `LLM_TIMEOUT` - Timeout for LLM operations (60 seconds)
  - `USERDB_TIMEOUT` - Timeout for UserDB operations (15 seconds)
  - `VECTORDB_TIMEOUT` - Timeout for VectorDB operations (45 seconds)

## gRPC Connection Management

The controller uses the following gRPC keepalive settings to maintain stable connections:

### Client Side (when connecting to other services)
- `grpc.keepalive_time_ms`: 60000 (60 seconds between pings)
- `grpc.keepalive_timeout_ms`: 20000 (20 seconds ping timeout)
- `grpc.keepalive_permit_without_calls`: False (only ping when there are active calls)

### Server Side (when accepting connections)
- `grpc.keepalive_permit_without_calls`: True (allow pings even without active calls)
- `grpc.http2.min_time_between_pings_ms`: 60000 (minimum 60 seconds between client pings)
- `grpc.http2.max_pings_without_data`: 2 (allow up to 2 pings without data)
- `grpc.http2.max_ping_strikes`: 3 (disconnect clients after 3 bad pings)

These settings prevent "ENHANCE_YOUR_CALM" (too many pings) errors while maintaining connection stability.

## Usage

The controller is designed to be deployed as a service that other gateway components can communicate with via gRPC.

For development and testing, you can run the controller locally:

```bash
python -m controller.server
```

## API Reference

The controller implements the gRPC service defined in `controller.proto`:
- `AnswerPrompt` - Process user queries using RAG
- `CreatePipeline` - Set up a new RAG pipeline

For detailed API specifications, refer to the protocol buffer definitions in the `proto/` directory.
