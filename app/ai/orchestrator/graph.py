from typing import Literal
from langgraph.graph import StateGraph, END
from app.ai.orchestrator.state import AgentState
from app.ai.orchestrator.router import OrchestratorRouter
from app.ai.agents.strategy_agent import strategy_agent
from app.ai.agents.marketing_agent import marketing_agent
from app.ai.agents.sales_agent import sales_agent
from app.ai.agents.dummy_agents import (
    finance_agent, operations_agent, customer_success_agent
)
from langchain_core.messages import AIMessage

# Initialize Router
router = OrchestratorRouter()

# Define graph builder
builder = StateGraph(AgentState)

# 1. Define nodes
async def route_node(state: AgentState):
    return await router.route(state)

async def general_chat_node(state: AgentState):
    # Fallback for general conversation
    print("--- [Node] General Chat ---")
    response = AIMessage(content="I am OrbitOS AI. How can I help you manage your business today?")
    return {"messages": [response], "current_agent": "orchestrator"}

# Add nodes to graph
builder.add_node("router", route_node)
builder.add_node("strategy", strategy_agent.invoke)
builder.add_node("marketing", marketing_agent.invoke)
builder.add_node("sales", sales_agent.invoke)
builder.add_node("finance", finance_agent.invoke)
builder.add_node("operations", operations_agent.invoke)
builder.add_node("customer_success", customer_success_agent.invoke)
builder.add_node("general", general_chat_node)

# 2. Define conditional routing logic
def router_condition(state: AgentState) -> Literal["strategy", "marketing", "sales", "finance", "operations", "customer_success", "general", "__end__"]:
    route = state.get("next_step", "general")
    if route == "end":
        return END
    return route

# 3. Add Edges
builder.set_entry_point("router")
builder.add_conditional_edges("router", router_condition)

# All specialized agents return to the user (END) for this phase
# (Future phases might route them back to the orchestrator for review)
builder.add_edge("strategy", END)
builder.add_edge("marketing", END)
builder.add_edge("sales", END)
builder.add_edge("finance", END)
builder.add_edge("operations", END)
builder.add_edge("customer_success", END)
builder.add_edge("general", END)

# Compile graph
# We handle long-term Redis memory at the API layer to keep the graph simple
orchestrator_graph = builder.compile()
