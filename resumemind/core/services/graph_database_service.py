"""
Graph database service for storing and querying resume knowledge graphs using FalkorDB with vector support
"""

import json
from typing import Dict, List, Optional

from falkordb.asyncio import FalkorDB

from resumemind.core.agents.resume_graph_extraction_workflow import (
    ResumeGraphExtractionOutput,
)


class GraphDatabaseService:
    """Service for managing resume knowledge graphs in FalkorDB"""

    def __init__(
        self, host: str = "localhost", port: int = 6389, db_name: str = "resumemind"
    ):
        """
        Initialize the graph database service.

        Args:
            host: Redis/FalkorDB host
            port: Redis/FalkorDB port
            db_name: Name of the graph database
        """
        self.host = host
        self.port = port
        self.db_name = db_name
        self.db = None
        self.graph = None

    def connect(self):
        """Connect to FalkorDB"""
        try:
            self.db = FalkorDB(host=self.host, port=self.port)
            self.graph = self.db.select_graph(self.db_name)
            return True
        except Exception as e:
            print(f"Failed to connect to FalkorDB: {e}")
            return False

    async def disconnect(self):
        """Disconnect from FalkorDB"""
        if self.db:
            await self.db.connection.close()
            self.db = None
            self.graph = None

    async def create_indexes(self):
        """Create indexes for better query performance"""
        if not self.graph:
            return False

        try:
            # Create indexes on commonly queried properties
            index_queries = [
                "CREATE INDEX FOR (p:Person) ON (p.name)",
                "CREATE INDEX FOR (c:Company) ON (c.name)",
                "CREATE INDEX FOR (s:Skill) ON (s.name)",
                "CREATE INDEX FOR (t:Technology) ON (t.name)",
                "CREATE INDEX FOR (pos:Position) ON (pos.title)",
                "CREATE INDEX FOR (proj:Project) ON (proj.name)",
            ]

            for query in index_queries:
                try:
                    await self.graph.query(query)
                except Exception:
                    # Index might already exist, continue
                    pass

            return True
        except Exception as e:
            print(f"Failed to create indexes: {e}")
            return False

    async def store_resume_graph(
        self,
        resume_id: str,
        graph_data: ResumeGraphExtractionOutput,
        triplet_subject_embeddings: Optional[Dict[int, List[float]]] = None,
        triplet_object_embeddings: Optional[Dict[int, List[float]]] = None,
        triplet_relationship_embeddings: Optional[Dict[int, List[float]]] = None,
    ) -> bool:
        """
        Store resume graph data in FalkorDB.

        Args:
            resume_id: Unique identifier for the resume
            graph_data: Extracted graph data from the workflow
            triplet_subject_embeddings: Optional embeddings for triplet subjects
            triplet_object_embeddings: Optional embeddings for triplet objects
            triplet_relationship_embeddings: Optional embeddings for relationships

        Returns:
            True if successful, False otherwise
        """
        if not self.graph:
            return False

        try:
            # Extract unique entities from triplets
            entities = {}
            for i, triplet in enumerate(graph_data.triplets):
                # Add subject entity
                entities[triplet.subject] = {
                    "type": triplet.subject_type,
                    "description": triplet.subject_description,
                    "embedding_idx": i,  # Use triplet index for subject embedding
                }
                # Add object entity
                entities[triplet.object] = {
                    "type": triplet.object_type,
                    "description": triplet.object_description,
                    "embedding_idx": i,  # Use triplet index for object embedding
                }

            # Create all entities as nodes with embeddings and descriptions
            entity_queries = []
            for entity_name, entity_data in entities.items():
                # Escape quotes and special characters
                safe_name = entity_name.replace("'", "\\'").replace('"', '\\"')
                safe_type = entity_data["type"].replace("'", "\\'").replace('"', '\\"')
                safe_description = (
                    entity_data["description"].replace("'", "\\'").replace('"', '\\"')
                )

                # Escape entity type for use as Cypher label (handle spaces and special chars)
                safe_label = f"`{entity_data['type'].replace('`', '``')}`"

                # Get embedding based on whether this entity is a subject or object
                embedding_json = "null"
                embedding_idx = entity_data["embedding_idx"]

                # Try subject embedding first, then object embedding
                if (
                    triplet_subject_embeddings
                    and embedding_idx in triplet_subject_embeddings
                ):
                    embedding = triplet_subject_embeddings[embedding_idx]
                    if embedding:
                        embedding_json = f"'{json.dumps(embedding)}'"
                elif (
                    triplet_object_embeddings
                    and embedding_idx in triplet_object_embeddings
                ):
                    embedding = triplet_object_embeddings[embedding_idx]
                    if embedding:
                        embedding_json = f"'{json.dumps(embedding)}'"

                query = f"""
                MERGE (e:{safe_label} {{
                    name: '{safe_name}',
                    type: '{safe_type}',
                    resume_id: '{resume_id}',
                    description: '{safe_description}',
                    embedding: {embedding_json}
                }})
                """
                entity_queries.append(query)

            # Execute entity creation queries
            for query in entity_queries:
                await self.graph.query(query)

            # Create relationships between entities with embeddings and descriptions
            relationship_queries = []
            for i, triplet in enumerate(graph_data.triplets):
                # Escape quotes and special characters
                safe_subject = triplet.subject.replace("'", "\\'").replace('"', '\\"')
                safe_object = triplet.object.replace("'", "\\'").replace('"', '\\"')
                safe_predicate = triplet.predicate.replace("'", "\\'").replace(
                    '"', '\\"'
                )

                # Escape entity types for use as Cypher labels
                safe_subject_label = f"`{triplet.subject_type.replace('`', '``')}`"
                safe_object_label = f"`{triplet.object_type.replace('`', '``')}`"

                # Get relationship description and embedding
                rel_description = triplet.relationship_description.replace(
                    "'", "\\'"
                ).replace('"', '\\"')

                # Serialize relationship embedding
                rel_embedding_json = "null"
                if (
                    triplet_relationship_embeddings
                    and i in triplet_relationship_embeddings
                ):
                    embedding = triplet_relationship_embeddings[i]
                    if embedding:
                        rel_embedding_json = f"'{json.dumps(embedding)}'"

                query = f"""
                MATCH (s:{safe_subject_label} {{name: '{safe_subject}', resume_id: '{resume_id}'}})
                MATCH (o:{safe_object_label} {{name: '{safe_object}', resume_id: '{resume_id}'}})
                MERGE (s)-[r:{safe_predicate} {{
                    resume_id: '{resume_id}',
                    description: '{rel_description}',
                    embedding: {rel_embedding_json}
                }}]->(o)
                """
                relationship_queries.append(query)

            # Execute relationship creation queries
            for query in relationship_queries:
                await self.graph.query(query)

            # Store metadata about the resume
            safe_validation_message = graph_data.validation_message.replace(
                "'", "\\'"
            ).replace('"', '\\"')
            metadata_query = f"""
            MERGE (r:Resume {{
                id: '{resume_id}',
                entity_count: {len(entities)},
                triplet_count: {len(graph_data.triplets)},
                validation_status: {str(graph_data.validation_status).lower()},
                validation_message: '{safe_validation_message}'
            }})
            """
            await self.graph.query(metadata_query)

            return True

        except Exception as e:
            print(f"Failed to store resume graph: {e}")
            return False

    async def get_resume_entities(
        self, resume_id: str, entity_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all entities for a specific resume.

        Args:
            resume_id: Resume identifier
            entity_type: Optional filter by entity type

        Returns:
            List of entity dictionaries
        """
        if not self.graph:
            return []

        try:
            if entity_type:
                safe_entity_label = f"`{entity_type.replace('`', '``')}`"
                query = f"MATCH (e:{safe_entity_label} {{resume_id: '{resume_id}'}}) RETURN e"
            else:
                query = f"MATCH (e {{resume_id: '{resume_id}'}}) RETURN e"

            result = await self.graph.query(query)
            entities = []

            for record in result.result_set:
                entity = record[0]
                entities.append(
                    {
                        "name": entity.properties.get("name", ""),
                        "type": entity.properties.get("type", ""),
                        "labels": list(entity.labels),
                    }
                )

            return entities

        except Exception as e:
            print(f"Failed to get resume entities: {e}")
            return []

    async def get_resume_relationships(self, resume_id: str) -> List[Dict]:
        """
        Get all relationships for a specific resume.

        Args:
            resume_id: Resume identifier

        Returns:
            List of relationship dictionaries
        """
        if not self.graph:
            return []

        try:
            query = f"""
            MATCH (s)-[r {{resume_id: '{resume_id}'}}]->(o)
            RETURN s.name as subject, type(r) as predicate, o.name as object, 
                   labels(s) as subject_type, labels(o) as object_type
            """

            result = await self.graph.query(query)
            relationships = []

            for record in result.result_set:
                relationships.append(
                    {
                        "subject": record[0],
                        "predicate": record[1],
                        "object": record[2],
                        "subject_type": record[3][0] if record[3] else "",
                        "object_type": record[4][0] if record[4] else "",
                    }
                )

            return relationships

        except Exception as e:
            print(f"Failed to get resume relationships: {e}")
            return []

    async def find_candidates_with_skill(self, skill_name: str) -> List[Dict]:
        """
        Find all candidates who have a specific skill.

        Args:
            skill_name: Name of the skill to search for

        Returns:
            List of candidate dictionaries with their resume IDs
        """
        if not self.graph:
            return []

        try:
            safe_skill = skill_name.replace("'", "\\'").replace('"', '\\"')
            query = f"""
            MATCH (p:Person)-[:HAS_SKILL]->(s:Skill {{name: '{safe_skill}'}})
            RETURN DISTINCT p.name as person, p.resume_id as resume_id
            """

            result = await self.graph.query(query)
            candidates = []

            for record in result.result_set:
                candidates.append({"name": record[0], "resume_id": record[1]})

            return candidates

        except Exception as e:
            print(f"Failed to find candidates with skill: {e}")
            return []

    async def find_candidates_by_company(self, company_name: str) -> List[Dict]:
        """
        Find all candidates who worked at a specific company.

        Args:
            company_name: Name of the company

        Returns:
            List of candidate dictionaries
        """
        if not self.graph:
            return []

        try:
            safe_company = company_name.replace("'", "\\'").replace('"', '\\"')
            query = f"""
            MATCH (p:Person)-[:WORKED_AT]->(c:Company {{name: '{safe_company}'}})
            RETURN DISTINCT p.name as person, p.resume_id as resume_id
            """

            result = await self.graph.query(query)
            candidates = []

            for record in result.result_set:
                candidates.append({"name": record[0], "resume_id": record[1]})

            return candidates

        except Exception as e:
            print(f"Failed to find candidates by company: {e}")
            return []

    async def get_skill_cooccurrence(self, skill_name: str) -> List[Dict]:
        """
        Find skills that frequently appear together with a given skill.

        Args:
            skill_name: Name of the skill

        Returns:
            List of related skills with co-occurrence counts
        """
        if not self.graph:
            return []

        try:
            safe_skill = skill_name.replace("'", "\\'").replace('"', '\\"')
            query = f"""
            MATCH (p:Person)-[:HAS_SKILL]->(s1:Skill {{name: '{safe_skill}'}})
            MATCH (p)-[:HAS_SKILL]->(s2:Skill)
            WHERE s1 <> s2
            RETURN s2.name as skill, count(*) as frequency
            ORDER BY frequency DESC
            LIMIT 10
            """

            result = await self.graph.query(query)
            related_skills = []

            for record in result.result_set:
                related_skills.append({"skill": record[0], "frequency": record[1]})

            return related_skills

        except Exception as e:
            print(f"Failed to get skill co-occurrence: {e}")
            return []

    async def delete_resume_graph(self, resume_id: str) -> bool:
        """
        Delete all graph data for a specific resume.

        Args:
            resume_id: Resume identifier

        Returns:
            True if successful, False otherwise
        """
        if not self.graph:
            return False

        try:
            # Delete all nodes and relationships for this resume
            query = f"""
            MATCH (n {{resume_id: '{resume_id}'}})
            DETACH DELETE n
            """
            await self.graph.query(query)

            # Delete resume metadata
            metadata_query = f"MATCH (r:Resume {{id: '{resume_id}'}}) DELETE r"
            await self.graph.query(metadata_query)

            return True

        except Exception as e:
            print(f"Failed to delete resume graph: {e}")
            return False

    async def find_similar_entities_by_embedding(
        self,
        query_embedding: List[float],
        entity_type: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Find entities similar to a query embedding using cosine similarity.

        Args:
            query_embedding: Query vector embedding
            entity_type: Optional filter by entity type
            top_k: Number of top results to return

        Returns:
            List of similar entities with similarity scores
        """
        if not self.graph or not query_embedding:
            return []

        try:
            # Build query based on entity type filter
            if entity_type:
                safe_entity_label = f"`{entity_type.replace('`', '``')}`"
                query = f"MATCH (e:{safe_entity_label}) WHERE e.embedding IS NOT NULL RETURN e"
            else:
                query = "MATCH (e) WHERE e.embedding IS NOT NULL RETURN e"

            result = await self.graph.query(query)
            similarities = []

            for record in result.result_set:
                entity = record[0]
                entity_embedding_str = entity.properties.get("embedding")

                if entity_embedding_str and entity_embedding_str != "null":
                    try:
                        entity_embedding = json.loads(entity_embedding_str)
                        similarity = self._cosine_similarity(
                            query_embedding, entity_embedding
                        )

                        similarities.append(
                            {
                                "name": entity.properties.get("name", ""),
                                "type": entity.properties.get("type", ""),
                                "description": entity.properties.get("description", ""),
                                "resume_id": entity.properties.get("resume_id", ""),
                                "similarity": similarity,
                                "labels": list(entity.labels),
                            }
                        )
                    except json.JSONDecodeError:
                        continue

            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:top_k]

        except Exception as e:
            print(f"Failed to find similar entities: {e}")
            return []

    async def find_similar_relationships_by_embedding(
        self,
        query_embedding: List[float],
        relationship_type: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Find relationships similar to a query embedding using cosine similarity.

        Args:
            query_embedding: Query vector embedding
            relationship_type: Optional filter by relationship type
            top_k: Number of top results to return

        Returns:
            List of similar relationships with similarity scores
        """
        if not self.graph or not query_embedding:
            return []

        try:
            # Build query based on relationship type filter
            if relationship_type:
                query = f"""
                MATCH (s)-[r:{relationship_type}]->(o)
                WHERE r.embedding IS NOT NULL
                RETURN s.name as subject, type(r) as predicate, o.name as object,
                       r.description as description, r.embedding as embedding,
                       labels(s) as subject_type, labels(o) as object_type
                """
            else:
                query = """
                MATCH (s)-[r]->(o)
                WHERE r.embedding IS NOT NULL
                RETURN s.name as subject, type(r) as predicate, o.name as object,
                       r.description as description, r.embedding as embedding,
                       labels(s) as subject_type, labels(o) as object_type
                """

            result = await self.graph.query(query)
            similarities = []

            for record in result.result_set:
                embedding_str = record[4]  # r.embedding

                if embedding_str and embedding_str != "null":
                    try:
                        relationship_embedding = json.loads(embedding_str)
                        similarity = self._cosine_similarity(
                            query_embedding, relationship_embedding
                        )

                        similarities.append(
                            {
                                "subject": record[0],
                                "predicate": record[1],
                                "object": record[2],
                                "description": record[3],
                                "subject_type": record[5][0] if record[5] else "",
                                "object_type": record[6][0] if record[6] else "",
                                "similarity": similarity,
                            }
                        )
                    except json.JSONDecodeError:
                        continue

            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:top_k]

        except Exception as e:
            print(f"Failed to find similar relationships: {e}")
            return []

    async def semantic_search(
        self, query_embedding: List[float], search_type: str = "both", top_k: int = 10
    ) -> Dict[str, List[Dict]]:
        """
        Perform semantic search across entities and relationships.

        Args:
            query_embedding: Query vector embedding
            search_type: Type of search ("entities", "relationships", or "both")
            top_k: Number of top results to return for each type

        Returns:
            Dictionary with entities and relationships results
        """
        results = {"entities": [], "relationships": []}

        if search_type in ["entities", "both"]:
            results["entities"] = await self.find_similar_entities_by_embedding(
                query_embedding, top_k=top_k
            )

        if search_type in ["relationships", "both"]:
            results[
                "relationships"
            ] = await self.find_similar_relationships_by_embedding(
                query_embedding, top_k=top_k
            )

        return results

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math

        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    async def search_resume_by_query(
        self,
        resume_id: str,
        query: str,
        limit: int = 10,
        embedding_service=None,
    ) -> List[Dict]:
        """
        Search a specific resume using natural language query.

        Args:
            resume_id: ID of the resume to search
            query: Natural language search query
            limit: Maximum number of results to return
            embedding_service: Optional EmbeddingService instance

        Returns:
            List of relevant triplets with descriptions
        """
        if not self.graph:
            return []

        try:
            # Generate embedding for the query
            if embedding_service:
                query_embedding = await embedding_service.generate_embedding(query)
            else:
                # Fallback to default (should not happen in normal flow)
                from ..services.embedding_service import EmbeddingService

                default_embedder = EmbeddingService()
                query_embedding = await default_embedder.generate_embedding(query)

            if not query_embedding:
                return []

            # Query for triplets with embeddings for this resume
            cypher_query = """
            MATCH (s)-[r]->(o)
            WHERE s.resume_id = $resume_id
            AND (s.embedding IS NOT NULL OR r.embedding IS NOT NULL OR o.embedding IS NOT NULL)
            RETURN s.name as subject,
                   type(r) as predicate,
                   o.name as object,
                   s.description as subject_description,
                   o.description as object_description,
                   r.description as relationship_description,
                   s.embedding as subject_embedding,
                   o.embedding as object_embedding,
                   r.embedding as relationship_embedding
            """

            result = await self.graph.query(cypher_query, {"resume_id": resume_id})

            # Calculate similarity scores and rank results
            scored_results = []
            for record in result.result_set:
                subject = record[0]
                predicate = record[1]
                obj = record[2]
                subject_desc = record[3] or ""
                object_desc = record[4] or ""
                rel_desc = record[5] or ""
                subject_emb = (
                    json.loads(record[6]) if record[6] and record[6] != "null" else []
                )
                object_emb = (
                    json.loads(record[7]) if record[7] and record[7] != "null" else []
                )
                rel_emb = (
                    json.loads(record[8]) if record[8] and record[8] != "null" else []
                )

                # Calculate similarity scores
                subject_sim = (
                    self._cosine_similarity(query_embedding, subject_emb)
                    if subject_emb
                    else 0
                )
                object_sim = (
                    self._cosine_similarity(query_embedding, object_emb)
                    if object_emb
                    else 0
                )
                rel_sim = (
                    self._cosine_similarity(query_embedding, rel_emb) if rel_emb else 0
                )

                # Use max similarity as the score
                max_similarity = max(subject_sim, object_sim, rel_sim)

                scored_results.append(
                    {
                        "subject": subject,
                        "predicate": predicate,
                        "object": obj,
                        "subject_description": subject_desc,
                        "object_description": object_desc,
                        "relationship_description": rel_desc,
                        "similarity_score": max_similarity,
                    }
                )

            # Sort by similarity score and return top results
            scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return scored_results[:limit]

        except Exception as e:
            print(f"Error during semantic search: {e}")
            return []

    async def search_all_resumes_by_query(
        self,
        query: str,
        limit: int = 15,
        embedding_service=None,
    ) -> List[Dict]:
        """
        Search across all resumes using natural language query.

        Args:
            query: Natural language search query
            limit: Maximum number of results to return
            embedding_service: Optional EmbeddingService instance

        Returns:
            List of relevant triplets with descriptions
        """
        if not self.graph:
            return []

        try:
            # Generate embedding for the query
            if embedding_service:
                query_embedding = await embedding_service.generate_embedding(query)
            else:
                # Fallback to default (should not happen in normal flow)
                from ..services.embedding_service import EmbeddingService

                default_embedder = EmbeddingService()
                query_embedding = await default_embedder.generate_embedding(query)

            if not query_embedding:
                return []

            # Query for all triplets with embeddings
            cypher_query = """
            MATCH (s)-[r]->(o)
            WHERE (s.embedding IS NOT NULL OR r.embedding IS NOT NULL OR o.embedding IS NOT NULL)
            RETURN s.name as subject,
                   type(r) as predicate,
                   o.name as object,
                   s.description as subject_description,
                   o.description as object_description,
                   r.description as relationship_description,
                   s.embedding as subject_embedding,
                   o.embedding as object_embedding,
                   r.embedding as relationship_embedding,
                   s.resume_id as resume_id
            """

            result = await self.graph.query(cypher_query)

            # Calculate similarity scores and rank results
            scored_results = []
            for record in result.result_set:
                subject = record[0]
                predicate = record[1]
                obj = record[2]
                subject_desc = record[3] or ""
                object_desc = record[4] or ""
                rel_desc = record[5] or ""
                subject_emb = (
                    json.loads(record[6]) if record[6] and record[6] != "null" else []
                )
                object_emb = (
                    json.loads(record[7]) if record[7] and record[7] != "null" else []
                )
                rel_emb = (
                    json.loads(record[8]) if record[8] and record[8] != "null" else []
                )
                resume_id = record[9] if record[9] else "unknown"

                # Calculate similarity scores
                subject_sim = (
                    self._cosine_similarity(query_embedding, subject_emb)
                    if subject_emb
                    else 0
                )
                object_sim = (
                    self._cosine_similarity(query_embedding, object_emb)
                    if object_emb
                    else 0
                )
                rel_sim = (
                    self._cosine_similarity(query_embedding, rel_emb) if rel_emb else 0
                )

                # Use max similarity as the score
                max_similarity = max(subject_sim, object_sim, rel_sim)

                scored_results.append(
                    {
                        "subject": subject,
                        "predicate": predicate,
                        "object": obj,
                        "subject_description": subject_desc,
                        "object_description": object_desc,
                        "relationship_description": rel_desc,
                        "similarity_score": max_similarity,
                        "resume_id": resume_id,
                    }
                )

            # Sort by similarity score and return top results
            scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return scored_results[:limit]

        except Exception as e:
            print(f"Error during semantic search: {e}")
            return []
