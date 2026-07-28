from abc import ABC
from typing import Any, Dict, List
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.orchestrator.state import AgentState
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService
from langchain_core.messages import AIMessage

class BaseAgent(ABC):
    """
    Abstract Base Class for all OrbitOS AI specialized agents.
    """
    def __init__(self, name: str, description: str, system_prompt: str, keywords: List[str]):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.keywords = keywords
        # Every agent gets its own instance of the LLM provider
        self.llm = OpenAIProvider()
        
    def _needs_context(self, query: str) -> bool:
        """Simple heuristic to determine if RAG context is needed based on query keywords."""
        query_lower = query.lower()
        return any(kw in query_lower for kw in self.keywords)

    def _get_rag_context(self, workspace_id: str, query: str) -> str:
        """Fetch relevant documents from the Knowledge Base."""
        try:
            embedding_service = EmbeddingService()
            vector_store = VectorStoreService(embedding_service=embedding_service)
            
            results = vector_store.search(
                query=query,
                top_k=3,
                filter_dict={"workspace_id": workspace_id}
            )
            
            if not results:
                return ""
            
            context_parts = []
            for r in results:
                context_parts.append(r["content"])
            
            return "\n\n---\n\n".join(context_parts)
        except Exception as e:
            print(f"[{self.name}] RAG search failed: {e}")
            return ""
            
    async def invoke(self, state: AgentState) -> Dict[str, Any]:
        print(f"--- [Node] {self.name} Execution ---")
        
        messages = state.get("messages", [])
        if not messages:
            return {
                "messages": [AIMessage(content=f"I need a message to work with. How can I help you?")],
                "current_agent": self.name
            }
        
        last_message = messages[-1].content
        workspace_id = state.get("workspace_id", "")
        business_goal = state.get("business_goal", "Not specified.")
        
        # Determine if we should query the Knowledge Base
        rag_context = ""
        if workspace_id and self._needs_context(last_message):
            print(f"--- [{self.name}] Fetching context for: {last_message[:30]}... ---")
            rag_context = self._get_rag_context(workspace_id, last_message)
        
        # Build the prompt
        system_prompt = self.system_prompt
        system_prompt += f"\n\nThe business owner's overarching goal is: {business_goal}"
        
        if rag_context:
            system_prompt += f"\n\n<BUSINESS_CONTEXT>\nThe following is relevant information from the business owner's uploaded documents:\n{rag_context}\n</BUSINESS_CONTEXT>"
        
        # Call LLM
        prompt_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": last_message}
        ]
        
        response = await self.llm.generate(prompt_messages)
        
        return {
            "messages": [AIMessage(content=response)],
            "current_agent": self.name
        }
