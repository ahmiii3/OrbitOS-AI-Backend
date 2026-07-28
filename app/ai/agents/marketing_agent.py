from typing import Any, Dict
from app.ai.agents.base import BaseAgent
from app.ai.orchestrator.state import AgentState
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService
from langchain_core.messages import AIMessage

MARKETING_SYSTEM_PROMPT = """You are the Chief Marketing Officer (CMO) and Lead Copywriter of OrbitOS AI.
You are an expert in digital marketing, SEO, social media strategy, audience profiling, and high-converting copywriting.

Your responsibilities:
- Create comprehensive marketing campaigns aligned with the overarching business goal.
- Generate high-quality copy for emails, landing pages, social media, and ads.
- Provide SEO recommendations and content strategies.
- Define target audience personas and value propositions.
- Use any uploaded business documents to maintain brand voice and product accuracy.

Guidelines:
- Keep your tone persuasive, engaging, and professional.
- Format your responses using clear Markdown (headers, bullet points, bold text).
- Always include actionable next steps for the marketing execution.
"""

class MarketingAgent(BaseAgent):
    """
    Marketing Agent - Handles marketing campaigns, SEO, social media, and copywriting.
    """
    
    def __init__(self):
        super().__init__(
            name="Marketing Agent",
            description="Handles marketing campaigns, SEO, social media, and copywriting."
        )
    
    def _needs_context(self, query: str) -> bool:
        """Simple heuristic to determine if RAG context is needed based on query keywords."""
        keywords = ["brand", "document", "context", "product", "company", "our", "my", "business"]
        query_lower = query.lower()
        return any(kw in query_lower for kw in keywords)

    def _get_rag_context(self, workspace_id: str, query: str) -> str:
        """Fetch relevant documents from the Knowledge Base."""
        try:
            embedding_service = EmbeddingService()
            vector_store = VectorStoreService(embedding_service=embedding_service)
            
            results = vector_store.search(
                query=query,
                top_k=3,  # Top 3 is enough for marketing copy context
                filter_dict={"workspace_id": workspace_id}
            )
            
            if not results:
                return ""
            
            context_parts = []
            for r in results:
                context_parts.append(r["content"])
            
            return "\n\n---\n\n".join(context_parts)
        except Exception as e:
            print(f"[MarketingAgent] RAG search failed: {e}")
            return ""
    
    async def invoke(self, state: AgentState) -> Dict[str, Any]:
        print("--- [Node] Marketing Agent Execution ---")
        
        messages = state.get("messages", [])
        if not messages:
            return {
                "messages": [AIMessage(content="I need a message to work with. How can I help with your marketing?")],
                "current_agent": self.name
            }
        
        last_message = messages[-1].content
        workspace_id = state.get("workspace_id", "")
        business_goal = state.get("business_goal", "Not specified.")
        
        # Determine if we should query the Knowledge Base
        rag_context = ""
        if workspace_id and self._needs_context(last_message):
            print(f"--- [MarketingAgent] Fetching context for: {last_message[:30]}... ---")
            rag_context = self._get_rag_context(workspace_id, last_message)
        
        # Build the prompt
        system_prompt = MARKETING_SYSTEM_PROMPT
        system_prompt += f"\n\nThe business owner's overarching goal is: {business_goal}"
        
        if rag_context:
            system_prompt += f"\n\n<BRAND_CONTEXT>\nThe following is relevant information from the business owner's uploaded documents:\n{rag_context}\n</BRAND_CONTEXT>"
        
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

# Singleton instance for the graph
marketing_agent = MarketingAgent()
