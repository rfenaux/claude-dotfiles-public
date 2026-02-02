"""Ollama embeddings client for local embedding generation."""
import httpx
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class OllamaEmbeddings:
    """Client for generating embeddings via local Ollama server."""

    # Model dimensions mapping
    MODEL_DIMENSIONS = {
        "nomic-embed-text": 768,
        "mxbai-embed-large": 1024,
        "all-minilm": 384,
        "snowflake-arctic-embed": 1024,
    }

    def __init__(
        self,
        model: str = "mxbai-embed-large",
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
    ):
        """Initialize Ollama embeddings client.

        Args:
            model: Ollama embedding model name
            base_url: Ollama server URL
            timeout: Request timeout in seconds
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None
        self._quick_client: Optional[httpx.Client] = None  # For fast availability checks

    @property
    def client(self) -> httpx.Client:
        """Lazy-initialize HTTP client for embeddings (longer timeout, fast connect)."""
        if self._client is None:
            # Long read timeout for embedding generation, but short connect timeout
            self._client = httpx.Client(
                timeout=httpx.Timeout(self.timeout, connect=2.0)
            )
        return self._client

    @property
    def quick_client(self) -> httpx.Client:
        """Lazy-initialize HTTP client for quick checks (2 second timeout)."""
        if self._quick_client is None:
            # Very short timeout: 1s connect, 2s total - fail fast if Ollama not running
            self._quick_client = httpx.Client(
                timeout=httpx.Timeout(2.0, connect=1.0)
            )
        return self._quick_client

    @property
    def dimension(self) -> int:
        """Return embedding dimension for the current model."""
        return self.MODEL_DIMENSIONS.get(self.model, 768)

    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = self.client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except httpx.HTTPError as e:
            logger.error(f"Ollama embedding request failed: {e}")
            raise RuntimeError(f"Failed to generate embedding: {e}") from e

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        return [self.embed(text) for text in texts]

    def is_available(self, auto_start: bool = True) -> bool:
        """Check if Ollama server is available (fast, 2s timeout).

        Args:
            auto_start: If True and Ollama not running, attempt to start it
        """
        try:
            response = self.quick_client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException):
            if auto_start:
                self._try_start_ollama()
                # Check again after starting
                try:
                    import time
                    time.sleep(2)  # Give Ollama time to start
                    response = self.quick_client.get(f"{self.base_url}/api/tags")
                    return response.status_code == 200
                except:
                    pass
            return False

    def _try_start_ollama(self):
        """Attempt to start Ollama via brew services."""
        import subprocess
        try:
            subprocess.run(
                ["brew", "services", "start", "ollama"],
                capture_output=True,
                timeout=10
            )
            logger.info("Started Ollama via brew services")
        except Exception as e:
            logger.warning(f"Could not auto-start Ollama: {e}")

    def ensure_model(self) -> bool:
        """Check if the embedding model is available (fast, 2s timeout)."""
        try:
            response = self.quick_client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                return False
            models = response.json().get("models", [])
            return any(m.get("name", "").startswith(self.model) for m in models)
        except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException):
            return False

    def close(self):
        """Close the HTTP clients."""
        if self._client is not None:
            self._client.close()
            self._client = None
        if self._quick_client is not None:
            self._quick_client.close()
            self._quick_client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
