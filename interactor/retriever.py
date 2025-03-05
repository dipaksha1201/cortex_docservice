from cortex_ingestion import CortexIngestion
from cortex_ingestion._graphrag import QueryParam
from typing import Union, List
from interactor.models import Entity, Relationship

def serialize_entities(entities):
    serialized_entities = []
    for entity , score in entities:
        serialized_entities.append(Entity(
            name=entity.name,
            description=entity.description,
            type=entity.type,
            score=score
        ).model_dump())
    return serialized_entities

def get_chunk_content_by_hash(chunks, target_hash_list):
    content = []
    for target_hash in target_hash_list:
        for chunk, _ in chunks:
            if chunk.id == target_hash:  # Direct comparison for scalar values
                content.append(chunk.content)
    return content

def serialize_relationships(relationships , chunks):
    serialized_relationships = []
    for relationship , score in relationships:
        serialized_relationships.append(Relationship(
            source=relationship.source,
            target=relationship.target,
            description=relationship.description,
            chunks=get_chunk_content_by_hash(chunks, relationship.chunks),
            score=score
        ).model_dump())
    return serialized_relationships

async def query_file(user_name: str, query: Union[str, List[str]]):
    # Use the same working_dir as used in indexing
    graph_rag = CortexIngestion(
        working_dir=f"dev/{user_name}",  # Must match the working_dir used in indexing
        domain="",  # These values don't matter for querying
        example_queries="",  # as the graph structure is already stored
        entity_types=[],     # in the working_dir
    )
    
    # Convert single query to list for uniform handling
    queries = [query] if isinstance(query, str) else query
    
    # Properly initialize state manager
    await graph_rag.state_manager.query_start()
    try:
        for q in queries:
            print("---------------Q-----------------")
            print(q)
            print("--------------------------------")
            # Yield processing status
            yield {
                "type": "processing",
                "query": q
            }
            
            response = await graph_rag.async_query(q, params=QueryParam(only_context=False))
            entities = serialize_entities(response.context.entities)
            relationships = serialize_relationships(response.context.relations, response.context.chunks)
            print("---------------R-----------------")
            print(response.response)
            print("--------------------------------")
            # Yield response
            yield {
                "type": "response",
                "query": q,
                "response" : response.response,
                "data": {
                    "entities": entities,
                    "relationships": relationships
                }
            }
    except Exception as e:
        yield {
            "type": "error",
            "message": str(e)
        }
    finally:
        await graph_rag.state_manager.query_done()