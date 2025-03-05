from doc_extractor import DocExtractor
from cortex_ingestion import CortexIngestion
from typing import AsyncGenerator, Dict, Any

from doc_extractor.doc_service import DocumentService
from doc_extractor.models import Document


async def index_file(file_obj: Dict[str, Any], user_name: str) -> AsyncGenerator[Dict[str, Any], None]:
    doc_extractor = DocExtractor()
    
    yield {"status": "Extracting", "message": "Extracting document features and content..."}
    features, parsed_text = await doc_extractor.extract(file_obj)
    document = Document.from_features(features, user_name, file_obj["filename"], "extracted")
    doc_service = DocumentService()
    doc_service.insert_document(document)
    
    ingestion = CortexIngestion(
                working_dir=f"dev/{user_name}",
                domain=features.domain,
                example_queries="\n".join(features.queries),
                entity_types=features.entity_types,
            )
    
    yield {"status": "Understanding", "message": "Understanding document structure..."}
    await ingestion.async_insert(parsed_text)
    doc_service.update_status(document.id, "completed")
    
    yield {"status": "Completed", "message": "Document indexed successfully", "features": features.dict()}