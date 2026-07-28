from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from app.models.user import User
from app.models.workspace import Workspace
from app.models.workflow import WorkflowExecution
from app.dependencies.auth import get_current_user
from app.services.workflow_service import WorkflowService

router = APIRouter()

class WorkflowCreateRequest(BaseModel):
    message: str
    business_goal: str

class WorkflowResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    status: str
    input_data: Optional[Dict[str, Any]]
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

@router.post("/workspaces/{workspace_id}/workflows", response_model=WorkflowResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_workflow(
    workspace_id: UUID,
    request: WorkflowCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Trigger a long-running AI workflow asynchronously.
    """
    # 1. Verify workspace exists and user has access
    workspace = await Workspace.get_or_none(id=workspace_id).prefetch_related("organization")
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    if workspace.organization.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")

    # 2. Create DB Record
    input_data = {
        "message": request.message,
        "business_goal": request.business_goal,
        "user_id": str(current_user.id)
    }
    workflow = await WorkflowService.create_workflow(workspace_id=workspace_id, input_data=input_data)
    
    # 3. Queue the background task
    background_tasks.add_task(WorkflowService.execute_workflow_async, workflow.id)
    
    # 4. Return 202 Accepted with the pending workflow ID
    return workflow


@router.get("/workspaces/{workspace_id}/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow_status(
    workspace_id: UUID,
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """
    Check the status and retrieve results of a long-running AI workflow.
    """
    workflow = await WorkflowExecution.get_or_none(id=workflow_id, workspace_id=workspace_id).prefetch_related("workspace__organization")
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    if workflow.workspace.organization.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this workflow")
        
    return workflow
