import json
import logging
from uuid import UUID
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from app.models.workflow import WorkflowExecution, WorkflowStatus
from app.models.notification import Notification
from app.ai.orchestrator.graph import orchestrator_graph

logger = logging.getLogger(__name__)

class WorkflowService:
    """Service to handle asynchronous long-running AI workflows."""
    
    @staticmethod
    async def create_workflow(workspace_id: UUID, input_data: Dict[str, Any]) -> WorkflowExecution:
        """Create a new pending workflow in the database."""
        workflow = await WorkflowExecution.create(
            workspace_id=workspace_id,
            status=WorkflowStatus.PENDING,
            input_data=input_data
        )
        return workflow

    @staticmethod
    async def execute_workflow_async(workflow_id: UUID) -> None:
        """Execute the workflow asynchronously, updating DB status."""
        workflow = await WorkflowExecution.get_or_none(id=workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found for execution.")
            return

        try:
            workflow.status = WorkflowStatus.RUNNING
            await workflow.save()

            message_text = workflow.input_data.get("message", "")
            business_goal = workflow.input_data.get("business_goal", "Not specified")
            workspace_id_str = str(workflow.workspace_id)
            user_id_str = workflow.input_data.get("user_id")

            state = {
                "messages": [HumanMessage(content=message_text)],
                "business_goal": business_goal,
                "workspace_id": workspace_id_str,
                "current_agent": "user"
            }
            
            final_state = await orchestrator_graph.ainvoke(state)
            
            final_messages = final_state.get("messages", [])
            last_message_content = final_messages[-1].content if final_messages else "No response generated."
            
            result_data = {
                "response": last_message_content,
                "last_agent": final_state.get("current_agent", "unknown")
            }

            workflow.status = WorkflowStatus.COMPLETED
            workflow.result_data = result_data
            await workflow.save()

            if user_id_str:
                await Notification.create(
                    user_id=UUID(user_id_str),
                    title="Workflow Completed",
                    message=f"Your AI workflow has successfully finished. Agent used: {result_data['last_agent']}"
                )

        except Exception as e:
            logger.exception(f"Workflow {workflow_id} failed: {str(e)}")
            workflow.status = WorkflowStatus.FAILED
            workflow.error_message = str(e)
            await workflow.save()
            
            user_id_str = workflow.input_data.get("user_id") if workflow.input_data else None
            if user_id_str:
                await Notification.create(
                    user_id=UUID(user_id_str),
                    title="Workflow Failed",
                    message="An error occurred while executing your AI workflow."
                )
