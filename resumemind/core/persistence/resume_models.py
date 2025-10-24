"""
Database models for resume data persistence in MySQL
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class ResumeDataModel:
    """Database model for resume data storage"""

    id: Optional[int] = None
    resume_id: str = ""  # Unique hash-based identifier
    file_name: str = ""
    file_path: str = ""
    file_size: int = 0
    file_type: str = ""  # pdf, docx, txt, etc.

    # Resume content
    raw_content: str = ""  # Original markdown from MarkItDown
    cleaned_content: str = ""  # Cleaned/formatted content
    content_hash: str = ""  # SHA256 hash of raw content

    # Metadata
    ingestion_status: str = "pending"  # pending, completed, failed
    graph_ingested: bool = False
    error_message: Optional[str] = None

    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    ingested_at: Optional[str] = None

    @classmethod
    def from_file_data(
        cls,
        file_path: str,
        raw_content: str,
        cleaned_content: str = "",
        resume_id: Optional[str] = None,
    ) -> "ResumeDataModel":
        """Create ResumeDataModel from file data"""
        path = Path(file_path)

        # Generate content hash
        content_hash = hashlib.sha256(raw_content.encode()).hexdigest()

        # Generate resume_id if not provided
        if resume_id is None:
            resume_id = hashlib.sha256(
                f"{path.absolute()}{content_hash}".encode()
            ).hexdigest()[:16]

        return cls(
            resume_id=resume_id,
            file_name=path.name,
            file_path=str(path.absolute()),
            file_size=path.stat().st_size if path.exists() else 0,
            file_type=path.suffix.lstrip(".").lower(),
            raw_content=raw_content,
            cleaned_content=cleaned_content,
            content_hash=content_hash,
            ingestion_status="pending",
            graph_ingested=False,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations"""
        return {
            "resume_id": self.resume_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "raw_content": self.raw_content,
            "cleaned_content": self.cleaned_content,
            "content_hash": self.content_hash,
            "ingestion_status": self.ingestion_status,
            "graph_ingested": self.graph_ingested,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "ingested_at": self.ingested_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResumeDataModel":
        """Create ResumeDataModel from dictionary"""
        return cls(
            id=data.get("id"),
            resume_id=data.get("resume_id", ""),
            file_name=data.get("file_name", ""),
            file_path=data.get("file_path", ""),
            file_size=data.get("file_size", 0),
            file_type=data.get("file_type", ""),
            raw_content=data.get("raw_content", ""),
            cleaned_content=data.get("cleaned_content", ""),
            content_hash=data.get("content_hash", ""),
            ingestion_status=data.get("ingestion_status", "pending"),
            graph_ingested=data.get("graph_ingested", False),
            error_message=data.get("error_message"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            ingested_at=data.get("ingested_at"),
        )

    def mark_completed(self):
        """Mark resume as successfully ingested"""
        self.ingestion_status = "completed"
        self.graph_ingested = True
        self.ingested_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def mark_failed(self, error_message: str):
        """Mark resume ingestion as failed"""
        self.ingestion_status = "failed"
        self.error_message = error_message
        self.updated_at = datetime.now().isoformat()
