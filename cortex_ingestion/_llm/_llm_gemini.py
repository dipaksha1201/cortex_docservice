"""LLM Services module."""
import os
import asyncio
from dataclasses import dataclass, field
from itertools import chain
from typing import Any, List, Optional, Tuple, Type, cast

import instructor
import numpy as np
from openai import APIConnectionError, AsyncOpenAI, RateLimitError
from pydantic import BaseModel
from tenacity import (
    AsyncRetrying,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from dotenv import load_dotenv

from cortex_ingestion._exceptions import LLMServiceNoResponseError
from cortex_ingestion._types import BaseModelAlias
from cortex_ingestion._utils import logger
from cortex_ingestion._utils import throttle_async_func_call

from cortex_ingestion._llm._base import BaseEmbeddingService, BaseLLMService, T_model

load_dotenv()  # Load environment variables from .env

@dataclass
class GeminiLLMService(BaseLLMService):
    """LLM Service for Gemini using OpenAI-compatible endpoint."""

    model: Optional[str] = field(default="gemini-2.0-flash")
    mode: instructor.Mode = field(default=instructor.Mode.JSON)

    def __post_init__(self):
        self.llm_async_client = instructor.from_openai(
            AsyncOpenAI(
                api_key=os.getenv('GEMINI_API_KEY_BETA'),
                base_url=os.getenv('GEMINI_BASE_URL'),
                timeout=float(os.getenv('TIMEOUT_SECONDS', '180.0')),
            ),
            mode=self.mode,
        )
        logger.debug("Initialized Gemini service with OpenAI-compatible endpoint")

    @throttle_async_func_call(max_concurrent=int(os.getenv("CONCURRENT_TASK_LIMIT", 1024)), stagger_time=0.001, waiting_time=0.001)
    async def send_message(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        history_messages: list[dict[str, str]] | None = None,
        response_model: Type[T_model] | None = None,
        **kwargs: Any,
    ) -> Tuple[T_model, list[dict[str, str]]]:
        """Send a message to Gemini and receive a response.

        Args:
            prompt (str): The input message to send to the language model.
            model (str): The name of the model to use. Defaults to gemini-2.0-flash.
            system_prompt (str, optional): The system prompt to set the context for the conversation.
            history_messages (list, optional): A list of previous messages in the conversation.
            response_model (Type[T], optional): The Pydantic model to parse the response.
            **kwargs: Additional keyword arguments for the API call.

        Returns:
            Tuple[T_model, list[dict[str, str]]]: The model response and conversation history.
        """
        logger.debug(f"Sending message with prompt: {prompt}")
        model = model or self.model or "gemini-2.0-flash"
        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            logger.debug(f"Added system prompt: {system_prompt}")

        if history_messages:
            messages.extend(history_messages)
            logger.debug(f"Added history messages: {history_messages}")

        messages.append({"role": "user", "content": prompt})

        llm_response: T_model = await self.llm_async_client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore
            response_model=response_model.Model
            if response_model and issubclass(response_model, BaseModelAlias)
            else response_model,
            **kwargs,
            max_retries=AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)),
        )

        if not llm_response:
            logger.error("No response received from Gemini.")
            raise LLMServiceNoResponseError("No response received from Gemini.")

        messages.append(
            {
                "role": "assistant",
                "content": llm_response.model_dump_json() if isinstance(llm_response, BaseModel) else str(llm_response),
            }
        )
        logger.debug(f"Received response: {llm_response}")

        if response_model and issubclass(response_model, BaseModelAlias):
            llm_response = cast(T_model, cast(BaseModelAlias.Model, llm_response).to_dataclass(llm_response))

        return llm_response, messages


@dataclass
class GeminiEmbeddingService(BaseEmbeddingService):
    """Embedding Service for Gemini."""

    embedding_dim: int = field(default=768)  # Gemini's embedding dimension
    max_elements_per_request: int = field(default=32)
    model: Optional[str] = field(default="text-embedding-004")

    def __post_init__(self):
        self.embedding_async_client = AsyncOpenAI(
            api_key=os.getenv('GEMINI_API_KEY_BETA'),
            base_url=os.getenv('GEMINI_BASE_URL'),
        )
        logger.debug("Initialized Gemini embedding service")

    async def encode(self, texts: list[str], model: Optional[str] = None) -> np.ndarray[Any, np.dtype[np.float32]]:
        """Get the embedding representation of the input text.

        Args:
            texts (str): The input text to embed.
            model (str, optional): The name of the model to use.

        Returns:
            np.ndarray: The embedding vectors.
        """
        logger.debug(f"Getting embedding for texts: {texts}")
        model = model or self.model or "text-embedding-004"

        batched_texts = [
            texts[i * self.max_elements_per_request : (i + 1) * self.max_elements_per_request]
            for i in range((len(texts) + self.max_elements_per_request - 1) // self.max_elements_per_request)
        ]
        response = await asyncio.gather(*[self._embedding_request(b, model) for b in batched_texts])

        data = chain(*[r.data for r in response])
        embeddings = np.array([dp.embedding for dp in data])
        logger.debug(f"Received embedding response: {len(embeddings)} embeddings")

        return embeddings

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((RateLimitError, APIConnectionError, TimeoutError)),
    )
    async def _embedding_request(self, input: List[str], model: str) -> Any:
        return await self.embedding_async_client.embeddings.create(model=model, input=input, encoding_format="float")
