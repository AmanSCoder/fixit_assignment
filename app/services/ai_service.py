import logging
import asyncio
from typing import List, AsyncGenerator
import openai
from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.api_key = settings.AZURE_OPENAI_API_KEY
        self.api_version = settings.AZURE_OPENAI_API_VERSION
        self.azure_endpoint = settings.AZURE_OPENAI_ENDPOINT
        self.embedding_deployment = settings.AZURE_EMBEDDING_DEPLOYMENT_NAME
        self.chat_deployment = settings.AZURE_CHAT_MODEL_DEPLOYMENT_NAME

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        try:
            logger.info(
                f"Generating embeddings for {len(texts)} texts using deployment '{self.embedding_deployment}'"
            )
            logger.debug(
                f"Embedding payload: {{'input': {texts}, 'model': {self.embedding_deployment}}}"
            )
            client = openai.AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.azure_endpoint,
            )
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.embeddings.create(
                    input=texts, model=self.embedding_deployment
                ),
            )
            embeddings = [item.embedding for item in response.data]
            logger.info("Successfully generated embeddings.")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise ValueError(f"Failed to generate embeddings: {str(e)}")

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        logger.debug(f"Generating embedding for single text: {text[:30]}...")
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]

    async def generate_answer(self, question: str, context: str) -> str:
        """Generate answer using the Azure OpenAI chat model"""
        try:
            logger.info(
                f"Generating answer for question: '{question}' using deployment '{self.chat_deployment}'"
            )
            prompt = f"""
            Answer the following question based on the provided context. 
            If the answer cannot be found in the context, say "I don't have enough information to answer this question."

            Context:
            {context}

            Question: {question}
            
            Answer:
            """
            payload = {
                "model": self.chat_deployment,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions based on the provided document context.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 500,
            }
            logger.debug(f"Chat completion payload: {payload}")
            client = openai.AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.azure_endpoint,
            )
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: client.chat.completions.create(**payload)
            )
            logger.debug(f"Chat completion response: {response}")
            logger.info("Successfully generated answer.")
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise ValueError(f"Failed to generate answer: {str(e)}")

    async def generate_answer_stream(
        self, question: str, context: str
    ) -> AsyncGenerator[str, None]:
        """Generate streaming answer using the Azure OpenAI chat model"""
        try:
            logger.info(
                f"Generating streaming answer for question: '{question}' using deployment '{self.chat_deployment}'"
            )
            prompt = f"""
            Answer the following question based on the provided context. 
            If the answer cannot be found in the context, say "I don't have enough information to answer this question."

            Context:
            {context}

            Question: {question}
            
            Answer:
            """
            payload = {
                "model": self.chat_deployment,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions based on the provided document context.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 500,
                "stream": True,
            }
            logger.debug(f"Chat completion stream payload: {payload}")
            client = openai.AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.azure_endpoint,
            )
            stream = client.chat.completions.create(**payload)
            logger.debug("Streaming response started.")
            for chunk in stream:
                logger.debug(f"Streaming token chunk: {chunk}")
                if (
                    chunk.choices
                    and chunk.choices[0].delta
                    and chunk.choices[0].delta.content
                ):
                    logger.debug(f"Streaming token: {chunk.choices[0].delta.content}")
                    yield chunk.choices[0].delta.content
            logger.info("Completed streaming answer.")
        except Exception as e:
            logger.error(f"Error generating streaming answer: {e}")
            raise ValueError(f"Failed to generate streaming answer: {str(e)}")


# Create a singleton instance
ai_service = AIService()
