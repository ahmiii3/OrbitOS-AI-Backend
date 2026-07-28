from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict
from uuid import UUID
from datetime import datetime

from app.models.user import User
from app.models.workspace import Workspace
from app.models.workflow import WorkflowExecution, WorkflowStatus
from app.models.document import Document
from app.models.notification import Notification
from app.dependencies.auth import get_current_user
from app.api.v1.endpoints.reports import ReportSummaryItem
from app.api.v1.endpoints.notifications import NotificationResponse

router = APIRouter()

class DashboardSummaryResponse(BaseModel):
    active_workflows: int
    completed_workflows: int
    failed_workflows: int
    uploaded_documents: int
    recent_activities: List[ReportSummaryItem]
    recent_notifications: List[NotificationResponse]
    most_used_agents: Dict[str, int]

@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user)
):
    """
    Get aggregated dashboard metrics for the logged-in user.
    Fetches cross-workspace metrics based on organizations the user owns.
    """
    # 1. Fetch user's workspaces
    # For MVP, we'll fetch workspaces from the org the user owns.
    from app.models.organization import Organization
    orgs = await Organization.filter(owner=current_user).prefetch_related("workspaces")
    workspace_ids = []
    for org in orgs:
        for ws in org.workspaces:
            workspace_ids.append(ws.id)

    # If no workspaces, return zeros
    if not workspace_ids:
        return DashboardSummaryResponse(
            active_workflows=0,
            completed_workflows=0,
            failed_workflows=0,
            uploaded_documents=0,
            recent_activities=[],
            recent_notifications=[],
            most_used_agents={}
        )

    # 2. Counts
    active_workflows = await WorkflowExecution.filter(workspace_id__in=workspace_ids, status=WorkflowStatus.RUNNING).count()
    completed_workflows = await WorkflowExecution.filter(workspace_id__in=workspace_ids, status=WorkflowStatus.COMPLETED).count()
    failed_workflows = await WorkflowExecution.filter(workspace_id__in=workspace_ids, status=WorkflowStatus.FAILED).count()
    uploaded_documents = await Document.filter(workspace_id__in=workspace_ids).count()

    # 3. Recent Activities (from workflows)
    recent_wfs = await WorkflowExecution.filter(
        workspace_id__in=workspace_ids, 
        status=WorkflowStatus.COMPLETED
    ).order_by("-updated_at").limit(5)
    
    recent_activities = []
    for wf in recent_wfs:
        result = wf.result_data or {}
        input_data = wf.input_data or {}
        agent = result.get("last_agent", "Unknown Agent")
        response_text = result.get("response", "")
        insight = response_text[:150] + "..." if len(response_text) > 150 else response_text
        recent_activities.append(
            ReportSummaryItem(
                workflow_id=wf.id,
                date=wf.updated_at,
                goal=input_data.get("business_goal", "No goal specified"),
                agent=agent,
                key_insight=insight
            )
        )

    # 4. Recent Notifications
    recent_notifs = await Notification.filter(
        user=current_user,
        is_read=False
    ).order_by("-created_at").limit(5)
    
    notifications = [
        NotificationResponse(
            id=n.id,
            title=n.title,
            message=n.message,
            is_read=n.is_read,
            created_at=n.created_at
        ) for n in recent_notifs
    ]

    # 5. Most Used Agents (fetch last 100 completed workflows to tally)
    last_100_wfs = await WorkflowExecution.filter(
        workspace_id__in=workspace_ids, 
        status=WorkflowStatus.COMPLETED
    ).order_by("-updated_at").limit(100)
    
    agent_tally = {}
    for wf in last_100_wfs:
        agent = (wf.result_data or {}).get("last_agent", "Unknown")
        agent_tally[agent] = agent_tally.get(agent, 0) + 1

    return DashboardSummaryResponse(
        active_workflows=active_workflows,
        completed_workflows=completed_workflows,
        failed_workflows=failed_workflows,
        uploaded_documents=uploaded_documents,
        recent_activities=recent_activities,
        recent_notifications=notifications,
        most_used_agents=agent_tally
    )
