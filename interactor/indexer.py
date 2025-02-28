from doc_extractor import DocExtractor
from cortex_ingestion import CortexIngestion
from typing import AsyncGenerator, Dict, Any


async def index_file(file_obj: Dict[str, Any], user_name: str) -> AsyncGenerator[Dict[str, Any], None]:
    doc_extractor = DocExtractor()
    
    yield {"status": "extracting", "message": "Extracting document features and content..."}
    features, parsed_text = await doc_extractor.extract(file_obj)
    
    yield {"status": "understanding", "message": "Understanding document structure..."}
    ingestion = CortexIngestion(
                working_dir=f"dev/{user_name}",
                domain=features.domain,
                example_queries="\n".join(features.queries),
                entity_types=features.entity_types,
            )
    
    yield {"status": "indexing", "message": "Indexing document content..."}
    await ingestion.async_insert(parsed_text)
    
    yield {"status": "completed", "message": "Document indexed successfully", "features": features.dict()}