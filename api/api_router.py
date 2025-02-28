from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import logging
import json
from typing import Union, List
from pydantic import BaseModel

from interactor.indexer import index_file as index_file_interactor
from interactor.retriever import query_file as query_file_interactor
# Configure logging
logger = logging.getLogger(__name__)

api_router = APIRouter()

class QueryRequest(BaseModel):
    user_name: str
    queries: Union[str, List[str]]

@api_router.post("/index")
async def index_file(
    user_name: str,
    file: UploadFile = File(...)
):
    """
    Index a file for a given project with streaming status updates
    
    Args:
        user_name: Name of the user (required)
        file: The file to be indexed
    """
    # Read file content immediately to prevent file handle issues
    file_content = await file.read()
    
    async def status_stream():
        try:
            file_obj = {
                "filename": file.filename,
                "content": file_content,
                "content_type": file.content_type
            }
            async for status in index_file_interactor(file_obj, user_name):
                yield json.dumps(status) + "\n"
        except Exception as e:
            logger.error(f"Failed to index file: {e}")
            yield json.dumps({"status": "error", "message": str(e)}) + "\n"
    
    return StreamingResponse(status_stream(), media_type="application/x-ndjson")

@api_router.post("/query")
async def query_file(
    request: QueryRequest
):
    """
    Query a file for a given project with streaming updates
    
    Args:
        request: QueryRequest containing:
            - user_name: Name of the user
            - queries: Single query string or list of query strings
    """
    async def query_stream():
        async for status in query_file_interactor(request.user_name, request.queries):
            yield json.dumps(status) + "\n"
    
    return StreamingResponse(query_stream(), media_type="application/x-ndjson")
