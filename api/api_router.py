from fastapi import APIRouter, HTTPException, UploadFile, File
import logging

from interactor.indexer import index_file as index_file_interactor
from interactor.retriever import query_file as query_file_interactor
# Configure logging
logger = logging.getLogger(__name__)

api_router = APIRouter()

@api_router.post("/index")
async def index_file(
    user_name: str,
    file: UploadFile = File(...)
):
    """
    Index a file for a given project
    
    Args:
        user_name: Name of the user (required)
        file: The file to be indexed
    """
    try: 
        response = await index_file_interactor(file , user_name)
        return response
    
    except Exception as e:
        logger.error(f"Failed to index file: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@api_router.get("/query")
async def query_file(
    user_name: str,
    query: str
):
    """
    Query a file for a given project
    
    Args:
        user_name: Name of the user (required)
        query: The query to be queried
    """
    try: 
        response = await query_file_interactor(user_name, query)
        return response
    except Exception as e:
        logger.error(f"Failed to query file: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
