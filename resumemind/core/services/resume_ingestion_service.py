import hashlib
from pathlib import Path

from markitdown import MarkItDown

from resumemind.core.agents.resume_cleaning_workflow import ResumeCleaningWorkflow
from resumemind.core.agents.resume_graph_extraction_workflow import (
    ResumeGraphExtractionWorkflow,
)
from resumemind.core.providers.config import ProviderConfig
from resumemind.core.services.embedding_service import (
    create_embedding_service_from_provider,
)
from resumemind.core.services.graph_database_service import GraphDatabaseService


async def read_resume(resume_path: str) -> str:
    md = MarkItDown(enable_plugins=True)
    resume_data = md.convert(resume_path)
    return resume_data.markdown


async def process_resume_content(
    resume_content: str, provider_config: ProviderConfig
) -> str:
    resume_cleaner = ResumeCleaningWorkflow(
        model_id=provider_config.model,
        api_key=provider_config.api_key_env,
        base_url=provider_config.base_url,
        additional_params=provider_config.additional_params or {},
    )
    response = await resume_cleaner.run(resume_content)
    if not response.validation_status:
        raise ValueError(response.validation_message)
    return response.formatted_resume


async def extract_resume_graph(formatted_resume: str, provider_config: ProviderConfig):
    """
    Extract graph triplets from formatted resume content with vector embeddings.

    Args:
        formatted_resume: Clean, formatted resume content in markdown
        provider_config: LLM provider configuration

    Returns:
        ResumeGraphExtractionOutput containing triplets, entities, validation info, and embeddings
    """
    # Extract graph structure
    graph_extractor = ResumeGraphExtractionWorkflow(
        model_id=provider_config.model,
        api_key=provider_config.api_key_env,
        base_url=provider_config.base_url,
        additional_params=provider_config.additional_params or {},
    )

    response = await graph_extractor.run(formatted_resume)
    if not response.validation_status:
        raise ValueError(f"Graph extraction failed: {response.validation_message}")

    # Generate vector embeddings
    try:
        embedding_service = create_embedding_service_from_provider(provider_config)
        response_with_embeddings = await embedding_service.embed_graph_data(
            response, formatted_resume
        )
        return response_with_embeddings, embedding_service
    except Exception as e:
        print(f"Warning: Failed to generate embeddings: {e}")
        print("Continuing without embeddings...")
        return response, None


async def store_resume_in_graph_db(
    resume_path: str,
    graph_data,
    graph_db_service: GraphDatabaseService = None,
    embedding_service=None,
) -> bool:
    """
    Store resume graph data in the graph database.

    Args:
        resume_path: Path to the original resume file
        graph_data: ResumeGraphExtractionOutput from the workflow
        graph_db_service: Optional graph database service instance
        embedding_service: Optional embedding service to get embeddings from

    Returns:
        True if successful, False otherwise
    """
    # Generate a unique resume ID based on file path and content hash
    resume_id = generate_resume_id(resume_path)

    # Use provided service or create a new one
    if graph_db_service is None:
        graph_db_service = GraphDatabaseService()

    # Connect to the database
    if not graph_db_service.connect():
        print("Failed to connect to graph database")
        return False

    try:
        # Create indexes for better performance
        await graph_db_service.create_indexes()

        # Get embeddings from embedding service if available
        entity_embeddings = None
        triplet_subject_embeddings = None
        triplet_object_embeddings = None
        triplet_relationship_embeddings = None

        if embedding_service:
            entity_embeddings = getattr(
                embedding_service, "last_entity_embeddings", None
            )
            triplet_subject_embeddings = getattr(
                embedding_service, "last_triplet_subject_embeddings", None
            )
            triplet_object_embeddings = getattr(
                embedding_service, "last_triplet_object_embeddings", None
            )
            triplet_relationship_embeddings = getattr(
                embedding_service, "last_triplet_relationship_embeddings", None
            )

        # Store the resume graph with embeddings
        success = await graph_db_service.store_resume_graph(
            resume_id,
            graph_data,
            entity_embeddings,
            triplet_subject_embeddings,
            triplet_object_embeddings,
            triplet_relationship_embeddings,
        )

        if success:
            print(f"Successfully stored resume graph with ID: {resume_id}")
        else:
            print("Failed to store resume graph")

        return success

    finally:
        await graph_db_service.disconnect()


def generate_resume_id(resume_path: str) -> str:
    """
    Generate a unique ID for a resume based on its file path.

    Args:
        resume_path: Path to the resume file

    Returns:
        Unique resume identifier
    """
    # Use the file name and path to create a consistent ID
    file_path = Path(resume_path)
    path_str = f"{file_path.stem}_{file_path.suffix}_{file_path.stat().st_mtime}"

    # Create a hash for the ID
    resume_hash = hashlib.md5(path_str.encode()).hexdigest()[:12]
    return f"resume_{resume_hash}"


async def complete_resume_ingestion_workflow(
    resume_path: str, provider_config: ProviderConfig
) -> dict:
    """
    Complete end-to-end resume ingestion workflow.

    Args:
        resume_path: Path to the resume file
        provider_config: LLM provider configuration

    Returns:
        Dictionary with workflow results and statistics
    """
    try:
        # Step 1: Read resume
        raw_content = await read_resume(resume_path)

        # Step 2: Clean and format resume
        formatted_content = await process_resume_content(raw_content, provider_config)

        # Step 3: Extract graph relationships
        graph_data, embedding_service = await extract_resume_graph(
            formatted_content, provider_config
        )
        print("Graph Data: ", graph_data)

        # Step 4: Store in graph database
        storage_success = await store_resume_in_graph_db(
            resume_path, graph_data, embedding_service=embedding_service
        )

        # Generate resume ID for reference
        resume_id = generate_resume_id(resume_path)

        return {
            "success": True,
            "resume_id": resume_id,
            "raw_content_length": len(raw_content),
            "formatted_content_length": len(formatted_content),
            "entity_count": len(graph_data.entities),
            "triplet_count": len(graph_data.triplets),
            "graph_stored": storage_success,
            "validation_status": graph_data.validation_status,
            "validation_message": graph_data.validation_message,
            "formatted_content": formatted_content,
            "graph_data": graph_data,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "resume_id": generate_resume_id(resume_path),
        }
