import grpc
import concurrent.futures
from grpc import StatusCode
import time
import logging
from typing import List, Optional

from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from pymilvus import db 
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from proto import vectordb_pb2
from proto import vectordb_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import re
import textwrap

import numpy as np
from sentence_transformers import SentenceTransformer


class VectorDatabaseService(vectordb_pb2_grpc.VectorDatabaseServiceServicer):
    def __init__(self, milvus_host="localhost", milvus_port=19530):
        """Initialize the service with connection to Milvus."""
        self.embedding_models = {
            "en": ["sentence-transformers/all-MiniLM-L6-v2", "OpenAI/text-embedding-ada-002"],
            "ru": ["sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"]
        }
        self.loaded_models = {}
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        
        try:
            connections.connect(host=milvus_host, port=milvus_port)
            logger.info(f"Connected to Milvus server at {milvus_host}:{milvus_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise
    
    def _get_model(self, model_name: str):
        """Get or load embedding model."""
        if model_name not in self.loaded_models:
            try:
                self.loaded_models[model_name] = SentenceTransformer(model_name)
                logger.info(f"Loaded embedding model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load embedding model {model_name}: {e}")
                raise
        return self.loaded_models[model_name]
    
    def _chunk_document(self, document: vectordb_pb2.Document, chunk_size=512, overlap=50):
        """Split document content into smaller chunks."""
        content = document.content
        source = document.source
        chunks = []
        
        # Think about delimeter
        paragraphs = re.split(r'\n\s*\n', content)
        
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
                
            if len(paragraph) > chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= chunk_size:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk:
                            doc = vectordb_pb2.Document(
                                source=f"{source}#chunk{len(chunks)+1}",
                                content=current_chunk.strip(),
                                score=0.0
                            )
                            chunks.append(doc)
                        current_chunk = sentence + " "
                
                if current_chunk:
                    doc = vectordb_pb2.Document(
                        source=f"{source}#chunk{len(chunks)+1}",
                        content=current_chunk.strip(),
                        score=0.0
                    )
                    chunks.append(doc)
            else:
                doc = vectordb_pb2.Document(
                    source=f"{source}#chunk{len(chunks)+1}",
                    content=paragraph.strip(),
                    score=0.0
                )
                chunks.append(doc)
        
        return chunks if chunks else [document] 
    
    def _ensure_database_exists(self, database_name: str):
        """Ensure the database exists, creating it if necessary."""
        try:
            all_dbs = db.list_database()
            
            if database_name not in all_dbs:
                db.create_database(database_name)
                logger.info(f"Created database: {database_name}")
            
            db.using_database(database_name)
            logger.info(f"Using database: {database_name}")
            return True
        except Exception as e:
            logger.error(f"Error ensuring database exists: {e}")
            return False

    def _create_collection_in_db(self, collection_name: str, embedding_model: str, database_name: str):
        """Create a collection in the specified database."""
        self._ensure_database_exists(database_name)
        
        model = self._get_model(embedding_model)
        dim = model.get_sentence_embedding_dimension()
        
        description = f"Collection for {collection_name}, using model {embedding_model}"
        
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
        ]
        
        schema = CollectionSchema(fields=fields, description=description)
        collection = Collection(name=collection_name, schema=schema)
        
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 128}
        }
        collection.create_index("embedding", index_params)
        collection.load()
        
        return collection
    
    def CreateCollection(self, request, context):
        """Implementation of CreateCollection RPC."""
        company_id = request.collection_name
        embedding_model = request.embedding_model
        documents = request.documents
        
        database_name = f"company_{company_id}"
        collection_name = "documents"
        
        try:
            if not self._ensure_database_exists(database_name):
                context.abort(StatusCode.INTERNAL, f"Failed to create database for company {company_id}")
            
            if utility.has_collection(collection_name):
                context.abort(StatusCode.ALREADY_EXISTS, f"Collection already exists for company {company_id}")
            
            collection = self._create_collection_in_db(collection_name, embedding_model, database_name)
            
            if documents:
                processed_docs = []
                for doc in documents:
                    chunks = self._chunk_document(doc)
                    processed_docs.extend(chunks)
                
                model = self._get_model(embedding_model)
                sources = [doc.source for doc in processed_docs]
                contents = [doc.content for doc in processed_docs]
                embeddings = model.encode(contents)
                
                data = [
                    sources,
                    contents,
                    embeddings.tolist()
                ]
                
                collection.insert(data)
                collection.flush()
            
            logger.info(f"Created database {database_name} with collection and {len(processed_docs) if documents else 0} documents")
            return vectordb_pb2.CreateCollectionResponse()
            
        except Exception as e:
            logger.error(f"Error creating collection for company {company_id}: {e}")
            context.abort(StatusCode.INTERNAL, f"Failed to create collection: {str(e)}")
    
    def AddDocuments(self, request, context):
        """Implementation of AddDocuments RPC."""
        company_id = request.collection_name
        documents = request.documents
        
        database_name = f"company_{company_id}"
        collection_name = "documents"
        
        try:
            all_dbs = db.list_database()
            if database_name not in all_dbs:
                context.abort(StatusCode.NOT_FOUND, f"Database for company {company_id} does not exist")
            
            db.using_database(database_name)
            
            if not utility.has_collection(collection_name):
                context.abort(StatusCode.NOT_FOUND, f"Collection for company {company_id} does not exist")
            
            collection = Collection(collection_name)
            collection.load()
            
            description = collection.description
            embedding_model = description.split("using model ")[-1] if "using model " in description else self.embedding_models["en"][0]
            
            processed_docs = []
            for doc in documents:
                chunks = self._chunk_document(doc)
                processed_docs.extend(chunks)
            
            model = self._get_model(embedding_model)
            sources = [doc.source for doc in processed_docs]
            contents = [doc.content for doc in processed_docs]
            embeddings = model.encode(contents)
            
            data = [
                sources,
                contents,
                embeddings.tolist()
            ]
            
            collection.insert(data)
            collection.flush()
            
            logger.info(f"Added {len(processed_docs)} documents to collection for company {company_id}")
            return vectordb_pb2.AddDocumentsResponse()
            
        except Exception as e:
            logger.error(f"Error adding documents for company {company_id}: {e}")
            context.abort(StatusCode.INTERNAL, f"Failed to add documents: {str(e)}")
    
    def Search(self, request, context):
        """Implementation of Search RPC."""
        company_id = request.collection_name
        query = request.query
        limit = request.limit if request.limit > 0 else 10
        
        database_name = f"company_{company_id}"
        collection_name = "documents"
        
        try:
            all_dbs = db.list_database()
            if database_name not in all_dbs:
                context.abort(StatusCode.NOT_FOUND, f"Database for company {company_id} does not exist")
            
            db.using_database(database_name)
            
            if not utility.has_collection(collection_name):
                context.abort(StatusCode.NOT_FOUND, f"Collection for company {company_id} does not exist")
            
            collection = Collection(collection_name)
            collection.load()
            
            description = collection.description
            embedding_model = description.split("using model ")[-1] if "using model " in description else self.embedding_models["en"][0]
            
            model = self._get_model(embedding_model)
            query_embedding = model.encode([query])[0].tolist()
            
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }
            
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                output_fields=["source", "content"]
            )
            
            response_docs = []
            for hits in results:
                for hit in hits:
                    doc = vectordb_pb2.Document(
                        source=hit.entity.get('source'),
                        content=hit.entity.get('content'),
                        score=float(hit.score)
                    )
                    response_docs.append(doc)
            
            return vectordb_pb2.SearchResponse(results=response_docs)
            
        except Exception as e:
            logger.error(f"Error searching for company {company_id}: {e}")
            context.abort(StatusCode.INTERNAL, f"Failed to perform search: {str(e)}")
    
    def DeleteCollection(self, request, context):
        """Implementation of DeleteCollection RPC."""
        company_id = request.collection_name
        database_name = f"company_{company_id}"
        
        try:
            all_dbs = db.list_database()
            if database_name not in all_dbs:
                context.abort(StatusCode.NOT_FOUND, f"Database for company {company_id} does not exist")
            
            db.drop_database(database_name)
            logger.info(f"Deleted database for company {company_id}")
            return vectordb_pb2.DeleteCollectionResponse()
            
        except Exception as e:
            logger.error(f"Error deleting database for company {company_id}: {e}")
            context.abort(StatusCode.INTERNAL, f"Failed to delete collection: {str(e)}")
    
    def GetCollectionInfo(self, request, context):
        """Implementation of GetCollectionInfo RPC."""
        company_id = request.collection_name
        database_name = f"company_{company_id}"
        collection_name = "documents"
        
        try:
            all_dbs = db.list_database()
            if database_name not in all_dbs:
                context.abort(StatusCode.NOT_FOUND, f"Database for company {company_id} does not exist")
            
            db.using_database(database_name)
            
            if not utility.has_collection(collection_name):
                context.abort(StatusCode.NOT_FOUND, f"Collection for company {company_id} does not exist")
            
            collection = Collection(collection_name)
            stats = collection.get_stats()
            
            row_count = int(stats["row_count"])
            size_estimate = row_count * 1024 
            
            info = vectordb_pb2.CollectionInfo(
                collection_name=company_id, 
                document_count=row_count,
                size=size_estimate
            )
            
            return vectordb_pb2.GetCollectionInfoResponse(info=info)
            
        except Exception as e:
            logger.error(f"Error getting info for company {company_id}: {e}")
            context.abort(StatusCode.INTERNAL, f"Failed to get collection info: {str(e)}")

    def GetEmbeddingModels(self, request, context):
        """Implementation of GetEmbeddingModels RPC."""
        language = request.language
        
        try:
            models = []
            if language:
                if language in self.embedding_models:
                    for model_name in self.embedding_models[language]:
                        dim = self._get_model(model_name).get_sentence_embedding_dimension()
                        models.append(vectordb_pb2.Model(
                            name=model_name,
                            language=language,
                            provider="SentenceTransformers" if "sentence-transformers" in model_name else "OpenAI",
                            dimension=dim
                        ))
            else:
                for lang, model_list in self.embedding_models.items():
                    for model_name in model_list:
                        dim = self._get_model(model_name).get_sentence_embedding_dimension()
                        models.append(vectordb_pb2.Model(
                            name=model_name,
                            language=lang,
                            provider="SentenceTransformers" if "sentence-transformers" in model_name else "OpenAI",
                            dimension=dim
                        ))
            
            return vectordb_pb2.GetEmbeddingModelsResponse(models=models)
            
        except Exception as e:
            logger.error(f"Error getting embedding models: {e}")
            context.abort(StatusCode.INTERNAL, f"Failed to get embedding models: {str(e)}")


def serve(host="0.0.0.0", port=50051):
    """Start the gRPC server."""
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    vectordb_pb2_grpc.add_VectorDatabaseServiceServicer_to_server(
        VectorDatabaseService(), server
    )
    server.add_insecure_port(f"{host}:{port}")
    server.start()
    logger.info(f"Server started on {host}:{port}")
    
    try:
        while True:
            time.sleep(86400) 
    except KeyboardInterrupt:
        server.stop(0)
        logger.info("Server stopped")


if __name__ == "__main__":
    serve()