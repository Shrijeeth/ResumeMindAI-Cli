"""
Resume Q&A Service - Answer questions about resumes using GraphRAG
"""

from textwrap import dedent
from typing import Any, Dict, List, Optional

from agno.agent import Agent

from ..services.embedding_service import EmbeddingService
from ..services.graph_database_service import GraphDatabaseService


class ResumeQAService:
    """Service for answering questions about resume data using GraphRAG"""

    def __init__(
        self,
        model_id: str,
        api_key: Optional[str],
        base_url: Optional[str],
        additional_params: Dict[str, Any],
        embedding_service: Optional[EmbeddingService] = None,
    ):
        from agno.models.litellm import LiteLLM

        self.model = LiteLLM(
            id=model_id,
            api_base=base_url,
            api_key=api_key,
            **additional_params,
        )
        self.graph_db = GraphDatabaseService()
        self.embedding_service = embedding_service
        self.chat_history: List[Dict[str, str]] = []  # Store conversation history

    async def ask_question(
        self,
        resume_id: str,
        question: str,
    ) -> Optional[str]:
        """
        Answer a question about a specific resume using GraphRAG.

        Args:
            resume_id: ID of the resume to query
            question: User's question about the resume

        Returns:
            Answer string or None if failed
        """
        try:
            # Connect to graph database
            self.graph_db.connect()

            # Build context-aware search query
            search_query = question
            if self.chat_history:
                # Include context from last message for better search
                last_qa = self.chat_history[-1]
                search_query = f"{last_qa['question']} {question}"

            # Perform semantic search to find relevant context
            relevant_context = await self.graph_db.search_resume_by_query(
                resume_id=resume_id,
                query=search_query,
                limit=10,
                embedding_service=self.embedding_service,
            )

            if not relevant_context:
                return "I couldn't find relevant information in the resume to answer your question."

            # Format context for the LLM
            context_text = self._format_context(relevant_context)

            # Generate answer using LLM
            answer = await self._generate_answer(question, context_text)

            return answer

        except Exception as e:
            print(f"Error during Q&A: {e}")
            return None
        finally:
            await self.graph_db.disconnect()

    async def ask_question_all_resumes(
        self,
        question: str,
    ) -> Optional[str]:
        """
        Answer a question across all resumes in the database.

        Args:
            question: User's question

        Returns:
            Answer string or None if failed
        """
        try:
            # Connect to graph database
            self.graph_db.connect()

            # Build context-aware search query
            search_query = question
            if self.chat_history:
                # Include context from last message for better search
                last_qa = self.chat_history[-1]
                search_query = f"{last_qa['question']} {question}"

            # Perform semantic search across all resumes
            relevant_context = await self.graph_db.search_all_resumes_by_query(
                query=search_query,
                limit=15,
                embedding_service=self.embedding_service,
            )

            if not relevant_context:
                return "I couldn't find relevant information to answer your question."

            # Format context for the LLM
            context_text = self._format_context(relevant_context)

            # Generate answer using LLM
            answer = await self._generate_answer(question, context_text)

            return answer

        except Exception as e:
            print(f"Error during Q&A: {e}")
            return None
        finally:
            await self.graph_db.disconnect()

    def _format_context(self, context_items: List[Dict[str, Any]]) -> str:
        """Format retrieved context items into a readable text"""
        formatted_lines = []

        for idx, item in enumerate(context_items, 1):
            # Extract triplet information
            subject = item.get("subject", "Unknown")
            predicate = item.get("predicate", "Unknown")
            obj = item.get("object", "Unknown")

            # Extract descriptions
            subject_desc = item.get("subject_description", "")
            object_desc = item.get("object_description", "")
            rel_desc = item.get("relationship_description", "")

            # Format the context entry
            formatted_lines.append(f"{idx}. {subject} --[{predicate}]--> {obj}")

            if subject_desc:
                formatted_lines.append(f"   Subject: {subject_desc}")
            if object_desc:
                formatted_lines.append(f"   Object: {object_desc}")
            if rel_desc:
                formatted_lines.append(f"   Relationship: {rel_desc}")

            formatted_lines.append("")  # Empty line for separation

        return "\n".join(formatted_lines)

    async def _generate_answer(self, question: str, context: str) -> str:
        """Generate an answer using the LLM based on context"""
        qa_agent = Agent(
            model=self.model,
            name="Resume Q&A Agent",
            role="Answer questions about resumes based on provided context",
            instructions=dedent("""
                You are a helpful assistant that answers questions about resumes.
                You will be provided with relevant context from a resume knowledge graph.

                Guidelines:
                - Answer based ONLY on the provided context
                - Be specific and cite relevant information from the context
                - If the context doesn't contain enough information, say so
                - Keep answers concise but informative
                - Use natural language, not technical jargon
                - If asked about skills, list them clearly
                - If asked about experience, provide details with context
                - If asked about education, include relevant details
                - Maintain conversation context from previous questions

                Format your answers in a clear, readable way.
            """),
            markdown=True,
        )

        # Build conversation history for context
        history_text = ""
        if self.chat_history:
            history_text = "\n\nPrevious Conversation:\n"
            for entry in self.chat_history[-3:]:  # Last 3 exchanges
                history_text += f"Q: {entry['question']}\nA: {entry['answer']}\n\n"

        prompt = dedent(f"""
            {history_text}
            Current Question: {question}

            Relevant Context from Resume:
            {context}

            Please answer the current question based on the context provided above.
            Consider the conversation history if relevant.
        """)

        response = await qa_agent.arun(prompt)
        answer = response.content

        # Store in chat history
        self.chat_history.append(
            {
                "question": question,
                "answer": answer,
            }
        )

        return answer

    def clear_chat_history(self):
        """Clear the conversation history"""
        self.chat_history = []

    async def get_resume_summary(self, resume_id: str) -> Optional[str]:
        """
        Generate a comprehensive summary of a resume.

        Args:
            resume_id: ID of the resume to summarize

        Returns:
            Summary string or None if failed
        """
        return await self.ask_question(
            resume_id=resume_id,
            question="Provide a comprehensive summary of this resume including key skills, experience, education, and notable achievements.",
        )
