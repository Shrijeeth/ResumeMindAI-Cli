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

        # Configure LiteLLM
        if api_key:
            litellm.api_key = api_key
        if base_url:
            litellm.api_base = base_url

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate vector embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Vector embedding as list of floats
        """
        try:
            response = await litellm.aembedding(
                model=self.model,
                input=text,
                api_key=self.api_key,
                api_base=self.base_url,
                **self.additional_params,
            )
            return response.data[0]["embedding"]
        except Exception as e:
            print(f"Failed to generate embedding for text: {e}")
            return []

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate vector embeddings for multiple texts in batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of vector embeddings
        """
        try:
            response = await litellm.aembedding(
                model=self.model,
                input=texts,
                api_key=self.api_key,
                api_base=self.base_url,
                **self.additional_params,
            )
            return [data["embedding"] for data in response.data]
        except Exception as e:
            print(f"Failed to generate batch embeddings: {e}")
            return [[] for _ in texts]

    async def embed_graph_data(self, graph_data, resume_content: str):
        """
        Add vector embeddings to graph extraction output.

        Args:
            graph_data: ResumeGraphExtractionOutput object
            resume_content: Original resume content for context

        Returns:
            Updated ResumeGraphExtractionOutput with embeddings
        """
        # Collect all texts to embed
        texts_to_embed = []
        text_mappings = {}

        # Add entity descriptions
        entity_texts = []
        for entity_name, description in graph_data.entity_descriptions.items():
            full_text = f"Entity: {entity_name}\nType: {graph_data.entities[entity_name]}\nDescription: {description}\nContext: {resume_content[:500]}"
            entity_texts.append(full_text)
            texts_to_embed.append(full_text)
            text_mappings[len(texts_to_embed) - 1] = ("entity", entity_name)

        # Add triplet descriptions
        for i, triplet in enumerate(graph_data.triplets):
            # Subject description
            subject_text = f"Entity: {triplet.subject}\nType: {triplet.subject_type}\nDescription: {triplet.subject_description}\nContext: {resume_content[:500]}"
            texts_to_embed.append(subject_text)
            text_mappings[len(texts_to_embed) - 1] = ("triplet_subject", i)

            # Object description
            object_text = f"Entity: {triplet.object}\nType: {triplet.object_type}\nDescription: {triplet.object_description}\nContext: {resume_content[:500]}"
            texts_to_embed.append(object_text)
            text_mappings[len(texts_to_embed) - 1] = ("triplet_object", i)

            # Relationship description
            relationship_text = f"Relationship: {triplet.predicate}\nSubject: {triplet.subject} ({triplet.subject_type})\nObject: {triplet.object} ({triplet.object_type})\nDescription: {triplet.relationship_description}\nContext: {resume_content[:500]}"
            texts_to_embed.append(relationship_text)
            text_mappings[len(texts_to_embed) - 1] = ("triplet_relationship", i)

        # Generate embeddings in batch
        embeddings = await self.generate_embeddings_batch(texts_to_embed)

        # Map embeddings back to entities and triplets
        entity_embeddings = {}
        for idx, embedding in enumerate(embeddings):
            if idx in text_mappings:
                mapping_type, mapping_id = text_mappings[idx]

                if mapping_type == "entity":
                    entity_embeddings[mapping_id] = embedding
                elif mapping_type == "triplet_subject":
                    graph_data.triplets[mapping_id].subject_embedding = embedding
                elif mapping_type == "triplet_object":
                    graph_data.triplets[mapping_id].object_embedding = embedding
                elif mapping_type == "triplet_relationship":
                    graph_data.triplets[mapping_id].relationship_embedding = embedding

        # Update the graph data with embeddings
        graph_data.entity_embeddings = entity_embeddings

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
