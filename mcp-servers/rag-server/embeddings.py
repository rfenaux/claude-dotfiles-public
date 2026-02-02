#!/usr/bin/env python3
"""
Embedding Provider Chain

Provides fallback chain for embedding generation:
1. Ollama (local, free)
2. OpenAI (cloud, paid)
3. Gemini (cloud, paid)

Part of: OpenClaw-inspired improvements (Phase 2, F08)
Created: 2026-01-30
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result from embedding generation."""
    embeddings: List[List[float]]
    provider: str
    model: str
    dimension: int


class EmbeddingProvider(ABC):
    """Base class for embedding providers."""

    name: str = "base"
    model: str = "unknown"

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available."""
        pass

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        pass


class OllamaProvider(EmbeddingProvider):
    """Local Ollama embeddings (default, free)."""

    name = "ollama"

    def __init__(self, model: str = "mxbai-embed-large", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self._dimension = 1024  # mxbai-embed-large default

    def is_available(self) -> bool:
        try:
            import requests
            r = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if r.status_code != 200:
                return False
            # Check if model is available
            models = r.json().get("models", [])
            return any(m.get("name", "").startswith(self.model.split(":")[0]) for m in models)
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    def embed(self, texts: List[str]) -> List[List[float]]:
        import requests
        embeddings = []
        for text in texts:
            r = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=30
            )
            r.raise_for_status()
            embeddings.append(r.json()["embedding"])
        return embeddings

    def get_dimension(self) -> int:
        return self._dimension


class OpenAIProvider(EmbeddingProvider):
    """OpenAI embeddings (cloud, paid)."""

    name = "openai"

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            # Quick check that key format is valid
            return self.api_key.startswith("sk-") and len(self.api_key) > 20
        except:
            return False

    def embed(self, texts: List[str]) -> List[List[float]]:
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

        client = OpenAI(api_key=self.api_key)
        response = client.embeddings.create(
            input=texts,
            model=self.model
        )
        return [e.embedding for e in response.data]

    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Embed texts in batches for efficiency with large datasets.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call (max 2048 for OpenAI)

        Returns:
            List of embeddings
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

        client = OpenAI(api_key=self.api_key)
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.debug(f"OpenAI batch {i // batch_size + 1}: {len(batch)} texts")
            response = client.embeddings.create(
                input=batch,
                model=self.model
            )
            all_embeddings.extend([e.embedding for e in response.data])

        return all_embeddings

    def get_dimension(self) -> int:
        return self._dimensions.get(self.model, 1536)


class GeminiProvider(EmbeddingProvider):
    """Google Gemini embeddings (cloud, paid)."""

    name = "gemini"

    def __init__(self, model: str = "models/embedding-001"):
        self.model = model
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self._dimension = 768

    def is_available(self) -> bool:
        return bool(self.api_key)

    def embed(self, texts: List[str]) -> List[List[float]]:
        try:
            import google.generativeai as genai
        except ImportError:
            raise RuntimeError("google-generativeai package not installed. Run: pip install google-generativeai")

        genai.configure(api_key=self.api_key)

        embeddings = []
        for text in texts:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])
        return embeddings

    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Embed texts in batches for efficiency.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call

        Returns:
            List of embeddings
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise RuntimeError("google-generativeai package not installed. Run: pip install google-generativeai")

        genai.configure(api_key=self.api_key)
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.debug(f"Gemini batch {i // batch_size + 1}: {len(batch)} texts")

            # Gemini can handle batch in single call
            result = genai.embed_content(
                model=self.model,
                content=batch,
                task_type="retrieval_document"
            )

            # Handle response format (single or batch)
            if isinstance(result['embedding'][0], list):
                all_embeddings.extend(result['embedding'])
            else:
                all_embeddings.append(result['embedding'])

        return all_embeddings

    def get_dimension(self) -> int:
        return self._dimension


class EmbeddingChain:
    """Fallback chain of embedding providers."""

    PROVIDER_CLASSES = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider
    }

    def __init__(self, provider_order: List[str] = None, config: dict = None):
        """
        Initialize with ordered list of provider names.

        Args:
            provider_order: List like ["ollama", "openai", "gemini"]
            config: Optional config dict with provider-specific settings
        """
        provider_names = provider_order or ["ollama", "openai", "gemini"]
        config = config or {}

        self.providers: List[EmbeddingProvider] = []

        for name in provider_names:
            if name not in self.PROVIDER_CLASSES:
                logger.warning(f"Unknown provider: {name}")
                continue

            try:
                provider_config = config.get(name, {})
                provider = self.PROVIDER_CLASSES[name](**provider_config)
                self.providers.append(provider)
                logger.debug(f"Initialized provider: {name}")
            except Exception as e:
                logger.warning(f"Failed to init {name}: {e}")

    def get_available_provider(self) -> Optional[EmbeddingProvider]:
        """Get first available provider."""
        for provider in self.providers:
            if provider.is_available():
                return provider
        return None

    def embed(self, texts: List[str]) -> EmbeddingResult:
        """
        Embed texts using first available provider.

        Raises:
            RuntimeError: If no providers are available
        """
        errors = []

        for provider in self.providers:
            if not provider.is_available():
                logger.debug(f"Provider {provider.name} not available, trying next")
                continue

            try:
                logger.info(f"Using embedding provider: {provider.name}")
                embeddings = provider.embed(texts)
                return EmbeddingResult(
                    embeddings=embeddings,
                    provider=provider.name,
                    model=provider.model,
                    dimension=provider.get_dimension()
                )
            except Exception as e:
                error_msg = f"Provider {provider.name} failed: {e}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue

        error_summary = "; ".join(errors) if errors else "No providers configured"
        raise RuntimeError(
            f"No embedding providers available. {error_summary}. "
            "Ensure Ollama is running or set OPENAI_API_KEY/GOOGLE_API_KEY."
        )

    def embed_batch(self, texts: List[str], batch_size: int = 100) -> EmbeddingResult:
        """
        Embed texts in batches for efficiency.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch

        Returns:
            EmbeddingResult with all embeddings
        """
        if len(texts) <= batch_size:
            return self.embed(texts)

        # Find available provider
        provider = self.get_available_provider()
        if not provider:
            raise RuntimeError("No embedding providers available")

        logger.info(f"Batch embedding {len(texts)} texts with {provider.name}")

        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.debug(f"Processing batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1}")
            embeddings = provider.embed(batch)
            all_embeddings.extend(embeddings)

        return EmbeddingResult(
            embeddings=all_embeddings,
            provider=provider.name,
            model=provider.model,
            dimension=provider.get_dimension()
        )

    def get_status(self) -> dict:
        """Get status of all providers."""
        status = {
            "available": [],
            "unavailable": [],
            "active": None
        }

        for provider in self.providers:
            info = {
                "name": provider.name,
                "model": provider.model,
                "dimension": provider.get_dimension()
            }

            if provider.is_available():
                status["available"].append(info)
                if status["active"] is None:
                    status["active"] = provider.name
            else:
                status["unavailable"].append(info)

        return status


# Module-level singleton
_default_chain: Optional[EmbeddingChain] = None


def get_embedding_chain(config: dict = None) -> EmbeddingChain:
    """Get or create the default embedding chain."""
    global _default_chain
    if _default_chain is None or config is not None:
        _default_chain = EmbeddingChain(config=config)
    return _default_chain


def embed_texts(texts: List[str]) -> EmbeddingResult:
    """Convenience function to embed texts."""
    return get_embedding_chain().embed(texts)


def get_embedding_status() -> dict:
    """Get status of embedding providers."""
    return get_embedding_chain().get_status()


if __name__ == "__main__":
    # CLI for testing
    print("Embedding Provider Status")
    print("=" * 40)

    chain = EmbeddingChain()
    status = chain.get_status()

    print(f"Active provider: {status['active'] or 'None'}")
    print()

    print("Available:")
    for p in status["available"]:
        print(f"  ✓ {p['name']}: {p['model']} ({p['dimension']}d)")

    print()
    print("Unavailable:")
    for p in status["unavailable"]:
        print(f"  ✗ {p['name']}: {p['model']}")

    # Test embedding if available
    if status["active"]:
        print()
        print("Testing embedding...")
        try:
            result = chain.embed(["Hello world"])
            print(f"  ✓ Generated {len(result.embeddings[0])}d embedding with {result.provider}")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
