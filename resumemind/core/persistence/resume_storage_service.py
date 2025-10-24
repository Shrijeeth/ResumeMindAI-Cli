"""
MySQL service for resume data persistence
"""

import sqlite3
from pathlib import Path
from typing import List, Optional

from .resume_models import ResumeDataModel


class ResumeStorageService:
    """
    Service for managing resume data persistence using SQLite.
    Uses SQLite for simplicity and portability, can be upgraded to MySQL later.
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure single database connection"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the service"""
        if self._initialized:
            return

        self.db_path = self._get_db_path()
        self.conn = None
        self._initialized = True
        self._ensure_database()

    def _get_db_path(self) -> Path:
        """Get the database file path"""
        home = Path.home()
        db_dir = home / ".resumemind"
        db_dir.mkdir(exist_ok=True)
        return db_dir / "resumes.db"

    def _ensure_database(self):
        """Ensure database and tables exist"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            self._create_tables()
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        cursor = self.conn.cursor()

        # Create resumes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_type TEXT NOT NULL,
                raw_content TEXT NOT NULL,
                cleaned_content TEXT,
                content_hash TEXT NOT NULL,
                ingestion_status TEXT DEFAULT 'pending',
                graph_ingested BOOLEAN DEFAULT 0,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                ingested_at TEXT
            )
        """)

        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resume_id ON resumes(resume_id)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ingestion_status ON resumes(ingestion_status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_graph_ingested ON resumes(graph_ingested)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_created_at ON resumes(created_at)"
        )

        self.conn.commit()

    def save_resume(self, resume: ResumeDataModel) -> ResumeDataModel:
        """
        Save or update a resume in the database.

        Args:
            resume: ResumeDataModel to save

        Returns:
            ResumeDataModel with updated id
        """
        cursor = self.conn.cursor()

        try:
            if resume.id is None:
                # Insert new resume
                cursor.execute(
                    """
                    INSERT INTO resumes (
                        resume_id, file_name, file_path, file_size, file_type,
                        raw_content, cleaned_content, content_hash,
                        ingestion_status, graph_ingested, error_message,
                        created_at, updated_at, ingested_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        resume.resume_id,
                        resume.file_name,
                        resume.file_path,
                        resume.file_size,
                        resume.file_type,
                        resume.raw_content,
                        resume.cleaned_content,
                        resume.content_hash,
                        resume.ingestion_status,
                        resume.graph_ingested,
                        resume.error_message,
                        resume.created_at,
                        resume.updated_at,
                        resume.ingested_at,
                    ),
                )
                resume.id = cursor.lastrowid
            else:
                # Update existing resume
                cursor.execute(
                    """
                    UPDATE resumes SET
                        file_name = ?, file_path = ?, file_size = ?, file_type = ?,
                        raw_content = ?, cleaned_content = ?, content_hash = ?,
                        ingestion_status = ?, graph_ingested = ?, error_message = ?,
                        updated_at = ?, ingested_at = ?
                    WHERE id = ?
                """,
                    (
                        resume.file_name,
                        resume.file_path,
                        resume.file_size,
                        resume.file_type,
                        resume.raw_content,
                        resume.cleaned_content,
                        resume.content_hash,
                        resume.ingestion_status,
                        resume.graph_ingested,
                        resume.error_message,
                        resume.updated_at,
                        resume.ingested_at,
                        resume.id,
                    ),
                )

            self.conn.commit()
            return resume

        except sqlite3.IntegrityError as e:
            # Handle duplicate resume_id
            if "UNIQUE constraint failed" in str(e):
                # Resume already exists, update it instead
                existing = self.get_resume_by_resume_id(resume.resume_id)
                if existing:
                    resume.id = existing.id
                    return self.save_resume(resume)
            raise

    def get_resume_by_id(self, resume_id: int) -> Optional[ResumeDataModel]:
        """Get resume by database ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
        row = cursor.fetchone()

        if row:
            return ResumeDataModel.from_dict(dict(row))
        return None

    def get_resume_by_resume_id(self, resume_id: str) -> Optional[ResumeDataModel]:
        """Get resume by unique resume_id"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM resumes WHERE resume_id = ?", (resume_id,))
        row = cursor.fetchone()

        if row:
            return ResumeDataModel.from_dict(dict(row))
        return None

    def get_all_resumes(
        self, status: Optional[str] = None, limit: Optional[int] = None
    ) -> List[ResumeDataModel]:
        """
        Get all resumes, optionally filtered by status.

        Args:
            status: Filter by ingestion status (pending, completed, failed)
            limit: Maximum number of resumes to return

        Returns:
            List of ResumeDataModel objects
        """
        cursor = self.conn.cursor()

        if status:
            query = "SELECT * FROM resumes WHERE ingestion_status = ? ORDER BY created_at DESC"
            params = (status,)
        else:
            query = "SELECT * FROM resumes ORDER BY created_at DESC"
            params = ()

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [ResumeDataModel.from_dict(dict(row)) for row in rows]

    def get_ingested_resumes(
        self, limit: Optional[int] = None
    ) -> List[ResumeDataModel]:
        """Get all successfully ingested resumes"""
        cursor = self.conn.cursor()
        query = (
            "SELECT * FROM resumes WHERE graph_ingested = 1 ORDER BY ingested_at DESC"
        )

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        rows = cursor.fetchall()

        return [ResumeDataModel.from_dict(dict(row)) for row in rows]

    def delete_resume(self, resume_id: str) -> bool:
        """
        Delete a resume by resume_id.

        Args:
            resume_id: Unique resume identifier

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM resumes WHERE resume_id = ?", (resume_id,))
        self.conn.commit()

        return cursor.rowcount > 0

    def get_resume_count(self, status: Optional[str] = None) -> int:
        """Get count of resumes, optionally filtered by status"""
        cursor = self.conn.cursor()

        if status:
            cursor.execute(
                "SELECT COUNT(*) FROM resumes WHERE ingestion_status = ?", (status,)
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM resumes")

        return cursor.fetchone()[0]

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __del__(self):
        """Cleanup on deletion"""
        self.close()
