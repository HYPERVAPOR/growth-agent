"""
LLM client for content evaluation and blog generation.

This module provides integration with OpenRouter API for AI-powered content operations.
"""

import json
import logging
from typing import Any

from openai import OpenAI, Stream
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from growth_agent.config import Settings
from growth_agent.core.prompts import PromptLoader
from growth_agent.core.schema import ContentEvaluation

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for LLM operations using OpenRouter API.

    Supports structured output for content evaluation and text generation for blogs.
    """

    def __init__(self, settings: Settings):
        """
        Initialize LLM client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
        self.prompt_loader = PromptLoader(settings.prompts_dir)

    def _create_chat_completion(
        self,
        messages: list[ChatCompletionMessageParam],
        response_format: type | None = None,
        max_retries: int = 3,
    ) -> Any:
        """
        Create chat completion with retry logic.

        Args:
            messages: Chat messages
            response_format: Optional response format for structured output
            max_retries: Maximum number of retries

        Returns:
            Chat completion response

        Raises:
            Exception: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                kwargs: dict[str, Any] = {
                    "model": self.settings.llm_model,
                    "messages": messages,
                    "temperature": self.settings.llm_temperature,
                    "max_tokens": self.settings.llm_max_tokens,
                }

                if response_format is not None:
                    kwargs["response_format"] = response_format

                response = self.client.chat.completions.create(**kwargs)
                return response

            except Exception as e:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise

    def evaluate_content(self, content: str, author: str, source: str) -> ContentEvaluation:
        """
        Evaluate content quality using LLM.

        Args:
            content: Content text to evaluate
            author: Content author name
            source: Content source (x/rss)

        Returns:
            ContentEvaluation with score, summary, and comment
        """
        try:
            # Load prompts from files
            system_prompt = self.prompt_loader.load("content_evaluation")
            user_prompt = self.prompt_loader.load(
                "content_evaluation_user",
                author=author,
                source=source.upper(),
                content=content,
            )
        except FileNotFoundError:
            # Fallback to default prompts if files not found
            logger.warning("Prompt files not found, using default prompts")
            system_prompt = self.prompt_loader.load("content_evaluation")
            user_prompt = f"Analyze this content from {author} ({source.upper()}):\n\n{content}\n\nProvide your evaluation in the required JSON format."

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self._create_chat_completion(
                messages,
                response_format={"type": "json_object"},
            )

            # Parse response
            content_text = response.choices[0].message.content or "{}"
            result_data = json.loads(content_text)

            # Validate with Pydantic
            evaluation = ContentEvaluation(**result_data)
            logger.info(f"Evaluated content: score={evaluation.score}, author={author}")
            return evaluation

        except Exception as e:
            logger.error(f"Content evaluation failed: {e}")
            # Return default evaluation on error
            return ContentEvaluation(
                score=50,
                summary="Evaluation failed - unable to summarize",
                comment="Evaluation error - manual review required",
            )

    def generate_blog(
        self,
        curated_items: list[dict],
        context: str = "AI and technology insights for business growth",
    ) -> str:
        """
        Generate blog post from curated content.

        Args:
            curated_items: List of curated items with summaries and comments
            context: Company/product context for the blog

        Returns:
            Blog post content with YAML frontmatter
        """
        # Build content summaries
        content_blocks = []
        for idx, item in enumerate(curated_items, 1):
            block = f"""
**Source #{idx}**
- Author: {item.get('author_name', 'Unknown')}
- URL: {item.get('url', 'N/A')}
- Score: {item['score']}/100
- Summary: {item['summary']}
- Value: {item['comment']}
"""
            content_blocks.append(block)

        try:
            # Load prompts from files
            system_prompt = self.prompt_loader.load(
                "blog_generation",
                context=context,
            )
            user_prompt = self.prompt_loader.load(
                "blog_generation_user",
                content_blocks="".join(content_blocks),
            )
        except FileNotFoundError:
            # Fallback to default prompts if files not found
            logger.warning("Blog generation prompt files not found, using default prompts")
            system_prompt = f"You are a tech content writer...\n\nCONTEXT:\n{context}\n\nREQUIREMENTS:\n- Write clear, engaging content\n- 800-1500 words"
            user_prompt = f"Based on the following curated content:\n\n{''.join(content_blocks)}\n\nGenerate a blog post."

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self._create_chat_completion(messages)
            content = response.choices[0].message.content or ""
            logger.info(f"Generated blog post: {len(content)} characters")
            return content

        except Exception as e:
            logger.error(f"Blog generation failed: {e}")
            raise

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for semantic search.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            # Use OpenRouter's embedding model
            response = self.client.embeddings.create(
                model="openai/text-embedding-3-small", input=texts
            )

            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
