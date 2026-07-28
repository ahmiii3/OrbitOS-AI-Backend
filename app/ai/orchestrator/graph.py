from typing import Literal
from langgraph.graph import StateGraph, END
from app.ai.orchestrator.state import AgentState
from app.ai.orchestrator.router import OrchestratorRouter
from app.ai.agents.strategy_agent import strategy_agent
from app.ai.agents.marketing_agent import marketing_agent
from app.ai.agents.sales_agent import sales_agent
from app.ai.agents.finance_agent import finance_agent
from app.ai.agents.operations_agent import operations_agent
from app.ai.agents.customer_success_agent import customer_success_agent
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

# All specialized agents return control back to the orchestrator (router)
# The router will then decide if the workflow is complete and route to END
builder.add_edge("strategy", "router")
builder.add_edge("marketing", "router")
builder.add_edge("sales", "router")
builder.add_edge("finance", "router")
builder.add_edge("operations", "router")
builder.add_edge("customer_success", "router")
builder.add_edge("general", "router")

# Compile graph
# We handle long-term Redis memory at the API layer to keep the graph simple
orchestrator_graph = builder.compile()
