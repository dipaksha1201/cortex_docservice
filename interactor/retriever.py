from cortex_ingestion import CortexIngestion
from cortex_ingestion._graphrag import QueryParam
from typing import Union, List

def convert_to_serializable(context):
    """Convert context to JSON serializable format"""
    return {
        "entities": [(str(e), float(s)) for e, s in context.entities],
        "relations": [(str(r), float(s)) for r, s in context.relations],
        "chunks": [(str(c), float(s)) for c, s in context.chunks]
    }

def create_context_string(context):
    """Create a combined string representation of context suitable for LLM consumption"""
    parts = []
    
    if context["entities"]:
        entities_by_type = {}
        for entity, score in context["entities"]:
            # Extract name and type from TEntity string format
            if "TEntity" in entity:
                entity_parts = entity.split("description='")
                if len(entity_parts) > 1:
                    name = entity_parts[0].split("name='")[1].split("'")[0]
                    type_ = entity_parts[0].split("type='")[1].split("'")[0]
                    desc = entity_parts[1].split("'")[0]
                    
                    if type_ not in entities_by_type:
                        entities_by_type[type_] = []
                    entities_by_type[type_].append((name, desc, score))
        
        entities_str = "## Relevant Concepts\n\n"
        for type_ in sorted(entities_by_type.keys()):
            entities_str += f"### {type_.title()}\n"
            for name, desc, score in sorted(entities_by_type[type_], key=lambda x: x[2], reverse=True):
                entities_str += f"- **{name}** (confidence: {score:.2f})\n  {desc}\n"
            entities_str += "\n"
        parts.append(entities_str)
    
    if context["relations"]:
        relations_str = "## Key Relationships\n\n"
        for relation, score in context["relations"]:
            if "TRelation" in relation:
                # Extract source, target, and description from TRelation string format
                rel_parts = relation.split("description='")
                if len(rel_parts) > 1:
                    source = rel_parts[0].split("source='")[1].split("'")[0]
                    target = rel_parts[0].split("target='")[1].split("'")[0]
                    desc = rel_parts[1].split("'")[0]
                    relations_str += f"- **{source}** → **{target}**: {desc} (confidence: {score:.2f})\n"
        parts.append(relations_str)
    
    if context["chunks"]:
        chunks_str = "## Supporting Text\n\n"
        for chunk, score in context["chunks"]:
            # Clean up chunk text
            clean_chunk = chunk.strip().replace('\n\n', '\n')
            if clean_chunk:
                chunks_str += f"{clean_chunk}\n*(confidence: {score:.2f})*\n\n"
        parts.append(chunks_str)
    
    return "\n".join(parts) if parts else "No relevant context found."

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
            # Yield processing status
            yield {
                "type": "processing",
                "query": q
            }
            
            response = await graph_rag.async_query(q, params=QueryParam(only_context=False))
            context = convert_to_serializable(response.context)
            context_string = create_context_string(context)
            
            # Yield response
            yield {
                "type": "response",
                "query": q,
                "data": {
                    "response": response.response,
                    "context_string": context_string
                }
            }
    except Exception as e:
        yield {
            "type": "error",
            "message": str(e)
        }
    finally:
        await graph_rag.state_manager.query_done()