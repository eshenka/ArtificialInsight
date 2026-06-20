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

# Import OpenAI client for LLM7
import openai

from logging_config import setup_logging

# Set up structured JSON logging
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger = setup_logging('llms', log_level)

class LLMService(llms_pb2_grpc.LLMServiceServicer):
    def __init__(self, llm7_base_url="https://api.llm7.io/v1"):
        """Initialize the LLM service with LLM7 models."""
        # LLM7 doesn't require a real API key, but expects "unused" as the value
        self.api_key = os.environ.get("LLM_KEY", "unused")
        self.llm7_base_url = llm7_base_url
        
        # Initialize the OpenAI client with LLM7 base URL
        try:
            self.client = openai.OpenAI(
                base_url=self.llm7_base_url,
                api_key=self.api_key
            )
            logger.info(f"Initialized OpenAI client with LLM7 base URL: {self.llm7_base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            # Continue anyway, we'll handle errors when making API calls
        
        # Define all available LLM7 models with their configurations
        # Source: https://llm7.io/docs/reference/models
        self.models = {
            # English models
            "gpt-4.1-nano": {
                "provider": "llm7",
                "language": "en",
                "max_context_length": 128000,
            },
            "gpt-4.1-mini": {
                "provider": "llm7",
                "language": "en",
                "max_context_length": 128000,
            },
            "gpt-4.1-express": {
                "provider": "llm7",
                "language": "en", 
                "max_context_length": 128000,
            },
            "gpt-4.1-preview": {
                "provider": "llm7",
                "language": "en",
                "max_context_length": 128000,
            },
            
            # Russian models
            "gpt-4.1-mini-ru": {
                "provider": "llm7",
                "language": "ru",
                "max_context_length": 128000,
            },
            "gpt-4.1-express-ru": {
                "provider": "llm7",
                "language": "ru",
                "max_context_length": 128000,
            },
            
            # Add model prefixes for backward compatibility
            "llm7/gpt-4.1-nano": {
                "provider": "llm7",
                "language": "en",
                "max_context_length": 128000,
            },
            "llm7/gpt-4.1-mini": {
                "provider": "llm7",
                "language": "en",
                "max_context_length": 128000,
            },
            "llm7/gpt-4.1-express": {
                "provider": "llm7",
                "language": "en", 
                "max_context_length": 128000,
            },
            "llm7/gpt-4.1-preview": {
                "provider": "llm7",
                "language": "en",
                "max_context_length": 128000,
            },
            "llm7/gpt-4.1-mini-ru": {
                "provider": "llm7",
                "language": "ru",
                "max_context_length": 128000,
            },
            "llm7/gpt-4.1-express-ru": {
                "provider": "llm7",
                "language": "ru",
                "max_context_length": 128000,
            }
        }
        
        logger.info(f"LLM Service initialized with {len(self.models)} models")
        
        # Log available languages
        languages = set(model["language"] for model in self.models.values())
        logger.info(f"Available languages: {', '.join(languages)}")
    
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
        """Call the LLM7 API with the given model and prompt."""
        actual_model_name = model_name.split("/", 1)[1] if "/" in model_name else model_name
        
        try:
            logger.info(f"Calling LLM7 API with model: {actual_model_name}")
            
            response = self.client.chat.completions.create(
                model=actual_model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1024
            )
            
            answer = response.choices[0].message.content
            logger.debug(f"Got response from LLM7 API: {answer[:50]}...")
            return answer
            
        except Exception as e:
            logger.error(f"LLM7 API error with model {actual_model_name}: {e}")
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
    
    def _get_default_model(self, language: str) -> str:
        """Get the default model for the specified language."""
        if language == "ru":
            return "gpt-4.1-mini-ru"
        else:  # Default to English
            return "gpt-4.1-nano"
    
    def GenerateAnswer(self, request, context):
        """Generate an answer for the given question using the provided context."""
        model_name = request.model_name
        question = request.question
        user_context = request.context
        
        try:
            # Check if the requested model exists
            if model_name not in self.models:
                # If the model name includes a prefix, try without it
                if "/" in model_name:
                    base_model_name = model_name.split("/", 1)[1]
                    if base_model_name in self.models:
                        model_name = base_model_name
                        logger.info(f"Using base model name: {model_name}")
                    else:
                        # Find a model for the same language as the requested one
                        language = "en"  # Default language
                        for model_key, model_info in self.models.items():
                            if model_key.lower() == model_name.lower() or model_key.lower().endswith(f"/{model_name.lower()}"):
                                language = model_info["language"]
                                break
                        
                        default_model = self._get_default_model(language)
                        logger.info(f"Model {model_name} not found, using default model for language {language}: {default_model}")
                        model_name = default_model
                else:
                    # Find a suitable default model
                    language = "en"  # Default to English
                    for existing_model in self.models.keys():
                        if existing_model.lower() == model_name.lower():
                            model_name = existing_model  # Use the correct case
                            break
                    else:
                        default_model = self._get_default_model(language)
                        logger.info(f"Model {model_name} not found, using default model: {default_model}")
                        model_name = default_model
            
            prompt = self._create_prompt(question, user_context)
            logger.info(f"Generating answer with model {model_name} for prompt: {prompt[:100]}...")
            
            answer = self._call_model_api(model_name, prompt)
            logger.info(f"Generated answer for question: {question[:50]}...")
            
            return llms_pb2.GenerateAnswerResponse(answer=answer)
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            context.abort(StatusCode.INTERNAL, f"Failed to generate answer: {str(e)}")
    
    def GetAvailableModels(self, request, context):
        """Get a list of available LLM models, optionally filtered by language."""
        language = request.language
        
        try:
            models_list = []
            logger.info(f"Getting available models for language: {language or 'any'}")
            
            for name, config in self.models.items():
                # Skip models with provider prefix for cleaner results
                if "/" in name:
                    continue
                    
                # Only include models for the requested language if specified
                if language and config["language"] != language:
                    continue
                
                model = llms_pb2.Model(
                    name=name,
                    provider=config["provider"],
                    language=config["language"]
                )
                models_list.append(model)
            
            # If no models are found for the requested language, add default models
            if not models_list:
                logger.warning(f"No models found for language: {language}. Adding default models.")
                if language == "ru":
                    default_model = "gpt-4.1-mini-ru"
                else:
                    default_model = "gpt-4.1-nano"
                    
                models_list.append(llms_pb2.Model(
                    name=default_model,
                    provider="llm7",
                    language="en" if language != "ru" else "ru"
                ))
            
            logger.info(f"Returning {len(models_list)} available models")
            return llms_pb2.GetAvailableModelsResponse(models=models_list)
            
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            # Return at least one model to prevent failures
            default_model = self._get_default_model(language or "en")
            default_lang = "ru" if language == "ru" else "en"
            
            return llms_pb2.GetAvailableModelsResponse(models=[
                llms_pb2.Model(
                    name=default_model,
                    provider="llm7",
                    language=default_lang
                )
            ])


def serve(host="0.0.0.0", port=50052, llm7_base_url="https://api.llm7.io/v1"):
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
    port = int(os.environ.get("GRPC_PORT", "50052"))
    serve(host="0.0.0.0", port=port, llm7_base_url=llm7_base_url)
