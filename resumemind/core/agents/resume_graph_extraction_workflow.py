import re
from textwrap import dedent
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from agno.models.litellm import LiteLLM
from agno.team import Team
from pydantic import BaseModel, Field


class GraphTriplet(BaseModel):
    """Represents a single graph triplet (subject, predicate, object)"""

    subject: str = Field(description="The subject node of the triplet")
    predicate: str = Field(
        description="The relationship/edge between subject and object"
    )
    object: str = Field(description="The object node of the triplet")
    subject_type: str = Field(description="Type/category of the subject node")
    object_type: str = Field(description="Type/category of the object node")
    subject_description: str = Field(
        description="Detailed description of the subject entity for context"
    )
    object_description: str = Field(
        description="Detailed description of the object entity for context"
    )
    relationship_description: str = Field(
        description="Detailed description of the relationship for context"
    )


class ResumeGraphExtractionOutput(BaseModel):
    """Output schema for resume graph extraction workflow with vector support"""

    triplets: List[GraphTriplet] = Field(
        description="List of graph triplets extracted from the resume"
    )
    validation_status: bool = Field(
        description="Whether the extraction was successful and valid"
    )
    validation_message: str = Field(
        description="Summary of the extraction process and any issues"
    )
    additional_extraction_requests: List[str] = Field(
        default_factory=list,
        description="Additional information requests from user during review",
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
                        Your task is to identify and extract all relevant entities from the given resume content.

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
                        - Do not add any extra content to the resume. Mainly focus on extracting entities only from the given resume content strictly.

                        Output format: List each entity with its type, one per line.
                        Examples: "Python (TECHNOLOGY)", "Google (COMPANY)", "Software Engineer (POSITION)"
                    """),
                    markdown=True,
                    retries=3,
                ),
                Agent(
                    model=self.model,
                    name="Relationship Mapper",
                    role="Identify relationships between extracted entities",
                    instructions=dedent("""
                        You are an expert relationship mapper for resume graph data.
                        Your task is to identify meaningful relationships between entities for given entities and their types.

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
                        - Do not add any extra content to the resume. Mainly focus on extracting relationships only from the given resume content and entities strictly.

                        Output format: List relationships as triplets (Subject, Predicate, Object)
                        Examples: "John Doe, WORKED_AT, Google", "Python Project, USES_TECHNOLOGY, Django"
                    """),
                    markdown=True,
                    retries=3,
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
                        - Extra content should not be added to the graph other than the given resume content and entities strictly.

                        Output the final validated graph structure with explanations for any changes made.
                    """),
                    markdown=True,
                    retries=3,
                ),
            ],
            instructions=dedent("""
                You are the lead of a resume graph extraction team.
                Your goal is to convert formatted resume content into a structured knowledge graph.
                If the graph is not valid, ask the validator to fix it.
                Stop the process when validator is ok with the output. Until then keep iterating the extraction and validation process.

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
                You are a JSON formatter specialized in graph data structures.
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

                Note: Focus on creating high-quality descriptions.
                Ensure the output strictly follows the ResumeGraphExtractionOutput schema.
            """),
            output_schema=ResumeGraphExtractionOutput,
            use_json_mode=True,
            retries=3,
        )

        # Dedicated team for additional extraction requests
        self.additional_extraction_team = Team(
            name="Additional Information Extraction Team",
            model=self.model,
            members=[
                Agent(
                    model=self.model,
                    name="Focused Entity Hunter",
                    role="Search for specific entities and information requested by user",
                    instructions=dedent("""
                        You are a focused entity hunter specialized in finding specific information in resumes.
                        Your task is to search ONLY for the specific information requested by the user.

                        Guidelines:
                        - Focus EXCLUSIVELY on the user's specific requests
                        - Extract ALL instances of the requested information, even if some may have been found before
                        - Look for subtle mentions, implicit references, and related information
                        - Be thorough but precise - only extract what's actually mentioned
                        - Include obvious instances that might have been missed in general extraction
                        - If the requested information is not found, clearly state so
                        - Pay attention to context and ensure accuracy

                        Entity Types to Consider:
                        - CERTIFICATION: Professional certifications, licenses
                        - PUBLICATION: Papers, articles, books, blogs
                        - VOLUNTEER: Volunteer work, community service
                        - AWARD: Awards, honors, recognitions
                        - PROJECT: Personal projects not mentioned in work experience
                        - COURSE: Additional courses, training programs
                        - LANGUAGE: Programming or spoken languages
                        - HOBBY: Personal interests and hobbies
                        - PATENT: Patents filed or granted

                        Output format: List each found entity with its type and context.
                        If nothing is found, explicitly state "No [requested information] found in resume."
                    """),
                    markdown=True,
                    retries=2,
                ),
                Agent(
                    model=self.model,
                    name="Specific Relationship Mapper",
                    role="Create relationships for the specifically requested information",
                    instructions=dedent("""
                        You are a relationship mapper focused on creating triplets for specific user requests.
                        Your task is to create meaningful relationships ONLY for the information found by the Entity Hunter.

                        Relationship Types for Specific Requests:
                        - HAS_CERTIFICATION: Person has Certification
                        - PUBLISHED: Person published Publication
                        - VOLUNTEERED_AT: Person volunteered at Organization
                        - RECEIVED_AWARD: Person received Award
                        - COMPLETED_COURSE: Person completed Course
                        - SPEAKS_LANGUAGE: Person speaks Language
                        - HAS_HOBBY: Person has Hobby
                        - FILED_PATENT: Person filed Patent
                        - PARTICIPATED_IN: Person participated in Activity

                        Guidelines:
                        - Only create relationships for information that was actually found
                        - Ensure all relationships are factually grounded in the resume
                        - Do not create speculative or assumed relationships
                        - Include temporal information when available
                        - Connect related entities appropriately

                        Output format: List relationships as triplets (Subject, Predicate, Object)
                        If no relationships can be created, state "No relationships found for requested information."
                    """),
                    markdown=True,
                    retries=2,
                ),
                Agent(
                    model=self.model,
                    name="Focused Validator",
                    role="Validate that extracted information matches user requests exactly",
                    instructions=dedent("""
                        You are a focused validator for specific extraction requests.
                        Your task is to ensure that ONLY the requested information is extracted and nothing else.

                        Validation Criteria:
                        - Verify that all extracted information directly relates to user requests
                        - Remove any general information that wasn't specifically requested
                        - Ensure factual accuracy - information must be explicitly mentioned in resume
                        - Check for completeness - did we find all instances of requested information?
                        - Validate relationship accuracy and appropriateness

                        Quality Checks:
                        - Every triplet must be directly related to the user's specific request
                        - Allow potential duplicates - deduplication will be handled later in the process
                        - No speculative or inferred information
                        - Proper entity typing for the specific domain requested
                        - Clear and accurate descriptions
                        - Prioritize completeness over avoiding duplicates

                        Output the final validated triplets with explanations for any changes made.
                        If no valid information is found, clearly state this result.
                    """),
                    markdown=True,
                    retries=2,
                ),
            ],
            instructions=dedent("""
                You are the lead of a focused extraction team for specific user requests.
                Your goal is to find and extract ONLY the specific information requested by the user.

                Process:
                1. Focused Entity Hunter searches for the specific requested information
                2. Specific Relationship Mapper creates relationships only for found information
                3. Focused Validator ensures accuracy and relevance to user requests

                Key Responsibilities:
                - Extract ALL instances of what the user specifically requested
                - Be thorough and comprehensive - find everything related to the request
                - Extract what's actually mentioned, even if it might overlap with previous extractions
                - Provide clear feedback if requested information is not found
                - Maintain high accuracy and factual grounding
                - Prioritize completeness over avoiding potential duplicates

                Final Output Requirements:
                - List of triplets specifically related to user requests
                - Clear indication if no information was found
                - Quality assessment focused on request fulfillment
            """),
            add_name_to_context=True,
            retries=2,
        )

    def _parse_resume_sections(self, formatted_resume: str) -> List[Dict[str, str]]:
        """
        Parse the formatted resume into distinct sections for better processing.

        Args:
            formatted_resume: Clean, formatted resume content in markdown format

        Returns:
            List of dictionaries with section_type, title, and content
        """
        sections = []
        lines = formatted_resume.split("\n")
        current_section = None
        current_content = []
        current_title = ""

        # Common section headers (case-insensitive patterns)
        section_patterns = {
            r"(?i)^#+\s*(education|academic|qualifications?)": "education",
            r"(?i)^#+\s*(experience|employment|work|career)": "experience",
            r"(?i)^#+\s*(skills?|technical|competenc)": "skills",
            r"(?i)^#+\s*(projects?|portfolio)": "projects",
            r"(?i)^#+\s*(publications?|research|papers?)": "publications",
            r"(?i)^#+\s*(contact|personal|info)": "contact",
            r"(?i)^#+\s*(summary|objective|profile)": "summary",
            r"(?i)^#+\s*(awards?|honors?|achievements?)": "awards",
            r"(?i)^#+\s*(volunteer|community|service)": "volunteer",
            r"(?i)^#+\s*(certifications?|licenses?)": "certifications",
        }

        for line in lines:
            # Check if this line starts a new section
            section_type = None

            for pattern, stype in section_patterns.items():
                if re.match(pattern, line.strip()):
                    section_type = stype
                    break

            if section_type:
                # Save previous section if it exists
                if current_section and current_content:
                    sections.append(
                        {
                            "section_type": current_section,
                            "title": current_title,
                            "content": "\n".join(current_content).strip(),
                        }
                    )

                # Start new section
                current_section = section_type
                current_title = line.strip()
                current_content = [line]
            else:
                # Add to current section content
                if current_section:
                    current_content.append(line)
                else:
                    # Handle content before first section (like header/contact info)
                    if not current_section:
                        current_section = "header"
                        current_title = "Header Information"
                        current_content = [line]

        # Add the last section
        if current_section and current_content:
            sections.append(
                {
                    "section_type": current_section,
                    "title": current_title,
                    "content": "\n".join(current_content).strip(),
                }
            )

        return sections

    async def _process_section(self, section: Dict[str, str]) -> List[GraphTriplet]:
        """
        Process a single resume section with the existing graph extraction team.

        Args:
            section: Dictionary with section_type, title, and content

        Returns:
            List of GraphTriplet objects extracted from the section
        """
        section_message = dedent(f"""
            Resume Section: {section["title"]}
            Section Type: {section["section_type"]}

            Content:
            ```
            {section["content"]}
            ```

            Focus on extracting information specifically from this {section["section_type"]} section.
            Pay attention to the section context when creating relationships and entity types.
            Ensure all extracted information is factually grounded in the section content.
        """)

        # Run the existing graph extraction team on this section
        team_response = await self.graph_extraction_team.arun(input=section_message)

        # Format the response into structured JSON
        json_response = await self.json_formatter_agent.arun(
            input=team_response.content
        )

        return json_response.content.triplets if json_response.content.triplets else []

    async def run(self, formatted_resume: str) -> ResumeGraphExtractionOutput:
        """
        Extract graph triplets from a formatted resume using section-based processing.

        Args:
            formatted_resume: Clean, formatted resume content in markdown format

        Returns:
            ResumeGraphExtractionOutput containing triplets, and validation info
        """
        # Parse resume into sections
        sections = self._parse_resume_sections(formatted_resume)

        print(f"📄 Parsed resume into {len(sections)} sections:")
        for section in sections:
            print(f"  - {section['section_type']}: {section['title']}")

        # Process each section separately
        all_triplets = []
        section_results = {}

        for section in sections:
            print(f"\n🔄 Processing {section['section_type']} section...")

            try:
                section_triplets = await self._process_section(section)
                all_triplets.extend(section_triplets)
                section_results[section["section_type"]] = len(section_triplets)

                print(
                    f"✅ Extracted {len(section_triplets)} triplets from {section['section_type']}"
                )

            except Exception as e:
                print(
                    f"⚠️  Error processing {section['section_type']} section: {str(e)}"
                )
                section_results[section["section_type"]] = 0

        # Create summary message
        total_triplets = len(all_triplets)
        summary_parts = [
            f"Successfully processed {len(sections)} sections with {total_triplets} total triplets"
        ]

        for section_type, count in section_results.items():
            summary_parts.append(f"{section_type}: {count} triplets")

        validation_message = "; ".join(summary_parts)

        print(
            f"\n📊 Section-based extraction complete: {total_triplets} total triplets"
        )

        return ResumeGraphExtractionOutput(
            triplets=all_triplets,
            validation_status=True,
            validation_message=validation_message,
            additional_extraction_requests=[],
        )

    async def extract_additional_triplets(
        self, formatted_resume: str, additional_requests: List[str]
    ) -> List[GraphTriplet]:
        """
        Extract additional triplets based on specific user requests.

        Args:
            formatted_resume: Clean, formatted resume content in markdown format
            additional_requests: List of specific information to extract

        Returns:
            List of additional GraphTriplet objects
        """
        if not additional_requests:
            return []

        requests_text = ", ".join(additional_requests)
        message = dedent(f"""
            Resume Content in markdown format:

            ```
            {formatted_resume}
            ```

            SPECIFIC EXTRACTION REQUEST:
            The user has specifically requested to extract information from resume content about: {requests_text}

            Please focus ONLY on extracting triplets related to these specific requests.
            Look carefully for any mentions, relationships, or entities related to: {requests_text}

            If no information about these specific requests is found in the resume content, return an empty list.
        """)

        # Run the dedicated additional extraction team
        team_response = await self.additional_extraction_team.arun(input=message)

        # Format the response into structured JSON
        json_response = await self.json_formatter_agent.arun(
            input=team_response.content
        )

        # Return only the triplets from the additional extraction
        return json_response.content.triplets if json_response.content.triplets else []
