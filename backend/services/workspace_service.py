from datetime import datetime, timezone

from fastapi import HTTPException, status
from beanie import PydanticObjectId

from models.workspace import Workspace
from models.user import User
from schemas.workspace_schema import WorkspaceCreate, WorkspaceResponse


def _to_response(ws: Workspace) -> WorkspaceResponse:
    data = ws.model_dump()
    data["id"] = str(ws.id)
    data["owner_id"] = str(ws.owner_id)
    return WorkspaceResponse.model_validate(data)


async def create_workspace(payload: WorkspaceCreate, current_user: User) -> WorkspaceResponse:
    ws = Workspace(
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
        objective=payload.objective,
    )
    await ws.insert()
    return _to_response(ws)


async def list_workspaces(current_user: User) -> list[WorkspaceResponse]:
    workspaces = await Workspace.find(Workspace.owner_id == current_user.id).to_list()
    return [_to_response(ws) for ws in workspaces]


async def get_workspace(workspace_id: str, current_user: User) -> Workspace:
    """Returns the raw Workspace document (not the response schema) so
    other services (company_service, comparison_service) can reuse this
    for ownership checks before touching Company/Document records."""
    try:
        obj_id = PydanticObjectId(workspace_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid workspace id")

    ws = await Workspace.get(obj_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if ws.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this workspace")
    return ws


async def get_workspace_response(workspace_id: str, current_user: User) -> WorkspaceResponse:
    ws = await get_workspace(workspace_id, current_user)
    return _to_response(ws)


async def delete_workspace(workspace_id: str, current_user: User) -> None:
    ws = await get_workspace(workspace_id, current_user)
    # NOTE: this does not cascade-delete Companies/Documents that
    # reference this workspace_id. Add that cleanup once company_service
    # exposes a delete-by-workspace helper — flagging so orphaned
    # companies aren't left behind silently.
    await ws.delete()