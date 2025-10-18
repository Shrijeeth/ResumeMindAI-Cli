from markitdown import MarkItDown

from resumemind.core.agents.resume_cleaning_workflow import ResumeCleaningWorkflow
from resumemind.core.providers.config import ProviderConfig


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
