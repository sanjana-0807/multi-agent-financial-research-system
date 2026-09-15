from datetime import datetime, timezone

from fastapi import HTTPException, status
from beanie import PydanticObjectId

from models.workspace import Workspace
from models.user import User
from models.company import Company
from models.document import DocumentModel
from schemas.workspace_schema import WorkspaceCreate, WorkspaceResponse


async def _document_count_for_workspace(workspace_id) -> int:
    """
    Count documents belonging to companies inside a workspace.

    Relationship:
        Workspace -> Company -> Document
    """

    companies = await Company.find(
        Company.workspace_id == workspace_id
    ).to_list()

    if not companies:
        return 0

    company_ids = [str(company.id) for company in companies]

    return await DocumentModel.find(
        {
            "company_id": {"$in": company_ids}
        }
    ).count()


async def _to_response(ws: Workspace) -> WorkspaceResponse:
    data = ws.model_dump()

    data["id"] = str(ws.id)
    data["owner_id"] = str(ws.owner_id)

    # Add the actual number of uploaded documents
    # belonging to companies in this workspace.
    data["document_count"] = await _document_count_for_workspace(
        ws.id
    )

    return WorkspaceResponse.model_validate(data)


async def create_workspace(
    payload: WorkspaceCreate,
    current_user: User,
) -> WorkspaceResponse:

    ws = Workspace(
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
        objective=payload.objective,
    )

    await ws.insert()

    return await _to_response(ws)


async def list_workspaces(
    current_user: User,
) -> list[WorkspaceResponse]:

    workspaces = await Workspace.find(
        Workspace.owner_id == current_user.id
    ).to_list()

    return [
        await _to_response(ws)
        for ws in workspaces
    ]


async def get_workspace(
    workspace_id: str,
    current_user: User,
) -> Workspace:
    """
    Returns the raw Workspace document.

    Other services can reuse this for ownership checks
    before accessing Company/Document records.
    """

    try:
        obj_id = PydanticObjectId(workspace_id)

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid workspace id",
        )

    ws = await Workspace.get(obj_id)

    if not ws:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
        )

    if ws.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this workspace",
        )

    return ws


async def get_workspace_response(
    workspace_id: str,
    current_user: User,
) -> WorkspaceResponse:

    ws = await get_workspace(
        workspace_id,
        current_user,
    )

    return await _to_response(ws)


async def delete_workspace(
    workspace_id: str,
    current_user: User,
) -> None:

    ws = await get_workspace(
        workspace_id,
        current_user,
    )

    # NOTE: this does not cascade-delete Companies/Documents
    # that reference this workspace through their company.
    await ws.delete()