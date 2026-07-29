from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from app.models.user import User
from app.models.workspace import Workspace
from app.models.workflow import WorkflowExecution, WorkflowStatus
from app.models.document import Document
from app.dependencies.auth import get_current_user

router = APIRouter()

class ReportSummaryItem(BaseModel):
    workflow_id: UUID
    chat_id: UUID  # Alias for workflow_id for frontend convenience
    title: Optional[str]
    date: datetime
    goal: str
    agent: str
    key_insight: str

class ReportSummaryResponse(BaseModel):
    workspace_id: UUID
    generated_at: datetime
    recent_activities: List[ReportSummaryItem]
    knowledge_base_count: int

@router.get("/workspaces/{workspace_id}/reports/summary", response_model=ReportSummaryResponse)
async def get_workspace_report_summary(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Generate an executive summary report aggregating recent AI workflow results 
    and workspace metrics.
    """
    # Verify workspace
    workspace = await Workspace.get_or_none(id=workspace_id).prefetch_related("organization")
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    if workspace.organization.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")

    # Fetch recent COMPLETED workflows (last 10)
    workflows = await WorkflowExecution.filter(
        workspace_id=workspace_id, 
        status=WorkflowStatus.COMPLETED
    ).order_by("-updated_at").limit(10)

    recent_activities = []
    for wf in workflows:
        result = wf.result_data or {}
        input_data = wf.input_data or {}
        
        agent = result.get("last_agent", "Unknown Agent")
        response_text = result.get("response", "")
        
        # Simple extraction for MVP (first 150 chars as key insight)
        insight = response_text[:150] + "..." if len(response_text) > 150 else response_text

        recent_activities.append(
            ReportSummaryItem(
                workflow_id=wf.id,
                chat_id=wf.id,
                title=wf.title,
                date=wf.updated_at,
                goal=input_data.get("business_goal", "No goal specified"),
                agent=agent,
                key_insight=insight
            )
        )

    # Document count
    doc_count = await Document.filter(workspace_id=workspace_id).count()

    return ReportSummaryResponse(
        workspace_id=workspace_id,
        generated_at=datetime.utcnow(),
        recent_activities=recent_activities,
        knowledge_base_count=doc_count
    )
