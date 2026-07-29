from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
import io
import markdown
from xhtml2pdf import pisa

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
    title: Optional[str]
    status: str
    messages: Optional[List[Dict[str, Any]]]
    input_data: Optional[Dict[str, Any]]
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

class WorkflowListResponse(BaseModel):
    id: UUID
    title: Optional[str]
    status: str
    preview: str
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
    workspace = await Workspace.get_or_none(id=workspace_id).prefetch_related("organization")
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    if workspace.organization.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")

    input_data = {
        "message": request.message,
        "business_goal": request.business_goal,
        "user_id": str(current_user.id)
    }
    workflow = await WorkflowService.create_workflow(workspace_id=workspace_id, input_data=input_data)
    
    background_tasks.add_task(WorkflowService.execute_workflow_async, workflow.id)
    return workflow

@router.get("/workspaces/{workspace_id}/workflows", response_model=List[WorkflowListResponse])
async def list_workflows(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """
    List all workflows/chats in a workspace.
    """
    workspace = await Workspace.get_or_none(id=workspace_id).prefetch_related("organization")
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.organization.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    workflows = await WorkflowExecution.filter(workspace_id=workspace_id).order_by("-created_at")
    
    response = []
    for wf in workflows:
        preview = "New workflow..."
        if wf.messages and len(wf.messages) > 0:
            content = str(wf.messages[0].get("content", ""))
            preview = content[:100] + "..." if len(content) > 100 else content
            
        response.append({
            "id": wf.id,
            "title": wf.title,
            "status": wf.status,
            "preview": preview,
            "created_at": wf.created_at,
            "updated_at": wf.updated_at
        })
    return response

@router.get("/workspaces/{workspace_id}/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow_status(
    workspace_id: UUID,
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """
    Check the status and retrieve full chat history of a long-running AI workflow.
    """
    workflow = await WorkflowExecution.get_or_none(id=workflow_id, workspace_id=workspace_id).prefetch_related("workspace__organization")
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    if workflow.workspace.organization.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this workflow")
        
    return workflow

@router.delete("/workspaces/{workspace_id}/workflows/{workflow_id}", status_code=status.HTTP_200_OK)
async def delete_workflow(
    workspace_id: UUID,
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a workflow from history.
    """
    workflow = await WorkflowExecution.get_or_none(id=workflow_id, workspace_id=workspace_id).prefetch_related("workspace__organization")
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.workspace.organization.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await workflow.delete()
    return {"message": "Workflow deleted successfully"}

@router.get("/workspaces/{workspace_id}/workflows/{workflow_id}/pdf")
async def export_workflow_pdf(
    workspace_id: UUID,
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """
    Export the completed workflow conversation as a professional PDF.
    """
    workflow = await WorkflowExecution.get_or_none(id=workflow_id, workspace_id=workspace_id).prefetch_related("workspace__organization")
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.workspace.organization.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if workflow.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Workflow is not yet completed.")

    # Format the messages as HTML
    chat_html = ""
    for msg in (workflow.messages or []):
        role = msg.get("role", "Unknown").title()
        content_md = msg.get("content", "")
        agent = msg.get("agent", "")
        
        content_html = markdown.markdown(content_md)
        
        if role == "User":
            chat_html += f"""
            <div class="message user-message">
                <strong>User</strong>
                <div>{content_html}</div>
            </div>
            """
        else:
            agent_str = f" ({agent})" if agent else ""
            chat_html += f"""
            <div class="message ai-message">
                <strong>AI Assistant{agent_str}</strong>
                <div>{content_html}</div>
            </div>
            """

    business_goal = (workflow.input_data or {}).get("business_goal", "Not Specified")
    
    html_template = f"""
    <html>
    <head>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
                @frame footer {{
                    -pdf-frame-content: footer_content;
                    bottom: 1cm;
                    height: 1cm;
                    text-align: right;
                    font-size: 10pt;
                    color: #777;
                }}
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                color: #333;
                line-height: 1.5;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 5px;
            }}
            .meta-data {{
                margin-bottom: 20px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                font-size: 11pt;
            }}
            .message {{
                margin-bottom: 15px;
                padding: 15px;
                border-radius: 8px;
            }}
            .user-message {{
                background-color: #e8f4f8;
                border-left: 4px solid #3498db;
            }}
            .ai-message {{
                background-color: #fdfdfd;
                border: 1px solid #ddd;
                border-left: 4px solid #2ecc71;
            }}
            strong {{
                display: block;
                margin-bottom: 5px;
                color: #2c3e50;
            }}
        </style>
    </head>
    <body>
        <h1>OrbitOS AI - Action Plan</h1>
        <div class="meta-data">
            <strong>Workspace:</strong> {workflow.workspace.name}<br/>
            <strong>Title:</strong> {workflow.title}<br/>
            <strong>Business Goal:</strong> {business_goal}<br/>
            <strong>Date:</strong> {workflow.created_at.strftime("%B %d, %Y - %H:%M:%S UTC")}
        </div>
        
        <h2>Conversation History</h2>
        {chat_html}

        <div id="footer_content">
            Generated by OrbitOS AI
        </div>
    </body>
    </html>
    """

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        io.BytesIO(html_template.encode("utf-8")),
        dest=pdf_buffer
    )

    if pisa_status.err:
        raise HTTPException(status_code=500, detail="Error generating PDF")

    pdf_buffer.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="OrbitOS_Report_{workflow.id}.pdf"'
    }
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)
