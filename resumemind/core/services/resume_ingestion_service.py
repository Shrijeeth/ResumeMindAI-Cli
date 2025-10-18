from markitdown import MarkItDown


async def read_resume(resume_path: str) -> str:
    md = MarkItDown(enable_plugins=True)
    resume_data = md.convert(resume_path)
    return resume_data.markdown


async def process_resume_content(resume_content: str) -> str:
    pass
