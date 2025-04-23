import logging
import grpc
import json # Added for parsing JSON string in form data
from fastapi import FastAPI, HTTPException, Header, Depends, Form # Added Form
from pydantic import BaseModel, ValidationError, Field # Added Field for potential future use
from typing import Annotated

# Assuming rpc bindings are in the 'rpc' subdirectory relative to this file's location
# Adjust the import path if your structure is different
try:
    from rpc import controller_pb2
    from rpc import controller_pb2_grpc
    from rpc import common_pb2 # Added import for common types
except ImportError:
    # Handle case where script is run directly for testing, adjust path accordingly
    import sys
    import os
    # Add the parent directory (service_api) to the Python path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from rpc import controller_pb2
    from rpc import controller_pb2_grpc
    from rpc import common_pb2 # Added import for common types


from config import (
    CONTROLLER_ADDR, 
    GATEWAY_HTTP_PORT, 
    ANSWER_TIMEOUT, 
    PIPELINE_TIMEOUT
)

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- FastAPI App ---
app = FastAPI(title="Gateway Service", description="HTTP Gateway for Controller gRPC Service")

# --- Pydantic Models ---
class PromptRequest(BaseModel):
    prompt: str

class AnswerResponse(BaseModel):
    answer: str

class PipelineResponse(BaseModel):
    token: str

# --- Pydantic models for parsing rules from JSON string ---
# These help validate the structure of the JSON string passed in the form
class RegexModel(BaseModel):
    pattern: str

class RuleModel(BaseModel):
    url: RegexModel
    css_selector: str | None = None # Optional css_selector

class ScrapeRulesModel(BaseModel):
    max_depth: int | None = None
    max_pages: int | None = None
    scrape_patterns: list[RuleModel] = []
    forbidden_urls: list[RegexModel] = []

# --- gRPC Client Setup ---
def get_controller_stub():
    """Dependency to create and manage the gRPC stub."""
    try:
        channel = grpc.insecure_channel(CONTROLLER_ADDR)
        # You might want to add channel readiness checks in a production scenario
        stub = controller_pb2_grpc.ControllerStub(channel)
        yield stub
    except Exception as e:
        logger.error(f"Failed to create gRPC channel or stub: {e}")
        raise HTTPException(status_code=500, detail="Internal server error: Could not connect to backend service.")
    finally:
        if 'channel' in locals() and channel:
            channel.close()
            logger.info("gRPC channel closed.")

# --- API Endpoints ---
@app.post("/answer", response_model=AnswerResponse)
async def answer_prompt(
    request_body: PromptRequest,
    authorization: Annotated[str | None, Header()] = None,
    stub: controller_pb2_grpc.ControllerStub = Depends(get_controller_stub)
):
    """
    Receives a user prompt and forwards it to the controller service.
    Requires 'Authorization' header with the user token.
    """
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(status_code=401, detail="Authorization header is missing")

    # The header might contain "Bearer <token>", adjust if needed. Assuming it's just the token for now.
    token = authorization # If it's "Bearer <token>", use: token = authorization.split(" ")[1] if " " in authorization else None

    if not token:
         logger.warning("Invalid or empty token in Authorization header")
         raise HTTPException(status_code=401, detail="Invalid token format in Authorization header")

    logger.info(f"Received prompt request for token: {token[:5]}...") # Log partial token for security

    try:
        grpc_request = controller_pb2.AnswerPromptRequest(
            token=token,
            prompt=request_body.prompt
        )
        logger.info(f"Sending request to controller at {CONTROLLER_ADDR} with timeout of {ANSWER_TIMEOUT}s")
        grpc_response = stub.AnswerPrompt(grpc_request, timeout=ANSWER_TIMEOUT) # Increased timeout
        logger.info(f"Received response from controller for token: {token[:5]}...")
        return AnswerResponse(answer=grpc_response.answer)

    except grpc.RpcError as e:
        logger.error(f"gRPC error occurred for token {token[:5]}...: {e.details()} (Status: {e.code()})")
        status_code = 500 # Default internal server error
        detail = "Internal server error: Failed to process request via backend service."

        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            status_code = 401
            detail = "Unauthorized: Invalid token provided."
        elif e.code() == grpc.StatusCode.INVALID_ARGUMENT:
             status_code = 422 # Or 400 Bad Request
             detail = f"Invalid request: {e.details()}"
        elif e.code() == grpc.StatusCode.UNAVAILABLE:
             status_code = 503 # Service Unavailable
             detail = "Backend service is currently unavailable."
        elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
             status_code = 504 # Gateway Timeout
             detail = "Request timed out waiting for backend service."
        # Add more specific gRPC status code mappings as needed

        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as e:
        logger.exception(f"An unexpected error occurred for token {token[:5]}...: {e}") # Log full traceback
        raise HTTPException(status_code=500, detail="Internal server error.")


