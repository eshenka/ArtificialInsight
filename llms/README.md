# LLM Service

A gRPC service that provides access to various large language models (LLMs) with an automatic fallback mechanism to locally-hosted Ollama models.

## Features

- Access multiple language models through a unified API
- Automatic fallback to locally hosted Ollama models when cloud providers fail
- Context-aware prompt generation
- Support for multiple languages
- Configurable through environment variables

## Technology Stack

- **Python 3.8+**
- **gRPC** for service definition and communication
- **Protocol Buffers** for data serialization
- **Ollama** for local model hosting
- **Tenacity** for retry mechanisms
- **Requests** for API communication

## API Definition

The service implements the `LLMService` defined in `proto/llms.proto`, which provides two main methods:

1. **GenerateAnswer**: Generates responses to user questions with provided context
2. **GetAvailableModels**: Returns a list of available language models with filtering by language

## Configuration

The service can be configured through the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_KEY` | API key for the LLM provider | None |
| `OLLAMA_HOST` | URL for the Ollama service | `http://localhost:11434` |
| `USE_OLLAMA_FALLBACK` | Whether to use Ollama as a fallback | `true` |

Additional provider-specific API keys can be added as needed in the `LLMService` class.

## Prerequisites

1. Python 3.8 or higher
2. [Ollama](https://ollama.ai/) for local model execution
3. API keys for any cloud LLM providers you want to use

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ArtificialInsight
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Generate gRPC code (if making changes to the proto files):
   ```bash
   python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/llms.proto ./proto/common.proto
   ```

## Running the Service

Start the service with:

```bash
cd llms
python main.py
```

By default, the service will run on `0.0.0.0:50052`.

## Usage Examples

### Using with gRPC client

```python
import grpc
import llms_pb2
import llms_pb2_grpc

# Create a channel and stub
channel = grpc.insecure_channel('localhost:50052')
stub = llms_pb2_grpc.LLMServiceStub(channel)

# Get available models
request = llms_pb2.GetAvailableModelsRequest(language="en")
response = stub.GetAvailableModels(request)
print("Available models:", [model.name for model in response.models])

# Generate an answer
context = llms_pb2.Context(
    info="This is some background information.",
    documents=[
        common_pb2.Document(
            source="Knowledge base",
            content="This is relevant information for the question."
        )
    ]
)

request = llms_pb2.GenerateAnswerRequest(
    model_name="ollama/llama2",
    question="What is machine learning?",
    context=context
)

response = stub.GenerateAnswer(request)
print("Answer:", response.answer)
```

## Architecture

The LLM service follows a simple architecture:

1. **gRPC Server**: Handles incoming requests
2. **LLM Service**: Core service implementation
3. **Provider APIs**: Connections to various LLM providers
4. **Ollama Fallback**: Local fallback mechanism

The service tries to use the requested model first, falling back to Ollama if:
- The requested model is not found
- API keys are missing
- The API call fails

## Extending with New Models

To add support for a new model:

1. Add the model configuration to the `models` dictionary in `LLMService.__init__`
2. Implement the API call in a new `_call_<provider>_api` method
3. Update the `_call_model_api` method to use the new provider

## License

[MIT License](LICENSE)
