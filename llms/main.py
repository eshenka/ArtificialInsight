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

# Import the official Ollama Python client
import ollama

from logging_config import setup_logging

# Set up structured JSON logging
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger = setup_logging('llms', log_level)

class LLMService(llms_pb2_grpc.LLMServiceServicer):
    def __init__(self, ollama_host="http://localhost:11434"):
        """Initialize the LLM service with available models and API configurations."""
        self.api_keys = {
            "llm": os.environ.get("LLM_KEY"),
        }
        
        self.ollama_host = ollama_host
        self.use_ollama_fallback = os.environ.get("USE_OLLAMA_FALLBACK", "true").lower() == "true"
        
        # Configure Ollama client - update with the proper client configuration
        if self.use_ollama_fallback:
            # The Ollama client now uses the OLLAMA_HOST environment variable
            # Set it for the client to use
            os.environ["OLLAMA_HOST"] = self.ollama_host
        
        self.models = {
            "model_name": {
                "provider": "provider_name",
                "language": "lang",
                "max_context_length": 128000,
                "api_url": "url"
            }
        }
        
        # Check for required Ollama models
        self.required_ollama_models = self._parse_required_ollama_models()
        if self.use_ollama_fallback and self.required_ollama_models:
            self._ensure_required_models()
        
        # Get available Ollama models
        self.ollama_models = self._get_ollama_models() if self.use_ollama_fallback else {}
        for model_name, model_info in self.ollama_models.items():
            self.models[f"ollama/{model_name}"] = {
                "provider": "ollama",
                "language": "en", 
                "max_context_length": model_info.get("context_length", 4096),
                "api_url": f"{self.ollama_host}/api/generate"
            }
        
        missing_keys = [provider for provider, key in self.api_keys.items() if not key and provider != "ollama"]
        if missing_keys:
            logger.warning(f"Missing API keys for providers: {', '.join(missing_keys)}")
            
        if self.use_ollama_fallback and not self.ollama_models:
            logger.warning("Ollama fallback is enabled but no Ollama models were found")
    
    def _parse_required_ollama_models(self) -> List[str]:
        """Parse the required Ollama models from environment variable."""
        models_str = os.environ.get("REQUIRED_OLLAMA_MODELS", "")
        if not models_str:
            return []
        
        # Parse comma-separated list of models
        models = [model.strip() for model in models_str.split(",") if model.strip()]
        logger.info(f"Required Ollama models: {', '.join(models)}")
        return models
    
    def _ensure_required_models(self):
        """Ensure that all required Ollama models are available."""
        try:
            # Get list of available models
            available_models = {model.model for model in ollama.list()['models']}
            
            # Check which required models are missing
            missing_models = [model for model in self.required_ollama_models if model not in available_models]
            
            if missing_models:
                logger.warning(f"Missing required Ollama models: {', '.join(missing_models)}")
                
                # Try to pull missing models if configured
                if os.environ.get("AUTO_PULL_OLLAMA_MODELS", "false").lower() == "true":
                    for model in missing_models:
                        try:
                            logger.info(f"Pulling Ollama model: {model}")
                            ollama.pull(model)
                            logger.info(f"Successfully pulled Ollama model: {model}")
                        except Exception as e:
                            logger.error(f"Failed to pull Ollama model {model}: {e}")
                else:
                    logger.warning("Auto-pulling is disabled. Please pull the required models manually.")
                    for model in missing_models:
                        logger.warning(f"Run: ollama pull {model}")
            
        except Exception as e:
            logger.error(f"Error ensuring required Ollama models: {e}")
    
    def _get_ollama_models(self) -> Dict[str, Dict[str, Any]]:
        """Get available Ollama models using the Python library."""
        try:
            models = {}
            # Use the Ollama Python library to list models
            ollama_models = ollama.list()
            
            for model in ollama_models['models']:
                name = model.model
                if name:
                    try:
                        # Get model info using the current Ollama API
                        model_info = ollama.show(name)
                        # Check if the parameters structure has changed
                        if "parameters" in model_info:
                            context_size = model_info.get("parameters", {}).get("context_length", 4096)
                        else:
                            context_size = model_info.get("context_length", 4096)
                        models[name] = {
                            "context_length": context_size
                        }
                    except Exception as e:
                        logger.warning(f"Error getting info for Ollama model {name}: {e}")
                        models[name] = {"context_length": 4096}  # Default context size
                        
            logger.info(f"Found {len(models)} Ollama models: {', '.join(models.keys())}")
            return models
        except Exception as e:
            logger.warning(f"Error connecting to Ollama: {e}")
            return {}
    
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
    def _call_openai_api(self, model_name: str, prompt: str) -> str:
        """Call the OpenAI API with the given prompt."""
        api_key = self.api_keys["openai"]
        if not api_key:
            raise ValueError("OpenAI API key not found")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        response = requests.post(
            self.models[model_name]["api_url"],
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            logger.error(f"OpenAI API error: {response.status_code} {response.text}")
            raise Exception(f"API error: {response.status_code}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_ollama_api(self, model_name: str, prompt: str) -> str:
        """Call the Ollama API using the Python library."""
        actual_model_name = model_name.split("/", 1)[1] if "/" in model_name else model_name
        
        try:
            # Use the ollama.generate function from the Python library
            response = ollama.generate(
                model=actual_model_name,
                prompt=prompt,
                stream=False,
                options={
                    "temperature": 0.7,
                    "num_predict": 1024  # Equivalent to max_tokens
                }
            )
            
            return response['response']
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise
    
    def _call_model_api(self, model_name: str, prompt: str) -> str:
        """Call the appropriate API based on the model name."""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        
        provider = self.models[model_name]["provider"]
        
        if provider == "openai": # as an example
            return self._call_openai_api(model_name, prompt)
        elif provider == "ollama":
            return self._call_ollama_api(model_name, prompt)
        else:
            raise ValueError(f"Provider {provider} not supported")
    
    def _try_with_fallback(self, model_name: str, prompt: str) -> tuple[str, bool]:
        """
        Try to call the specified model, falling back to Ollama if needed.
        Returns the answer and whether a fallback was used.
        """
        try:
            return self._call_model_api(model_name, prompt), False
        except Exception as e:
            logger.warning(f"Error with primary model {model_name}: {e}")
            
            if not self.use_ollama_fallback or not self.ollama_models:
                raise  
            
            # Try to use preferred fallback models first (from required models list)
            preferred_models = [model for model in self.required_ollama_models if model in self.ollama_models]
            all_models = list(preferred_models) + [model for model in self.ollama_models if model not in preferred_models]
            
            last_error = None
            for ollama_model_name in all_models:
                fallback_model = f"ollama/{ollama_model_name}"
                try:
                    logger.info(f"Trying fallback with Ollama model: {ollama_model_name}")
                    return self._call_ollama_api(fallback_model, prompt), True
                except Exception as err:
                    last_error = err
                    logger.warning(f"Fallback with {ollama_model_name} failed: {err}")
            
            if last_error:
                raise last_error
            else:
                raise Exception("All LLM providers failed, including fallbacks")
    
    def GenerateAnswer(self, request, context):
        """Generate an answer for the given question using the provided context."""
        model_name = request.model_name
        question = request.question
        user_context = request.context
        
        try:
            if model_name not in self.models and not model_name.startswith("ollama/"):
                if self.use_ollama_fallback and self.ollama_models:
                    # Try to use a required model first if available
                    for required_model in self.required_ollama_models:
                        if required_model in self.ollama_models:
                            model_name = f"ollama/{required_model}"
                            logger.info(f"Model not found, using preferred Ollama model: {model_name}")
                            break
                    else:
                        # If no required model is available, use the first available one
                        first_ollama_model = next(iter(self.ollama_models.keys()))
                        model_name = f"ollama/{first_ollama_model}"
                        logger.info(f"Model not found, using Ollama fallback: {model_name}")
                else:
                    context.abort(StatusCode.NOT_FOUND, f"Model {model_name} not found")
            
            provider = self.models[model_name]["provider"]
            if provider != "ollama" and not self.api_keys[provider]:
                if self.use_ollama_fallback and self.ollama_models:
                    # Try to use a required model first if available
                    for required_model in self.required_ollama_models:
                        if required_model in self.ollama_models:
                            model_name = f"ollama/{required_model}"
                            provider = "ollama"
                            logger.info(f"API key not found, using preferred Ollama model: {model_name}")
                            break
                    else:
                        # If no required model is available, use the first available one
                        first_ollama_model = next(iter(self.ollama_models.keys()))
                        model_name = f"ollama/{first_ollama_model}"
                        provider = "ollama"
                        logger.info(f"API key not found, using Ollama fallback: {model_name}")
                else:
                    context.abort(StatusCode.UNAVAILABLE, f"API key for {provider} not configured")
            
            prompt = self._create_prompt(question, user_context)

            logger.info(f"Generating response for prompt: {prompt}")
            
            answer, used_fallback = self._try_with_fallback(model_name, prompt)
            
            log_message = f"Generated answer for question: {question[:50]}..."
            if used_fallback:
                log_message += " (used Ollama fallback)"
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
            
            for name, config in self.models.items():
                if config["provider"] == "ollama":
                    continue
                    
                if language and config["language"] != language:
                    continue
                
                if not self.api_keys[config["provider"]]:
                    continue
                
                model = llms_pb2.Model(
                    name=name,
                    provider=config["provider"],
                    language=config["language"]
                )
                models_list.append(model)
            
            if self.use_ollama_fallback:
                for ollama_model in self.ollama_models.keys():
                    if language and language != "en":
                        continue
                    
                    model = llms_pb2.Model(
                        name=f"ollama/{ollama_model}",
                        provider="ollama",
                        language="en"
                    )
                    models_list.append(model)
            
            return llms_pb2.GetAvailableModelsResponse(models=models_list)
            
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            context.abort(StatusCode.INTERNAL, f"Failed to get available models: {str(e)}")


def serve(host="0.0.0.0", port=50052, ollama_host="http://localhost:11434"):
    """Start the gRPC server."""
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    llms_pb2_grpc.add_LLMServiceServicer_to_server(
        LLMService(ollama_host=ollama_host), server
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
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    serve(ollama_host=ollama_host)
