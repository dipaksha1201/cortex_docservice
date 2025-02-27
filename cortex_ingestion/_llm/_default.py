__all__ = ['DefaultLLMService', 'DefaultEmbeddingService']

from cortex_ingestion._llm._llm_openai import OpenAIEmbeddingService, OpenAILLMService


class DefaultLLMService(OpenAILLMService):
    pass
class DefaultEmbeddingService(OpenAIEmbeddingService):
    pass
