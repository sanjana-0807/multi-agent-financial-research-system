from fastapi import APIRouter, Depends

from schemas.workspace_schema import WorkspaceCreate, WorkspaceResponse
from services import workspace_service
from core.dependencies import get_current_user

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.post("/", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    payload: WorkspaceCreate,
    current_user=Depends(get_current_user),
):
    return await workspace_service.create_workspace(payload, current_user)


@router.get("/", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user=Depends(get_current_user),
):
    return await workspace_service.list_workspaces(current_user)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user=Depends(get_current_user),
):
    return await workspace_service.get_workspace_response(workspace_id, current_user)


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: str,
    current_user=Depends(get_current_user),
):
    await workspace_service.delete_workspace(workspace_id, current_user)