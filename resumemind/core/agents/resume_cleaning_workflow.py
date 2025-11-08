from textwrap import dedent
from typing import Any, Dict, Optional

from agno.agent import Agent
from agno.models.litellm import LiteLLM
from agno.team import Team
from pydantic import BaseModel, Field


class ResumeCleaningWorkflowOutput(BaseModel):
    formatted_resume: str = Field(
        description="The final formatted resume in markdown format as string"
    )
    validation_status: bool = Field(
        description="The validation status. Whether validation is successful or not"
    )
    validation_message: str = Field(description="The team log summary")


class ResumeCleaningWorkflow:
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
        self.resume_structuring_team = Team(
            name="Resume Structuring Team",
            model=self.model,
            members=[
                Agent(
                    model=self.model,
                    name="Resume Formatter",
                    role="Format the raw resume content into proper markdown",
                    instructions=dedent("""
                        You are a resume formatter.
                        Your task is to format the raw resume content into proper markdown.
                        The formatted resume should be easy to read and understand.
                        Fix encoding issues if any.
                        Fix any formatting issues if any.
                        Fix any spacing issues if any.
                        Fix any alignment issues if any.
                        Fix any indentation issues if any.
                        Fix any other issues if any.
                        Do not add any extra content to the resume. Mainly focus on formatting.
                        Your work will be validated by a resume validator.
                        If the validator finds any issues, you will be asked to fix them.
                        Your final output should be a proper markdown formatted resume.
                    """),
                    markdown=True,
                ),
                Agent(
                    model=self.model,
                    name="Resume Validator",
                    role="Validate the resume content",
                    instructions=dedent("""
                        You are a resume validator.
                        Your task is to validate the resume content.
                        If the resume content is not proper markdown or has any syntax/style/structure issues, you will be asked to fix it.
                        Your final output should be a proper markdown formatted resume.
                    """),
                    markdown=True,
                ),
            ],
            instructions=dedent("""
                You are a resume structuring team lead.
                Your task is to lead the resume structuring team.
                Your final output should be a proper markdown formatted resume for the given raw resume content.
                Collaborate with `Resume Formatter` and `Resume Validator` to get the final output.
                Key Responsibilities:
                    - Lead the resume structuring team.
                    - Collaborate with `Resume Formatter` and `Resume Validator` to get the final output.
                    - Ensure the final output is a proper markdown formatted resume.
                    - If the validator finds any issues, ask the formatter to fix them.
                    - Stop the process when validator is ok with the output. Until then keep iterating the formatting and validation process.
            """),
            add_name_to_context=True,
            retries=3,
        )

        self.json_formatter_agent = Agent(
            model=self.model,
            name="JSON Formatter",
            role="Convert the given task log into JSON format according to the given schema",
            instructions=dedent("""
                You are a JSON formatter.
                Your are given a task log and a schema.
                The task log is a log of the task that was executed by the resume structuring team. It is a string.
                The schema is a JSON schema that defines the structure of the JSON output.
                Your task is to convert the given task log into JSON format according to the given schema.
                Your final output should be a JSON formatted resume.
            """),
            output_schema=ResumeCleaningWorkflowOutput,
            use_json_mode=True,
            structured_outputs=True,
            retries=3,
        )

    async def run(self, raw_resume: str):
        message = dedent(f"""
            Here is the raw resume content to be cleaned:

            {raw_resume}
        """)
        team_response = await self.resume_structuring_team.arun(input=message)
        json_response = await self.json_formatter_agent.arun(
            input=team_response.content
        )
        return json_response.content
