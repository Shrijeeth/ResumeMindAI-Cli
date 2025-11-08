"""
Resume Optimizer Workflow - Analyzes ingested resume data and suggests optimizations
"""

from textwrap import dedent
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from agno.models.litellm import LiteLLM
from agno.team import Team
from pydantic import BaseModel, Field


class OptimizationSuggestion(BaseModel):
    """Represents a single optimization suggestion"""

    category: str = Field(
        description="Category (Skills, Experience, Education, Keywords, Formatting)"
    )
    priority: str = Field(description="HIGH, MEDIUM, or LOW")
    suggestion: str = Field(description="Clear, actionable improvement suggestion")
    rationale: str = Field(description="Why this matters (1-2 sentences)")


class MissingInformation(BaseModel):
    """Represents missing information that should be added"""

    category: str = Field(description="Category of missing info")
    what_missing: str = Field(description="What's missing (brief)")
    why_important: str = Field(description="Why it matters (1 sentence)")


class ResumeOptimizationOutput(BaseModel):
    """Output schema for resume optimization workflow"""

    overall_assessment: str = Field(
        description="2-3 sentence summary of resume quality"
    )
    strengths: List[str] = Field(description="Top 3-5 strengths (brief points)")
    optimization_suggestions: List[OptimizationSuggestion] = Field(
        description="5-10 prioritized suggestions"
    )
    missing_information: List[MissingInformation] = Field(
        description="Key missing elements (max 5)"
    )
    ats_score: int = Field(description="ATS compatibility score 0-100", ge=0, le=100)
    top_actions: List[str] = Field(description="Top 3-5 immediate action items")


