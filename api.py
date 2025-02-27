"""
Cortex Ingestion API - FastAPI Backend
"""

import os
import sys
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn

# Ensure we can import from the current directory
sys.path.append('.')

# Import from cortex_ingestion module
import cortex_ingestion as ci

# Create FastAPI app
app = FastAPI(
    title="Cortex Ingestion API",
    description="API for the Cortex Ingestion System",
    version="0.1.0",
)

# Models for API requests and responses
class IngestionRequest(BaseModel):
    content: str = Field(..., description="Text content to ingest")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata for the content")

class QueryRequest(BaseModel):
    query: str = Field(..., description="The query to run against the system")
    max_results: Optional[int] = Field(default=10, description="Maximum number of results to return")

class QueryResponse(BaseModel):
    results: Dict[str, Any] = Field(..., description="Query results")
    query: str = Field(..., description="Original query")

# Global instance of CortexIngestion
cortex_instance = None

def get_cortex_instance():
    """
    Dependency to get or create the Cortex instance.
    This ensures we only initialize it once.
    """
    global cortex_instance
    if cortex_instance is None:
        # Load configuration from environment variables
        config = ci.CortexConfig(
            # Core settings
            working_dir=os.environ.get("CORTEX_WORKING_DIR", "./cortex_workspace"),
            domain=os.environ.get("CORTEX_DOMAIN", "default"),
            
            # Cloud provider settings - enable based on environment
            use_cloud_vector_storage=os.environ.get("USE_PINECONE", "false").lower() == "true",
            use_cloud_document_storage=os.environ.get("USE_MONGODB", "false").lower() == "true",
            use_cloud_graph_storage=os.environ.get("USE_NEO4J", "false").lower() == "true",
            
            # Credentials
            pinecone_api_key=os.environ.get("PINECONE_API_KEY", ""),
            pinecone_environment=os.environ.get("PINECONE_ENV", "us-west1-gcp"),
            pinecone_index=os.environ.get("PINECONE_INDEX", "cortex-vectors"),
            
            mongodb_connection_string=os.environ.get("MONGODB_URI", None),
            mongodb_username=os.environ.get("MONGODB_USERNAME", "cortex"),
            mongodb_password=os.environ.get("MONGODB_PASSWORD", ""),
            mongodb_host=os.environ.get("MONGODB_HOST", "cluster0.example.mongodb.net"),
            mongodb_database=os.environ.get("MONGODB_DATABASE", "cortex"),
            mongodb_collection=os.environ.get("MONGODB_COLLECTION", "chunks"),
            
            neo4j_password=os.environ.get("NEO4J_PASSWORD", ""),
            neo4j_instance_id=os.environ.get("NEO4J_INSTANCE_ID", ""),
            neo4j_database=os.environ.get("NEO4J_DATABASE", "neo4j"),
        )
        cortex_instance = ci.CortexIngestion(config)
    
    return cortex_instance

@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    return {"status": "online", "message": "Cortex Ingestion API is running"}

@app.post("/ingest")
async def ingest_content(
    request: IngestionRequest,
    background_tasks: BackgroundTasks,
    cortex: ci.CortexIngestion = Depends(get_cortex_instance)
):
    """
    Ingest content into the Cortex system.
    This is processed in the background to avoid blocking the API.
    """
    try:
        # If metadata is provided, combine with content
        if request.metadata:
            content = {"text": request.content, "metadata": request.metadata}
        else:
            content = request.content
            
        # Add to background tasks to avoid blocking
        background_tasks.add_task(cortex.ingest, content)
        
        return {
            "status": "success", 
            "message": "Content scheduled for ingestion"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_system(
    request: QueryRequest,
    cortex: ci.CortexIngestion = Depends(get_cortex_instance)
):
    """Query the Cortex system."""
    try:
        # Execute the query
        results = cortex.query(request.query)
        
        return {
            "results": results,
            "query": request.query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Run the app
if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload for development
    ) 