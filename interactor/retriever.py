from cortex_ingestion import CortexIngestion
from cortex_ingestion._graphrag import QueryParam

def convert_to_serializable(context):
    """Convert context to JSON serializable format"""
    return {
        "entities": [(str(e), float(s)) for e, s in context.entities],
        "relations": [(str(r), float(s)) for r, s in context.relations],
        "chunks": [(str(c), float(s)) for c, s in context.chunks]
    }

async def query_file(user_name: str, query: str):
    # Use the same working_dir as used in indexing
    graph_rag = CortexIngestion(
        working_dir=f"dev/{user_name}",  # Must match the working_dir used in indexing
        domain="",  # These values don't matter for querying
        example_queries="",  # as the graph structure is already stored
        entity_types=[],     # in the working_dir
    )
    
    # Properly initialize state manager
    await graph_rag.state_manager.query_start()
    try:
        response = await graph_rag.async_query(query, params=QueryParam(only_context=False))
        context = convert_to_serializable(response.context)
        response = response.response
        return response
    finally:
        await graph_rag.state_manager.query_done()