class ResumeOptimizerWorkflow:
    """
    Agentic workflow to analyze ingested resume data and provide optimization suggestions.
    Uses graph data and raw content to provide comprehensive recommendations.
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
            temperature=0.0,
            **additional_params,
        )

        self.optimization_team = Team(
            name="Resume Optimization Team",
            model=self.model,
            members=[
                Agent(
                    model=self.model,
                    name="Content Analyzer",
                    role="Analyze resume content quality",
                    instructions=dedent("""
                        Evaluate resume content focusing on:
                        - Quantified accomplishments with metrics
                        - Strong action verbs
                        - Relevant, impactful content
                        - Timeline consistency
                        - Appropriate technical depth

                        Keep feedback brief and actionable.
                    """),
                    markdown=True,
                    retries=2,
                ),
                Agent(
                    model=self.model,
                    name="ATS Specialist",
                    role="Evaluate ATS compatibility",
                    instructions=dedent("""
                        Assess ATS compatibility focusing on:
                        - Keyword usage and relevance
                        - Standard section headers
                        - Skills alignment with industry terms
                        - Format compatibility (no tables/graphics)

                        Provide ATS score (0-100) and top 3-5 recommendations.
                    """),
                    markdown=True,
                    retries=2,
                ),
                Agent(
                    model=self.model,
                    name="Career Strategist",
                    role="Provide strategic positioning advice",
                    instructions=dedent("""
                        Evaluate career positioning focusing on:
                        - Career narrative and progression
                        - Unique value propositions
                        - Alignment with target roles
                        - Leadership and impact

                        Provide 3-5 strategic recommendations.
                    """),
                    markdown=True,
                    retries=2,
                ),
                Agent(
                    model=self.model,
                    name="Gap Identifier",
                    role="Identify missing information",
                    instructions=dedent("""
                        Identify top 3-5 missing elements:
                        - Missing dates/durations
                        - Vague descriptions needing specifics
                        - Achievements without metrics
                        - Skills without context
                        - Projects without outcomes

                        Keep descriptions brief.
                    """),
                    markdown=True,
                    retries=2,
                ),
            ],
            instructions=dedent("""
                You are the lead of a resume optimization team.
                Your goal is to analyze resume content and provide comprehensive optimization suggestions.

                Process:
                1. Content Analyzer evaluates content quality and impact
                2. ATS Specialist assesses ATS compatibility and provides score
                3. Career Strategist provides strategic positioning advice
                4. Gap Identifier finds missing information

                Coordinate the team to produce:
                - Overall assessment of resume quality
                - Key strengths identified
                - Prioritized optimization suggestions (HIGH/MEDIUM/LOW)
                - Missing information that should be added
                - ATS compatibility score and insights
                - Top immediate action items

                Ensure all feedback is specific, actionable, and prioritized by impact.
            """),
            add_name_to_context=True,
            retries=2,
        )

        self.json_formatter_agent = Agent(
            model=self.model,
            name="Optimization JSON Formatter",
            role="Convert optimization analysis into structured JSON format",
            instructions=dedent("""
                You are a JSON formatter specialized in resume optimization data.
                You receive the output from the optimization team and convert it into the required JSON schema.

                Your tasks:
                1. Extract overall assessment (2-3 sentence summary)
                2. List top 3-5 strengths (brief points)
                3. Format 5-10 optimization suggestions with:
                    - category (Skills, Experience, Education, Keywords, Formatting)
                    - priority (HIGH, MEDIUM, LOW)
                    - suggestion (clear, actionable)
                    - rationale (1-2 sentences)
                4. List max 5 missing information items with:
                    - category
                    - what_missing (brief)
                    - why_important (1 sentence)
                5. Extract ATS score (0-100)
                6. List top 3-5 immediate action items

                Quality Requirements:
                - Keep all text concise and actionable
                - Prioritize by impact (HIGH > MEDIUM > LOW)
                - Ensure suggestions are specific, not generic
                - Focus on most important improvements

                Ensure the output strictly follows the ResumeOptimizationOutput schema.
            """),
            output_schema=ResumeOptimizationOutput,
            use_json_mode=True,
            structured_outputs=True,
            retries=3,
        )

    async def analyze_and_optimize(
        self,
        resume_data: Dict[str, Any],
        graph_relationships: List[Dict[str, Any]],
        additional_context: Optional[str] = None,
    ) -> ResumeOptimizationOutput:
        """
        Analyze resume data and provide optimization suggestions.

        Args:
            resume_data: Dictionary containing resume metadata and content
            graph_relationships: List of graph relationships extracted from resume
            additional_context: Optional additional context from user (target role, industry, etc.)

        Returns:
            ResumeOptimizationOutput with comprehensive optimization suggestions
        """
        analysis_prompt = self._prepare_analysis_prompt(
            resume_data, graph_relationships, additional_context
        )

        # Step 1: Team analyzes and produces unstructured output
        team_output = await self.optimization_team.arun(analysis_prompt)

        # Step 2: JSON formatter converts to structured output
        result = await self.json_formatter_agent.arun(team_output.content)

        return result.content

    def _prepare_analysis_prompt(
        self,
        resume_data: Dict[str, Any],
        graph_relationships: List[Dict[str, Any]],
        additional_context: Optional[str] = None,
    ) -> str:
        """Prepare the analysis prompt for the optimization team"""

        relationships_text = self._format_relationships(graph_relationships)

        file_name = resume_data.get("file_name", "Unknown")
        ingestion_date = resume_data.get("created_at", "Unknown")

        cleaned_content = resume_data.get("cleaned_content", "")
        raw_content = resume_data.get("raw_content", "")

        context_section = (
            f"## Additional Context\\n{additional_context}\\n"
            if additional_context
            else ""
        )

        prompt = dedent(f"""
            Analyze the following resume data and provide comprehensive optimization suggestions.

            ## Resume Metadata
            - File: {file_name}
            - Ingestion Date: {ingestion_date}

            ## Resume Content
            ```
            {cleaned_content if cleaned_content else raw_content}
            ```

            ## Extracted Knowledge Graph Relationships
            The following relationships were extracted from the resume:
            ```
            {relationships_text}
            ```

            {context_section}

            ## Your Task
            Provide a comprehensive analysis and optimization plan including:

            1. **Overall Assessment**: High-level evaluation of the resume's current state
            2. **Strengths**: What's working well in this resume
            3. **Optimization Suggestions**: Specific, prioritized recommendations for improvement
            4. **Missing Information**: Gaps that should be filled with specific questions to ask
            5. **ATS Compatibility**: Score and recommendations for ATS optimization
            6. **Keyword Analysis**: Evaluation of keyword usage and effectiveness
            7. **Next Steps**: Clear, prioritized action items

            Be specific, actionable, and prioritize recommendations by impact.
            Consider both content quality and ATS compatibility.
            Identify information gaps and formulate questions to gather missing details.
        """)

        return prompt

    def _format_relationships(self, relationships: List[Dict[str, Any]]) -> str:
        """Format graph relationships for display in prompt"""
        if not relationships:
            return "No relationships available."

        formatted = []
        for rel in relationships:
            subject = rel.get("subject", "Unknown")
            predicate = rel.get("predicate", "Unknown")
            obj = rel.get("object", "Unknown")
            formatted.append(f"  • {subject} --[{predicate}]--> {obj}")

        return "\n".join(formatted)
