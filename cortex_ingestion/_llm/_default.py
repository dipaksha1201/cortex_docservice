__all__ = ['DefaultLLMService', 'DefaultEmbeddingService']

from cortex_ingestion._llm._llm_gemini import GeminiEmbeddingService, GeminiLLMService


class DefaultLLMService(GeminiLLMService):
    pass
class DefaultEmbeddingService(GeminiEmbeddingService):
    pass
