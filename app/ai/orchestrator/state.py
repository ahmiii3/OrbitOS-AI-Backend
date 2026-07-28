import operator
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    Central shared state for the LangGraph Orchestrator.
    Every node (agent) reads from and writes to this state.
    """
    # Conversation history: operator.add ensures messages are appended, not overwritten
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # The overarching business goal that all agents work towards
    business_goal: str 
    
    # Context IDs for fetching RAG data or saving to DB
    workspace_id: str
    organization_id: str
    
    # Routing state: which agent is currently active or where to go next
    current_agent: str
    next_step: str
