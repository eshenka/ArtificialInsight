# Vector Database Service

A high-performance vector database service built for semantic search and document retrieval. This service provides a gRPC interface for managing document collections and performing vector similarity searches.

## Overview

The Vector Database Service enables efficient storage and retrieval of document embeddings using Milvus as the underlying vector database. It provides functionality for creating collections, adding documents, performing semantic searches, and managing embedding models.

## Features

- **Document Management**: Create collections and add documents with automatic chunking
- **Semantic Search**: Find semantically similar documents based on vector embeddings
- **Multiple Embedding Models**: Support for various embedding models across different languages
- **Ollama Integration**: Use Ollama models for generating embeddings
- **Collection Management**: Create, delete, and get information about collections
- **Automatic Chunking**: Documents are automatically split into manageable chunks for optimal retrieval

## Architecture & Tech Stack

- **Backend**: Python
- **Vector Database**: [Milvus](https://milvus.io/)
- **Embedding Models**: 
  - [SentenceTransformers](https://www.sbert.net/) for text embedding generation
  - [Ollama](https://ollama.ai/) for local embedding model deployment
- **API**: gRPC for high-performance client-server communication
- **Protocol Buffers**: For data serialization and API definitions

## Prerequisites

- Python 3.8+
- Milvus 2.0+ running as a service
- gRPC tools
- SentenceTransformers library
- Ollama (optional, for local embedding models)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ArtificialInsight.git
cd ArtificialInsight
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or install the required packages manually:

```bash
pip install grpcio grpcio-tools pymilvus sentence-transformers numpy requests
```

### 3. Set up Milvus

You can run Milvus using Docker:

```bash
docker run -d --name milvus-standalone -p 19530:19530 -p 19121:19121 milvusdb/milvus:latest standalone
```

### 4. Set up Ollama (Optional)

If you want to use Ollama for embeddings:

```bash
docker run -d --name ollama -p 11434:11434 ollama/ollama:latest
```

## Configuration

The Vector Database Service can be configured through environment variables or command-line arguments:

- `MILVUS_HOST` (default: "localhost"): Milvus server host
- `MILVUS_PORT` (default: 19530): Milvus server port
- `GRPC_HOST` (default: "0.0.0.0"): Host to bind the gRPC server
- `GRPC_PORT` (default: 50051): Port to bind the gRPC server
- `OLLAMA_HOST`: URL of Ollama API server (e.g., "http://localhost:11434")
- `OLLAMA_MODELS`: Comma-separated list of Ollama model names to use for embeddings

Example OLLAMA_MODELS configuration:
```
OLLAMA_MODELS=nomic-embed-text,llama2,mistral
```

## Running the Service

Start the gRPC server with:

```bash
python main.py
```

You can specify custom host and port:

```bash
python main.py --host 0.0.0.0 --port 50051
```

With Ollama integration:

```bash
OLLAMA_HOST="http://localhost:11434" OLLAMA_MODELS="nomic-embed-text,llama2" python main.py
```

## API Reference

The service implements the `VectorDatabaseService` defined in `vectordb.proto`:

### CreateCollection

Creates a new collection and adds initial documents.

```protobuf
rpc CreateCollection(CreateCollectionRequest) returns (CreateCollectionResponse);
```

### AddDocuments

Adds documents to an existing collection.

```protobuf
rpc AddDocuments(AddDocumentsRequest) returns (AddDocumentsResponse);
```

### Search

Searches for relevant documents in a collection.

```protobuf
rpc Search(SearchRequest) returns (SearchResponse);
```

### DeleteCollection

Deletes an existing collection.

```protobuf
rpc DeleteCollection(DeleteCollectionRequest) returns (DeleteCollectionResponse);
```

### GetCollectionInfo

Gets information about an existing collection.

```protobuf
rpc GetCollectionInfo(GetCollectionInfoRequest) returns (GetCollectionInfoResponse);
```

### GetEmbeddingModels

Gets available embedding models, optionally filtered by language.

```protobuf
rpc GetEmbeddingModels(GetEmbeddingModelsRequest) returns (GetEmbeddingModelsResponse);
```

## Client Examples

### Python Client

```python
import grpc
import vectordb_pb2
import vectordb_pb2_grpc

# Connect to the server
channel = grpc.insecure_channel('localhost:50051')
stub = vectordb_pb2_grpc.VectorDatabaseServiceStub(channel)

# Create a collection
create_request = vectordb_pb2.CreateCollectionRequest(
    collection_name="my_company",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",  # Or "ollama/nomic-embed-text" for Ollama
    documents=[
        vectordb_pb2.Document(
            source="document1.txt",
            content="This is a sample document for vector database testing."
        )
    ]
)
stub.CreateCollection(create_request)

# Search in the collection
search_request = vectordb_pb2.SearchRequest(
    collection_name="my_company",
    query="How to test vector databases?",
    limit=5
)
search_response = stub.Search(search_request)

for doc in search_response.results:
    print(f"Source: {doc.source}")
    print(f"Score: {doc.score}")
    print(f"Content: {doc.content}")
    print("---")
```

## Data Architecture

For each company or client, the service creates:

1. A dedicated database named `company_{company_id}`
2. A collection named `documents` within that database
3. Document entries with fields:
   - `id`: Auto-generated primary key
   - `source`: Document source identifier
   - `content`: Document text content
   - `embedding`: Vector embedding of the content

## Embedding Models

The service supports multiple types of embedding models:

1. **SentenceTransformers Models** (default):
   - `sentence-transformers/all-MiniLM-L6-v2` (English)
   - `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (Russian)

2. **Ollama Models** (when configured):
   - Use `ollama/model-name` format to specify an Ollama model
   - Example: `ollama/nomic-embed-text` for English embeddings
   - Models configured in `OLLAMA_MODELS` will be automatically downloaded

3. **OpenAI Models**:
   - `OpenAI/text-embedding-ada-002` (requires API key)

## Performance Considerations

- The chunking mechanism splits large documents into smaller pieces for better retrieval
- Index parameters can be tuned for specific use cases in the `_create_collection_in_db` method
- Consider adjusting the number of worker threads based on your server's capabilities

## Troubleshooting

Common issues:

1. **Connection refused to Milvus**: Ensure Milvus is running and accessible
2. **Memory issues with large models**: Consider using smaller embedding models or increasing server memory
3. **Slow search performance**: Adjust index parameters or increase the number of server workers
4. **Ollama models not loading**: Check OLLAMA_HOST is correct and accessible, and that models are specified correctly

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
