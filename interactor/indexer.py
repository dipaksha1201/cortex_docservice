from doc_extractor import DocExtractor
from cortex_ingestion import CortexIngestion


async def index_file(file: str , user_name: str):
    doc_extractor = DocExtractor()
    features , parsed_text = await doc_extractor.extract(file)
    ingestion = CortexIngestion(
                working_dir=f"dev/{user_name}",
                domain=features.domain,
                example_queries="\n".join(features.queries),
                entity_types=features.entity_types,
            )
    await ingestion.async_insert(parsed_text)   
    return features