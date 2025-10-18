from textwrap import dedent
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from agno.models.litellm import LiteLLM
from agno.team import Team
from pydantic import BaseModel, Field


class GraphTriplet(BaseModel):
    """Represents a single graph triplet (subject, predicate, object) with vector embeddings"""

    subject: str = Field(description="The subject node of the triplet")
    predicate: str = Field(
        description="The relationship/edge between subject and object"
    )
    object: str = Field(description="The object node of the triplet")
    subject_type: str = Field(description="Type/category of the subject node")
    object_type: str = Field(description="Type/category of the object node")

    # Vector embeddings for GraphRAG
    subject_description: str = Field(
        description="Detailed description of the subject entity for context"
    )
    object_description: str = Field(
        description="Detailed description of the object entity for context"
    )
    relationship_description: str = Field(
        description="Detailed description of the relationship for context"
    )
    subject_embedding: Optional[List[float]] = Field(
        default=None, description="Vector embedding of the subject entity"
    )
    object_embedding: Optional[List[float]] = Field(
        default=None, description="Vector embedding of the object entity"
    )
    relationship_embedding: Optional[List[float]] = Field(
        default=None, description="Vector embedding of the relationship"
    )


class ResumeGraphExtractionOutput(BaseModel):
    """Output schema for resume graph extraction workflow with vector support"""

    triplets: List[GraphTriplet] = Field(
        description="List of graph triplets extracted from the resume"
    )
    entities: Dict[str, str] = Field(
        description="Dictionary mapping entity names to their types"
    )
    entity_descriptions: Dict[str, str] = Field(
        description="Dictionary mapping entity names to their detailed descriptions"
    )
    entity_embeddings: Optional[Dict[str, List[float]]] = Field(
        default=None,
        description="Dictionary mapping entity names to their vector embeddings",
    )
    validation_status: bool = Field(
        description="Whether the extraction was successful and valid"
    )
    validation_message: str = Field(
        description="Summary of the extraction process and any issues"
    )


