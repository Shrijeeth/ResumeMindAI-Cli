"""
Embedding service for generating vector embeddings for GraphRAG support using LiteLLM
"""

from typing import Dict, List, Optional

import litellm


class EmbeddingService:
    """Service for generating vector embeddings using LiteLLM for multi-provider support"""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        additional_params: Optional[Dict] = None,
    ):
        """
        Initialize the embedding service.

        Args:
            model: Embedding model to use (supports OpenAI, Ollama, etc.)
            api_key: API key for the provider
            base_url: Optional base URL for API calls
            additional_params: Additional parameters for the provider
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.additional_params = additional_params or {}

        # Get model-specific token limit
        token_limits = get_embedding_token_limits()
        self.max_tokens = token_limits.get(model, token_limits["default"])

        # Configure LiteLLM
        if api_key:
            litellm.api_key = api_key
        if base_url:
            litellm.api_base = base_url

    def _chunk_text(self, text: str, max_tokens: Optional[int] = None) -> List[str]:
        """
        Chunk text into smaller pieces that fit within token limits.

        Args:
            text: Text to chunk
            max_tokens: Maximum tokens per chunk (default 7000 to be safe)

        Returns:
            List of text chunks
        """
        # Use model-specific token limit if not provided
        if max_tokens is None:
            max_tokens = int(self.max_tokens * 0.8)  # Use 80% of limit for safety

        # Simple chunking by characters (rough approximation: 1 token ≈ 4 characters)
        max_chars = max_tokens * 4

        if len(text) <= max_chars:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + max_chars

            # Try to break at sentence boundaries
            if end < len(text):
                # Look for sentence endings within the last 500 characters
                search_start = max(start, end - 500)
                sentence_end = -1

                for delimiter in [". ", ".\n", "! ", "!\n", "? ", "?\n"]:
                    pos = text.rfind(delimiter, search_start, end)
                    if pos > sentence_end:
                        sentence_end = pos + len(delimiter)

                if sentence_end > start:
                    end = sentence_end

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end

        return chunks

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate vector embedding for a single text with automatic chunking.

        Args:
            text: Text to embed

        Returns:
            Vector embedding as list of floats (averaged if chunked)
        """
        try:
            # Check if text needs chunking
            chunks = self._chunk_text(text)

            if len(chunks) == 1:
                # Single chunk, process normally
                response = await litellm.aembedding(
                    model=self.model,
                    input=text,
                    api_key=self.api_key,
                    api_base=self.base_url,
                    **self.additional_params,
                )
                return response.data[0]["embedding"]
            else:
                # Multiple chunks, process and average
                print(
                    f"Text too large ({len(text)} chars), chunking into {len(chunks)} pieces"
                )
                chunk_embeddings = []

                for i, chunk in enumerate(chunks):
                    try:
                        response = await litellm.aembedding(
                            model=self.model,
                            input=chunk,
                            api_key=self.api_key,
                            api_base=self.base_url,
                            **self.additional_params,
                        )
                        chunk_embeddings.append(response.data[0]["embedding"])
                        print(f"Processed chunk {i + 1}/{len(chunks)}")
                    except Exception as e:
                        print(f"Failed to embed chunk {i + 1}: {e}")
                        continue

                if not chunk_embeddings:
                    return []

                # Average the embeddings
                avg_embedding = []
                embedding_dim = len(chunk_embeddings[0])

                for dim in range(embedding_dim):
                    avg_value = sum(emb[dim] for emb in chunk_embeddings) / len(
                        chunk_embeddings
                    )
                    avg_embedding.append(avg_value)

                print(f"Averaged {len(chunk_embeddings)} chunk embeddings")
                return avg_embedding

        except Exception as e:
            print(f"Failed to generate embedding for text: {e}")
            return []

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate vector embeddings for multiple texts in batch with chunking support.

        Args:
            texts: List of texts to embed

        Returns:
            List of vector embeddings
        """
        try:
            # Check if any texts need chunking
            needs_chunking = any(len(text) > 28000 for text in texts)  # ~7k tokens

            if not needs_chunking:
                # Process normally if all texts are small enough
                response = await litellm.aembedding(
                    model=self.model,
                    input=texts,
                    api_key=self.api_key,
                    api_base=self.base_url,
                    **self.additional_params,
                )
                return [data["embedding"] for data in response.data]
            else:
                # Process individually with chunking support
                print(
                    f"Some texts are large, processing {len(texts)} texts individually..."
                )
                embeddings = []

                for i, text in enumerate(texts):
                    embedding = await self.generate_embedding(text)
                    embeddings.append(embedding)
                    if (i + 1) % 5 == 0:  # Progress update every 5 texts
                        print(f"Processed {i + 1}/{len(texts)} texts")

                return embeddings

        except Exception as e:
            print(f"Failed to generate batch embeddings: {e}")
            # Fallback to individual processing
            print("Falling back to individual processing...")
            embeddings = []
            for text in texts:
                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)
            return embeddings

    async def embed_graph_data(self, graph_data, resume_content: str):
        """
        Add vector embeddings to graph extraction output.

        Args:
            graph_data: ResumeGraphExtractionOutput object
            resume_content: Original resume content for context

        Returns:
            Updated ResumeGraphExtractionOutput with embeddings
        """
        # Prepare texts for embedding with shorter, focused descriptions
        texts_to_embed = []
        text_mappings = {}  # Maps text index to (type, identifier)

        # Use shorter context to avoid token limits
        # short_context = resume_content[:200] if resume_content else ""

        # Add entity descriptions (keep them concise)
        for entity_name, entity_description in graph_data.entity_descriptions.items():
            # Create focused text for embedding (limit description length)
            description = (
                entity_description[:300] if entity_description else entity_name
            )
            entity_text = f"{entity_name}: {description}"
            texts_to_embed.append(entity_text)
            text_mappings[len(texts_to_embed) - 1] = ("entity", entity_name)

        # Add triplet descriptions (more concise)
        for i, triplet in enumerate(graph_data.triplets):
            # Subject description (concise)
            subject_desc = (
                triplet.subject_description[:200]
                if triplet.subject_description
                else triplet.subject
            )
            subject_text = f"{triplet.subject} ({triplet.subject_type}): {subject_desc}"
            texts_to_embed.append(subject_text)
            text_mappings[len(texts_to_embed) - 1] = ("triplet_subject", i)

            # Object description (concise)
            object_desc = (
                triplet.object_description[:200]
                if triplet.object_description
                else triplet.object
            )
            object_text = f"{triplet.object} ({triplet.object_type}): {object_desc}"
            texts_to_embed.append(object_text)
            text_mappings[len(texts_to_embed) - 1] = ("triplet_object", i)

            # Relationship description (concise)
            rel_desc = (
                triplet.relationship_description[:300]
                if triplet.relationship_description
                else f"{triplet.subject} {triplet.predicate} {triplet.object}"
            )
            relationship_text = f"{triplet.predicate}: {rel_desc}"
            texts_to_embed.append(relationship_text)
            text_mappings[len(texts_to_embed) - 1] = ("triplet_relationship", i)

        # Generate embeddings in batch
        embeddings = await self.generate_embeddings_batch(texts_to_embed)

        # Create separate embedding dictionaries (don't modify graph_data)
        entity_embeddings = {}
        triplet_subject_embeddings = {}
        triplet_object_embeddings = {}
        triplet_relationship_embeddings = {}

        for idx, embedding in enumerate(embeddings):
            if idx in text_mappings:
                mapping_type, mapping_id = text_mappings[idx]

                if mapping_type == "entity":
                    entity_embeddings[mapping_id] = embedding
                elif mapping_type == "triplet_subject":
                    triplet_subject_embeddings[mapping_id] = embedding
                elif mapping_type == "triplet_object":
                    triplet_object_embeddings[mapping_id] = embedding
                elif mapping_type == "triplet_relationship":
                    triplet_relationship_embeddings[mapping_id] = embedding

        # Store embeddings separately for use by graph database
        # Don't modify the original graph_data structure
        self.last_entity_embeddings = entity_embeddings
        self.last_triplet_subject_embeddings = triplet_subject_embeddings
        self.last_triplet_object_embeddings = triplet_object_embeddings
        self.last_triplet_relationship_embeddings = triplet_relationship_embeddings

        return graph_data

    async def find_similar_entities(
        self, query_text: str, entity_embeddings: Dict[str, List[float]], top_k: int = 5
    ) -> List[tuple]:
        """
        Find entities similar to a query text using cosine similarity.

        Args:
            query_text: Text to search for
            entity_embeddings: Dictionary of entity names to embeddings
            top_k: Number of top results to return

        Returns:
            List of (entity_name, similarity_score) tuples
        """
        query_embedding = await self.generate_embedding(query_text)
        if not query_embedding:
            return []

        similarities = []
        for entity_name, embedding in entity_embeddings.items():
            if embedding:
                similarity = self._cosine_similarity(query_embedding, embedding)
                similarities.append((entity_name, similarity))

        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0

        return dot_product / (magnitude1 * magnitude2)


# Utility function to create embedding service from provider config
def create_embedding_service_from_provider(provider_config) -> EmbeddingService:
    """
    Create an embedding service from provider configuration.

    Args:
        provider_config: ProviderConfig object

    Returns:
        EmbeddingService instance
    """
    import os

    # Use embedding-specific configuration if available, otherwise fallback to main config
    embedding_model = provider_config.embedding_model
    embedding_api_key_env = provider_config.embedding_api_key_env
    embedding_base_url = provider_config.embedding_base_url
    embedding_additional_params = provider_config.embedding_additional_params or {}

    # Fallback to main provider config if embedding config not specified
    if not embedding_model:
        # Auto-select embedding model based on main provider
        if (
            "openai" in provider_config.model.lower()
            or provider_config.model.startswith("gpt")
        ):
            embedding_model = "text-embedding-3-small"
        elif (
            "ollama" in provider_config.model.lower()
            or provider_config.model.startswith("ollama/")
        ):
            embedding_model = (
                "ollama/nomic-embed-text"  # Popular Ollama embedding model
            )
        elif "gemini" in provider_config.model.lower():
            embedding_model = (
                "text-embedding-004"  # Google's embedding model via LiteLLM
            )
        elif "claude" in provider_config.model.lower():
            # Anthropic doesn't have embeddings, fallback to OpenAI
            embedding_model = "text-embedding-3-small"
        else:
            # Default fallback
            embedding_model = "text-embedding-3-small"

    if not embedding_api_key_env:
        embedding_api_key_env = provider_config.api_key_env

    if not embedding_base_url:
        embedding_base_url = provider_config.base_url

    # Extract API key from environment variable
    api_key = None
    if embedding_api_key_env:
        api_key = os.getenv(embedding_api_key_env)

    return EmbeddingService(
        model=embedding_model,
        api_key=api_key,
        base_url=embedding_base_url,
        additional_params=embedding_additional_params,
    )


def get_default_embedding_models() -> Dict[str, str]:
    """
    Get default embedding models for different providers.

    Returns:
        Dictionary mapping provider types to default embedding models
    """
    return {
        "openai": "text-embedding-3-small",
        "ollama": "ollama/nomic-embed-text",
        "gemini": "text-embedding-004",
        "claude": "text-embedding-3-small",  # Fallback to OpenAI
        "custom": "text-embedding-3-small",  # Default fallback
    }


def get_embedding_token_limits() -> Dict[str, int]:
    """
    Get token limits for different embedding models.

    Returns:
        Dictionary mapping model names to their token limits
    """
    return {
        # OpenAI models
        "text-embedding-3-small": 8191,
        "text-embedding-3-large": 8191,
        "text-embedding-ada-002": 8191,
        # Google models
        "text-embedding-004": 8000,  # Conservative limit for Gemini
        "text-embedding-gecko-001": 8000,
        # Ollama models (generally more flexible)
        "ollama/nomic-embed-text": 8192,
        "ollama/mxbai-embed-large": 8192,
        "ollama/all-minilm": 8192,
        # Default fallback
        "default": 7000,  # Conservative default
    }
