import grpc
import concurrent.futures
from grpc import StatusCode
import time
import logging
import os
from typing import List, Dict, Any, Optional

import llms_pb2
import llms_pb2_grpc

import requests
import json
from tenacity import retry, stop_after_attempt, wait_exponential

# Replace Ollama with OpenAI client for LLM7
import openai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService(llms_pb2_grpc.LLMServiceServicer):
    def __init__(self, llm7_base_url="https://api.llm7.io/v1"):
        """Initialize the LLM service with available models and API configurations."""
        # Configure API keys
        self.api_keys = {
            "llm7": os.environ.get("LLM7_API_KEY", "unused"),  # LLM7 uses "unused" as default
        }
        
        # LLM7 configuration
        self.llm7_base_url = llm7_base_url
        
        try:
            # Initialize OpenAI client for LLM7
            self.llm7_client = openai.OpenAI(
                base_url=self.llm7_base_url,
                api_key=self.api_keys["llm7"]
            )
            
            # Define available LLM7 models
            self.llm7_models = {
                "gpt-4.1-nano": {
                    "context_length": 128000,
                },
                "gpt-4.1-mini": {
                    "context_length": 128000,
                }
            }
            
            # Initialize models dictionary
            self.models = {}
            
            # Add LLM7 models to the models dictionary
            for model_name, model_info in self.llm7_models.items():
                model_id = f"llm7/{model_name}"
                self.models[model_id] = {
                    "provider": "llm7",
                    "language": "en", 
                    "max_context_length": model_info["context_length"],
                }
                
                # Also add models without prefix for backward compatibility
                self.models[model_name] = {
                    "provider": "llm7",
                    "language": "en", 
                    "max_context_length": model_info["context_length"],
                }
            
            logger.info(f"LLM7 service initialized with models: {', '.join(self.llm7_models.keys())}")
        except Exception as e:
            logger.error(f"Error initializing LLM7 service: {e}")
            # Add fallback models in case of initialization error
            self.models = {
                "llm7/gpt-4.1-nano": {
                    "provider": "llm7",
                    "language": "en",
                    "max_context_length": 128000,
                },
                "gpt-4.1-nano": {
                    "provider": "llm7",
                    "language": "en",
                    "max_context_length": 128000,
                }
            }
            logger.warning("Using fallback model configuration due to initialization error")
    
    def _create_prompt(self, question: str, context: llms_pb2.Context) -> str:
        """Create a prompt combining the context and the question."""
        general_info = context.info.strip() if context.info else ""
        
        document_contexts = []
        for doc in context.documents:
            document_contexts.append(f"Source: {doc.source}\nContent: {doc.content}")
        
        document_text = "\n\n".join(document_contexts)
        
        if document_text and general_info:
            prompt = f"Based on the following information and documents, please answer this question: \n\n{question}\n\nGeneral Information:\n{general_info}\n\nRelevant Documents:\n{document_text}"
        elif document_text:
            prompt = f"Based on the following documents, please answer this question: \n\n{question}\n\nRelevant Documents:\n{document_text}"
        elif general_info:
            prompt = f"Based on the following information, please answer this question: \n\n{question}\n\nGeneral Information:\n{general_info}"
        else:
            prompt = question
        
        return prompt
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_llm7_api(self, model_name: str, prompt: str) -> str:
        """Call the LLM7 API using the OpenAI client."""
        # Extract the actual model name if it has a provider prefix
        actual_model_name = model_name.split("/", 1)[1] if "/" in model_name else model_name
        
        try:
            response = self.llm7_client.chat.completions.create(
                model=actual_model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM7 API error: {e}")
            raise
    
    def _call_model_api(self, model_name: str, prompt: str) -> str:
        """Call the appropriate API based on the model name."""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        
        provider = self.models[model_name]["provider"]
        
        if provider == "llm7":
            return self._call_llm7_api(model_name, prompt)
        else:
            raise ValueError(f"Provider {provider} not supported")
    
    def _try_with_fallback(self, model_name: str, prompt: str) -> tuple[str, bool]:
        """
        Try to call the specified model, falling back to default model if needed.
        Returns the answer and whether a fallback was used.
        """
        try:
            # If the model doesn't exist directly, try with llm7/ prefix
            if model_name not in self.models and "/" not in model_name:
                prefixed_name = f"llm7/{model_name}"
                if prefixed_name in self.models:
                    model_name = prefixed_name
                    
            return self._call_model_api(model_name, prompt), False
        except Exception as e:
            logger.warning(f"Error with model {model_name}: {e}")
            
            # Use default model as fallback
            fallback_model = "llm7/gpt-4.1-nano"
            try:
                logger.info(f"Trying fallback with default model: gpt-4.1-nano")
                return self._call_llm7_api(fallback_model, prompt), True
            except Exception as err:
                logger.error(f"Fallback failed: {err}")
                raise
    
    def GenerateAnswer(self, request, context):
        """Generate an answer for the given question using the provided context."""
        model_name = request.model_name
        question = request.question
        user_context = request.context
        
        try:
            # Handle case when model doesn't exist
            if model_name not in self.models:
                # Try with llm7/ prefix
                prefixed_name = f"llm7/{model_name}"
                if prefixed_name in self.models:
                    model_name = prefixed_name
                else:
                    # Use default model
                    model_name = "llm7/gpt-4.1-nano"
                    logger.info(f"Model {request.model_name} not found, using default model: {model_name}")
            
            prompt = self._create_prompt(question, user_context)
            logger.info(f"Generating response for prompt: {prompt[:100]}...")
            
            answer, used_fallback = self._try_with_fallback(model_name, prompt)
            
            log_message = f"Generated answer for question: {question[:50]}..."
            if used_fallback:
                log_message += " (used fallback model)"
            logger.info(log_message)
            
            return llms_pb2.GenerateAnswerResponse(answer=answer)
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            context.abort(StatusCode.INTERNAL, f"Failed to generate answer: {str(e)}")
    
    def GetAvailableModels(self, request, context):
        """Get a list of available LLM models, optionally filtered by language."""
        language = request.language
        
        try:
            models_list = []
            logger.info(f"Getting available models for language: {language or 'any'}, models dict has {len(self.models)} entries")
            
            for name, config in self.models.items():
                # Only include models for the requested language if specified
                if language and config["language"] != language:
                    continue
                
                model = llms_pb2.Model(
                    name=name,
                    provider=config["provider"],
                    language=config["language"]
                )
                models_list.append(model)
            
            # If no models are found for the requested language, add a default model
            if not models_list:
                logger.warning(f"No models found for language: {language}. Adding default model.")
                default_model = llms_pb2.Model(
                    name="llm7/gpt-4.1-nano",
                    provider="llm7",
                    language="en"
                )
                models_list.append(default_model)
                logger.info(f"Added default model: {default_model.name}")
            
            logger.info(f"Returning {len(models_list)} available models")
            return llms_pb2.GetAvailableModelsResponse(models=models_list)
            
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            # Return at least one default model in case of error
            default_model = llms_pb2.Model(
                name="llm7/gpt-4.1-nano",
                provider="llm7",
                language="en"
            )
            logger.info(f"Returning fallback model due to error: {default_model.name}")
            return llms_pb2.GetAvailableModelsResponse(models=[default_model])


def serve(host="0.0.0.0", port=50054, llm7_base_url="https://api.llm7.io/v1"):
    """Start the gRPC server."""
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    llms_pb2_grpc.add_LLMServiceServicer_to_server(
        LLMService(llm7_base_url=llm7_base_url), server
    )
    server.add_insecure_port(f"{host}:{port}")
    server.start()
    logger.info(f"LLM service started on {host}:{port}")
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
        logger.info("Server stopped")


if __name__ == "__main__":
    llm7_base_url = os.environ.get("LLM7_BASE_URL", "https://api.llm7.io/v1")
    port = int(os.environ.get("GRPC_PORT", "50054"))  # Use port 50054 by default
    serve(host="0.0.0.0", port=port, llm7_base_url=llm7_base_url)