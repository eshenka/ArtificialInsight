# ArtificialInsight

ArtificialInsight is a powerful platform for automatically creating Retrieval-Augmented Generation (RAG) pipelines by scraping documentation websites. Users can define scraping parameters and documentation URLs, and the system creates a complete RAG pipeline. The generated pipelines are accessible through a HTTP REST API, enabling users to answer client prompts using LLMs (Large Language Models) enhanced with relevant documents retrieved from a vector database.

## Services

### Gateway Service
Provides a RESTful API interface for users to interact with the underlying RAG system. It receives user prompts via HTTP, forwards them to the controller service using gRPC, and returns the generated answer back to the user.

### Web UI
A user-friendly interface that allows users to:
- Create RAG pipelines with an easy-to-use form
- Test generated pipelines through a chat interface
- Manage access tokens for previously created pipelines

### Controller
The central orchestration component that coordinates interactions between different services. It implements:
- `CreatePipeline`: Creates new RAG pipelines by coordinating scraping, user management, and vector storage
- `AnswerPrompt`: Processes user queries using the RAG methodology

### Scraping Service
Provides web scraping functionality based on user-defined rules:
- Recursively crawls documentation websites
- Extracts relevant content using CSS selectors
- Respects URL patterns and depth/page limits

### VectorDB Service
A high-performance vector database service built for semantic search:
- Stores document embeddings using Milvus
- Enables efficient retrieval of semantically similar documents
- Provides automatic document chunking for optimal retrieval

### UserDB Service
Manages user information and authentication:
- Creates and manages user records
- Handles token-based authentication
- Tracks usage statistics like request counts

### LLM Service
Provides access to various large language models:
- Supports multiple LLM providers
- Features automatic fallback to locally-hosted Ollama models
- Handles context-aware prompt generation

## Getting Started

### Prerequisites

- Docker and Docker Compose (for recommended installation)
- For manual installation:
  - Python 3.8+
  - Rust 1.67+ (for UserDB service)
  - Node.js (v16+) and npm/yarn (for Web UI)

### Installation

#### Option 1: Docker Compose (Recommended)

The fastest and simplest way to deploy ArtificialInsight is with Docker Compose:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ArtificialInsight.git
   cd ArtificialInsight
   ```

2. Create and configure the environment file:
   ```bash
   # Copy the example environment file to the docker directory
   cp .env.example docker/.env
   
   # Edit the .env file with your preferred settings
   # IMPORTANT: Set your LLM_KEY if using external LLM providers
   nano docker/.env  # or use your preferred text editor
   ```

3. Navigate to the docker directory and start all services:
   ```bash
   cd docker
   docker-compose up -d
   ```

4. Verify all services are running:
   ```bash
   docker-compose ps
   ```

5. Access the Web UI at http://localhost:5173

That's it! Your ArtificialInsight system is now ready to use.

#### Docker Compose Configuration

The Docker Compose deployment can be configured using environment variables in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| **Web UI Configuration** |
| `WEBUI_PORT` | Port to expose the Web UI | `5173` |
| `VITE_API_BASE_URL` | URL of the API Gateway | `http://localhost:8000` |
| **API Gateway Configuration** |
| `GATEWAY_HTTP_PORT` | Internal port for the gateway service | `8000` |
| `GATEWAY_EXPOSED_PORT` | External port for the gateway service | `8000` |
| **Controller Configuration** |
| `CONTROLLER_PORT` | Port for the controller service | `50050` |
| `CONTROLLER_MAX_WORKERS` | Maximum worker threads | `10` |
| **LLM Service Configuration** |
| `LLM_PORT` | Port for the LLM service | `50052` |
| `LLM_KEY` | API key for external LLM provider | ` ` (empty) |
| `USE_OLLAMA_FALLBACK` | Whether to use Ollama as fallback | `true` |
| **Scraping Service Configuration** |
| `SCRAPING_PORT` | Port for the scraping service | `50051` |
| `SCRAPING_TIMEOUT` | HTTP request timeout in seconds | `30` |
| `SCRAPING_MAX_WORKERS` | Maximum worker threads | `10` |
| `SCRAPING_USER_AGENT` | User agent for HTTP requests | `ArtificialInsightScraper/1.0` |
| **Vector Database Configuration** |
| `VECTORDB_PORT` | Port for the vector database service | `50051` |
| **User Database Configuration** |
| `USERDB_PORT` | Port for the user database service | `2780` |
| **PostgreSQL Configuration** |
| `POSTGRES_PASSWORD` | PostgreSQL password | `password` |
| `POSTGRES_USER` | PostgreSQL username | `postgres` |
| `POSTGRES_DB` | PostgreSQL database name | `aiusers` |
| **General Configuration** |
| `LOG_LEVEL` | Logging level for all services | `INFO` |

#### Docker Compose Commands

All docker-compose commands should be run from the `docker` directory:

- **Start all services:**
  ```bash
  cd docker
  docker-compose up -d
  ```

- **Stop all services:**
  ```bash
  cd docker
  docker-compose down
  ```

- **View logs from all services:**
  ```bash
  cd docker
  docker-compose logs -f
  ```

- **View logs from a specific service:**
  ```bash
  cd docker
  docker-compose logs -f service_name  # e.g., docker-compose logs -f controller
  ```

