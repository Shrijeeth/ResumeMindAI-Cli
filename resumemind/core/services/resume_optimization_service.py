"""
Resume Optimization Service - Orchestrates resume optimization workflow
"""

from typing import Any, Dict, List, Optional

from ..agents import ResumeOptimizationOutput, ResumeOptimizerWorkflow
from ..persistence.resume_storage_service import ResumeStorageService
from ..services.graph_database_service import GraphDatabaseService


class ResumeOptimizationService:
    """Service for optimizing resume data using AI analysis"""

    def __init__(
        self,
        model_id: str,
        api_key: Optional[str],
        base_url: Optional[str],
        additional_params: Dict[str, Any],
    ):
        self.optimizer = ResumeOptimizerWorkflow(
            model_id=model_id,
            api_key=api_key,
            base_url=base_url,
            additional_params=additional_params,
        )
        self.resume_storage = ResumeStorageService()
        self.graph_db = GraphDatabaseService()

    async def optimize_resume(
        self,
        resume_id: str,
        additional_context: Optional[str] = None,
    ) -> Optional[ResumeOptimizationOutput]:
        """
        Optimize a specific resume by analyzing its content and graph data.

        Args:
            resume_id: ID of the resume to optimize
            additional_context: Optional additional context (target role, industry, etc.)

        Returns:
            ResumeOptimizationOutput with optimization suggestions or None if failed
        """
        try:
            # Get resume data from storage
            resume_model = self.resume_storage.get_resume_by_resume_id(resume_id)
            if not resume_model:
                print(f"Resume not found: {resume_id}")
                return None

            # Convert ResumeDataModel to dictionary
            resume_data = resume_model.to_dict()

            # Connect to graph database and get relationships
            self.graph_db.connect()
            relationships = await self.graph_db.get_resume_relationships(resume_id)

            # Run optimization analysis
            optimization_result = await self.optimizer.analyze_and_optimize(
                resume_data=resume_data,
                graph_relationships=relationships,
                additional_context=additional_context,
            )

            return optimization_result

        except Exception as e:
            print(f"Error during resume optimization: {e}")
            return None
        finally:
            await self.graph_db.disconnect()

    async def get_available_resumes(self) -> List[Dict[str, Any]]:
        """
        Get list of all ingested resumes available for optimization.

        Returns:
            List of resume dictionaries with metadata
        """
        try:
            resumes = self.resume_storage.get_all_resumes()
            # Filter to only completed resumes
            completed_resumes = [
                r for r in resumes if r.get("ingestion_status") == "completed"
            ]
            return completed_resumes
        except Exception as e:
            print(f"Error getting available resumes: {e}")
            return []
