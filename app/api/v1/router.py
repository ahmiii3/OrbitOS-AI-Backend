from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, organizations, workspaces, knowledge, workflows

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(workspaces.router, tags=["Workspaces"])
api_router.include_router(knowledge.router, tags=["Knowledge Base"])
api_router.include_router(workflows.router, tags=["AI Orchestrator Workflows"])