- **Rebuild and update services after code changes:**
  ```bash
  cd docker
  docker-compose up -d --build
  ```

#### Option 2: Manual Installation

For development or advanced users who prefer more control, you can install and run each component separately:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ArtificialInsight.git
   cd ArtificialInsight
   ```

2. Set up environment variables (or use defaults):
   ```bash
   # Example configuration
   export MILVUS_HOST=localhost
   export MILVUS_PORT=19530
   export USERDB_PG_URL=postgres://username:password@localhost/userdb
   export LLM_KEY=your_api_key_here
   ```

3. Start required services:
   ```bash
   # Start Milvus for VectorDB
   docker run -d --name milvus-standalone -p 19530:19530 -p 19121:19121 milvusdb/milvus:latest standalone
   
   # Start PostgreSQL for UserDB
   docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=password postgres
   ```

4. Start each service (from their respective directories):
   ```bash
   # UserDB service
   cd userdb
   cargo run --release
   
   # VectorDB service
   cd ../vectorDB
   python main.py
   
   # LLM service
   cd ../llms
   python main.py
   
   # Scraping service
   cd ../scraping
   python server.py
   
   # Controller service
   cd ../controller
   python -m controller.server
   
   # Gateway service
   cd ../service_api
   python main.py
   
   # Web UI
   cd ../webui
   npm install
   npm run dev
   ```

### Usage

#### Using the Web UI

1. Access the Web UI at http://localhost:5173
2. Fill out the Pipeline Creation form with:
   - User information
   - Pipeline description
   - Documentation URL
   - Scraping configuration
3. Submit the form to create your RAG pipeline
4. Use the returned token in the Chat Testing interface to interact with your pipeline

#### Using the REST API

1. Create a new pipeline:
   ```bash
   curl -X POST http://localhost:8000/pipeline \
     -d "user_name=example_user" \
     -d "description=My documentation helper" \
     -d "language=en" \
     -d "entry_docs_url=https://docs.example.com" \
     -d "rules={\"max_depth\":3,\"max_pages\":50,\"scrape_patterns\":[{\"url\":{\"pattern\":\"https://docs\\.example\\.com/.*\"},\"css_selector\":\"main\"}],\"forbidden_urls\":[{\"pattern\":\".*login.*\"}]}"
   ```

2. Use the returned token to ask questions:
   ```bash
   curl -X POST http://localhost:8000/answer \
     -H "Authorization: your_token_here" \
     -H "Content-Type: application/json" \
     -d '{"prompt":"How do I implement feature X?"}'
   ```

## Configuration Options

Each service can be configured through environment variables or command-line arguments. 

### Important Configuration Options:

| Service    | Variable        | Description                               | Default           |
|------------|----------------|-------------------------------------------|-------------------|
| All        | `LOG_LEVEL`    | Logging verbosity (DEBUG, INFO, WARNING)  | `INFO`            |
| UserDB     | `USERDB_PG_URL`| PostgreSQL connection string              | See documentation |
| LLM        | `LLM_KEY`      | API key for external LLM provider         | None              |
| LLM        | `OLLAMA_HOST`  | Host for local Ollama instance            | `http://localhost:11434` |
| VectorDB   | `MILVUS_HOST`  | Milvus server host                        | `localhost`       |
| VectorDB   | `MILVUS_PORT`  | Milvus server port                        | `19530`           |
| Gateway    | `CONTROLLER_HOST` | Host for controller service            | `localhost`       |
| Gateway    | `CONTROLLER_PORT` | Port for controller service            | `50050`           |

See individual service README files for specific configuration options.

## Development

### Protocol Buffers

The services communicate using gRPC, with interfaces defined in Protocol Buffer files:

- `proto/common.proto`: Common message definitions
- `proto/controller.proto`: Controller service definition
- `proto/llms.proto`: LLM service definition
- `proto/scraping.proto`: Scraping service definition
- `proto/vectordb.proto`: VectorDB service definition
- `proto/userdb.proto`: UserDB service definition

After modifying these files, regenerate the client/server code for the respective languages:

For Python services:
```bash
python -m grpc_tools.protoc -I./proto --python_out=./service_name --pyi_out=./service_name --grpc_python_out=./service_name ./proto/*.proto
```

For Rust services:
```bash
cd userdb
cargo build
```

### Local Development

For local development, you can run individual services in development mode while keeping others in Docker:

1. Start the infrastructure and services you don't want to modify:
   ```bash
   docker-compose up -d milvus postgres llm_service
   ```

2. Run the service you're working on locally:
   ```bash
   cd service_directory
   python main.py  # Or the appropriate start command
   ```

### Testing

Each service has its own test suite. Refer to the individual service READMEs for testing instructions.

### Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Common Issues

1. **Connection refused errors**: Ensure all dependent services are running and accessible
2. **Authentication errors**: Check that your LLM API keys are properly configured
3. **Missing dependencies**: Make sure you've installed all required dependencies
4. **Port conflicts**: Check if the required ports are already in use by other applications

### Getting Help

If you encounter issues:
1. Check the logs of the relevant services
2. Refer to the individual service READMEs
3. Open an issue on the GitHub repository

## License

This project is licensed under the MIT License - see the LICENSE file for details.