class ResumeGraphExtractionWorkflow:
    """
    Agentic workflow to extract graph triplets from formatted resumes.
    Converts resume content into structured graph data for storage in graph databases.
    """

    def __init__(
        self,
        model_id: str,
        api_key: Optional[str],
        base_url: Optional[str],
        additional_params: Dict[str, Any],
    ):
        self.model = LiteLLM(
            id=model_id,
            api_base=base_url,
            api_key=api_key,
            **additional_params,
        )

        self.graph_extraction_team = Team(
            name="Resume Graph Extraction Team",
            model=self.model,
            members=[
                Agent(
                    model=self.model,
                    name="Entity Extractor",
                    role="Extract entities and their types from resume content",
                    instructions=dedent("""
                        You are an expert entity extractor for resume data.
                        Your task is to identify and extract all relevant entities from the resume content.

                        Entity Types to Extract:
                        - PERSON: The resume owner's name
                        - SKILL: Technical and soft skills
                        - COMPANY: Organizations, employers, clients
                        - POSITION: Job titles, roles
                        - EDUCATION: Degrees, certifications, courses
                        - INSTITUTION: Schools, universities, training centers
                        - PROJECT: Personal or professional projects
                        - TECHNOLOGY: Programming languages, tools, frameworks
                        - LOCATION: Cities, countries, addresses
                        - DATE: Time periods, years, durations
                        - ACHIEVEMENT: Awards, accomplishments, metrics
                        - INDUSTRY: Business sectors, domains
                        - DEPARTMENT: Organizational units, teams

                        Guidelines:
                        - Extract specific, concrete entities (avoid generic terms)
                        - Normalize entity names (e.g., "JavaScript" not "javascript")
                        - Include quantifiable achievements and metrics
                        - Identify both explicit and implicit entities
                        - Maintain consistency in entity naming

                        Output format: List each entity with its type, one per line.
                        Example: "Python (TECHNOLOGY)", "Google (COMPANY)", "Software Engineer (POSITION)"
                    """),
                    markdown=True,
                ),
                Agent(
                    model=self.model,
                    name="Relationship Mapper",
                    role="Identify relationships between extracted entities",
                    instructions=dedent("""
                        You are an expert relationship mapper for resume graph data.
                        Your task is to identify meaningful relationships between entities.

                        Relationship Types:
                        - WORKED_AT: Person worked at Company
                        - HAS_POSITION: Person has Position at Company
                        - HAS_SKILL: Person has Skill
                        - WORKED_ON: Person worked on Project
                        - USES_TECHNOLOGY: Person/Project uses Technology
                        - LOCATED_IN: Company/Institution located in Location
                        - STUDIED_AT: Person studied at Institution
                        - HAS_DEGREE: Person has Education from Institution
                        - ACHIEVED: Person achieved Achievement
                        - DURING_PERIOD: Activity happened during Date
                        - PART_OF: Department part of Company
                        - REQUIRES_SKILL: Position requires Skill
                        - IN_INDUSTRY: Company/Position in Industry
                        - COLLABORATED_WITH: Person collaborated with Person/Team
                        - MANAGED: Person managed Project/Team
                        - CERTIFIED_IN: Person certified in Skill/Technology

                        Guidelines:
                        - Focus on factual, verifiable relationships
                        - Include temporal relationships (when things happened)
                        - Map skill requirements to positions
                        - Connect projects to technologies and skills used
                        - Identify management and collaboration relationships
                        - Include educational and certification relationships

                        Output format: List relationships as triplets (Subject, Predicate, Object)
                        Example: "John Doe, WORKED_AT, Google", "Python Project, USES_TECHNOLOGY, Django"
                    """),
                    markdown=True,
                ),
                Agent(
                    model=self.model,
                    name="Graph Validator",
                    role="Validate and refine the extracted graph structure",
                    instructions=dedent("""
                        You are a graph data validator for resume knowledge graphs.
                        Your task is to validate, clean, and optimize the extracted graph structure.
                        
                        Validation Criteria:
                        - Entity consistency: Same entities should have consistent names and types
                        - Relationship validity: All relationships should be meaningful and factual
                        - Completeness: Important relationships shouldn't be missing
                        - Redundancy: Remove duplicate or redundant triplets
                        - Accuracy: Verify relationships match the resume content

                        Optimization Tasks:
                        - Merge similar entities (e.g., "JS" and "JavaScript")
                        - Standardize entity names and types
                        - Add missing obvious relationships
                        - Remove invalid or speculative relationships
                        - Ensure proper entity typing

                        Quality Checks:
                        - Every triplet should be factually supported by resume content
                        - Entity types should be consistent and appropriate
                        - Relationships should follow logical patterns
                        - No orphaned entities (entities with no relationships)
                        - Temporal consistency in date-related relationships

                        Output the final validated graph structure with explanations for any changes made.
                    """),
                    markdown=True,
                ),
            ],
            instructions=dedent("""
                You are the lead of a resume graph extraction team.
                Your goal is to convert formatted resume content into a structured knowledge graph.

                Process:
                1. Entity Extractor identifies all relevant entities and their types
                2. Relationship Mapper finds meaningful connections between entities
                3. Graph Validator ensures quality and consistency of the final graph

                Key Responsibilities:
                - Coordinate the team to produce high-quality graph triplets
                - Ensure comprehensive coverage of resume information
                - Maintain consistency in entity naming and relationship types
                - Validate that all triplets are factually grounded in the resume
                - Optimize the graph structure for database storage and querying

                Final Output Requirements:
                - Complete list of validated graph triplets
                - Entity dictionary with types
                - Quality assessment and validation summary

                The extracted graph should enable rich querying capabilities like:
                - Finding candidates with specific skills
                - Identifying career progression patterns
                - Matching candidates to job requirements
                - Analyzing skill-technology relationships
                - Understanding industry experience
            """),
            add_name_to_context=True,
            retries=3,
        )

        self.json_formatter_agent = Agent(
            model=self.model,
            name="Graph JSON Formatter",
            role="Convert graph extraction results into structured JSON format with descriptions",
            instructions=dedent("""
                You are a JSON formatter specialized in graph data structures with vector embedding support.
                You receive the output from the graph extraction team and convert it into the required JSON schema.

                Your tasks:
                1. Parse the team's output to extract triplets and entities
                2. Format triplets with proper subject, predicate, object structure
                3. Assign appropriate types to subjects and objects
                4. Create detailed descriptions for each entity and relationship
                5. Create entity dictionary mapping names to types
                6. Create entity descriptions dictionary with rich contextual information
                7. Assess validation status and provide summary message
                
                Description Requirements:
                - Subject descriptions: Provide rich context about the entity (e.g., "John Doe is a Senior Software Engineer with 5 years of experience in Python and machine learning")
                - Object descriptions: Detailed context about the target entity (e.g., "Google is a multinational technology company specializing in search, cloud computing, and AI")
                - Relationship descriptions: Explain the nature and context of the relationship (e.g., "John Doe worked as a Senior Software Engineer at Google from 2019 to 2024, focusing on machine learning infrastructure")
                - Entity descriptions: Comprehensive information about each entity including context from the resume

                Quality Requirements:
                - All triplets must include detailed descriptions for GraphRAG compatibility
                - Entity types must be consistent and from the predefined set
                - Descriptions should be informative and contextually rich
                - Validation status should reflect the quality of extraction
                - Summary message should be informative about the process

                Note: Vector embeddings will be generated separately, so focus on creating high-quality descriptions.
                Ensure the output strictly follows the ResumeGraphExtractionOutput schema.
            """),
            output_schema=ResumeGraphExtractionOutput,
            use_json_mode=True,
            retries=3,
        )

    async def run(self, formatted_resume: str) -> ResumeGraphExtractionOutput:
        """
        Extract graph triplets from a formatted resume.

        Args:
            formatted_resume: Clean, formatted resume content in markdown format

        Returns:
            ResumeGraphExtractionOutput containing triplets, entities, and validation info
        """
        message = dedent(f"""
            Extract graph triplets from the following formatted resume content.
            Convert all relevant information into a knowledge graph structure.

            Resume Content:
            {formatted_resume}

            Instructions:
            - Extract all entities (people, companies, skills, technologies, etc.)
            - Identify meaningful relationships between entities
            - Create graph triplets in (subject, predicate, object) format
            - Ensure all triplets are factually grounded in the resume content
            - Optimize for comprehensive coverage and query capabilities
        """)

        # Run the graph extraction team
        team_response = await self.graph_extraction_team.arun(input=message)

        # Format the response into structured JSON
        json_response = await self.json_formatter_agent.arun(
            input=team_response.content
        )

        return json_response.content