@app.post("/pipeline", response_model=PipelineResponse)
async def create_pipeline(
    user_name: Annotated[str, Form()],
    description: Annotated[str, Form()],
    language: Annotated[str, Form()],
    entry_docs_url: Annotated[str, Form()],
    rules_json: Annotated[str, Form(alias="rules")], # Expect 'rules' field to contain JSON string
    stub: controller_pb2_grpc.ControllerStub = Depends(get_controller_stub)
):
    """
    Creates a new RAG pipeline by forwarding the request to the controller service.
    Accepts application/x-www-form-urlencoded data.
    The 'rules' field must be a JSON string representing the ScrapeRules structure.
    """
    logger.info(f"Received create pipeline request for user: {user_name}")

    try:
        # Parse the JSON string for rules
        rules_data = json.loads(rules_json)
        # Validate the parsed JSON using the Pydantic model
        validated_rules = ScrapeRulesModel.model_validate(rules_data)

        # Construct the common_pb2.ScrapeRules object
        scrape_rules_proto = common_pb2.ScrapeRules()
        if validated_rules.max_depth is not None:
             scrape_rules_proto.max_depth = validated_rules.max_depth
        if validated_rules.max_pages is not None:
             scrape_rules_proto.max_pages = validated_rules.max_pages

        for rule_model in validated_rules.scrape_patterns:
            rule_proto = scrape_rules_proto.scrape_patterns.add()
            rule_proto.url.pattern = rule_model.url.pattern
            if rule_model.css_selector is not None:
                rule_proto.css_selector = rule_model.css_selector

        for regex_model in validated_rules.forbidden_urls:
             regex_proto = scrape_rules_proto.forbidden_urls.add()
             regex_proto.pattern = regex_model.pattern

        # Construct the gRPC request
        grpc_request = controller_pb2.CreatePipelineRequest(
            user_name=user_name,
            description=description,
            language=language,
            entry_docs_url=entry_docs_url,
            rules=scrape_rules_proto
        )

        logger.info(f"Sending CreatePipeline request to controller at {CONTROLLER_ADDR} with timeout of {PIPELINE_TIMEOUT}s")
        grpc_response = stub.CreatePipeline(grpc_request, timeout=PIPELINE_TIMEOUT) # Increased timeout for pipeline creation
        logger.info(f"Pipeline created successfully for user: {user_name}, Token: {grpc_response.token[:5]}...")
        return PipelineResponse(token=grpc_response.token)

    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON for 'rules' field for user {user_name}")
        raise HTTPException(status_code=422, detail="Invalid JSON format in 'rules' form field.")
    except ValidationError as e:
         logger.error(f"Invalid structure in 'rules' JSON for user {user_name}: {e}")
         raise HTTPException(status_code=422, detail=f"Invalid data in 'rules' field: {e}")
    except grpc.RpcError as e:
        logger.error(f"gRPC error during pipeline creation for user {user_name}: {e.details()} (Status: {e.code()})")
        status_code = 500
        detail = "Internal server error: Failed to create pipeline via backend service."
        if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
             status_code = 422
             detail = f"Invalid pipeline configuration: {e.details()}"
        elif e.code() == grpc.StatusCode.UNAVAILABLE:
             status_code = 503
             detail = "Backend service is currently unavailable."
        elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
             status_code = 504
             detail = "Request timed out waiting for backend service."
        # Add more specific gRPC status code mappings as needed
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as e:
        logger.exception(f"An unexpected error occurred during pipeline creation for user {user_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


# --- Run Server (for local development) ---
if __name__ == "__main__":
    import uvicorn
    import json
    import os

    # Define paths
    DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
    OPENAPI_FILE_PATH = os.path.join(DOCS_DIR, "openapi.json")

    # Ensure docs directory exists
    os.makedirs(DOCS_DIR, exist_ok=True)

    # Generate OpenAPI schema
    openapi_schema = app.openapi()

    # Save the schema to a file
    try:
        with open(OPENAPI_FILE_PATH, "w") as f:
            json.dump(openapi_schema, f, indent=2)
        logger.info(f"OpenAPI specification saved to {OPENAPI_FILE_PATH}")
    except IOError as e:
        logger.error(f"Failed to save OpenAPI specification to {OPENAPI_FILE_PATH}: {e}")

    logger.info("Starting Gateway Service...")
    # Create a .env file in the same directory with CONTROLLER_ADDR=host:port and GATEWAY_HTTP_PORT=port if needed
    logger.info(f"Gateway listening on http://0.0.0.0:{GATEWAY_HTTP_PORT}")
    logger.info(f"Attempting to connect to Controller gRPC service at: {CONTROLLER_ADDR}")
    # Ensure 'app' is the variable holding your FastAPI instance
    # Using reload=True might cause the schema generation to run multiple times,
    # consider disabling reload or using a separate script for schema generation in production.
    uvicorn.run("server:app", host="0.0.0.0", port=GATEWAY_HTTP_PORT) # Use string "server:app" for reload
