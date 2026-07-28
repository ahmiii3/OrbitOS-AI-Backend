from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
from redis.asyncio import Redis
from app.dependencies.auth import get_current_active_user
from app.dependencies.redis import get_redis_client
from app.models.user import User
from app.ai.orchestrator.graph import orchestrator_graph
from app.ai.memory.redis_memory import RedisMemory
from langchain_core.messages import HumanMessage

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    business_goal: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    agent: str

@router.post(
    "/workspaces/{workspace_id}/chat",
    response_model=ChatResponse,
    summary="Interact with AI Orchestrator"
)
async def chat_with_orchestrator(
    workspace_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    redis_client: Redis = Depends(get_redis_client)
):
    """
    Main entry point for executing tasks via the AI Orchestrator.
    Pass a message, and the Orchestrator will route it to the proper specialized agent.
    """
    memory = RedisMemory(redis_client)
    session_id = f"{workspace_id}_{current_user.id}"
    
    # 1. Load previous state from Redis
    state = await memory.get_context(session_id)
    
    # 2. Update state with new inputs
    if request.business_goal:
        state["business_goal"] = request.business_goal
    
    # Initialize message list if empty
    if "messages" not in state:
        state["messages"] = []
        
    state["workspace_id"] = workspace_id
    
    # We append the new message to pass into the graph
    new_message = HumanMessage(content=request.message)
    # Actually, in LangGraph, passing a dict with 'messages' containing the new message
    # will trigger the operator.add automatically.
    input_state = {**state, "messages": [new_message]}
    
    # 3. Execute LangGraph Orchestrator
    try:
        final_state = await orchestrator_graph.ainvoke(input_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    # 4. Save the new state back to Redis
    # LangGraph returns the fully updated state dict
    await memory.save_context(session_id, final_state)
    
    # 5. Extract the final response
    last_msg = final_state["messages"][-1].content if final_state.get("messages") else "No response generated."
    agent = final_state.get("current_agent", "orchestrator")
    
    return ChatResponse(response=last_msg, agent=agent)
