from datetime import datetime, timezone

from fastapi import HTTPException, status
from beanie import PydanticObjectId

from models.workspace import Workspace
from models.user import User
from models.company import Company
from models.document import DocumentModel
from schemas.workspace_schema import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse


async def _document_count_for_workspace(workspace_id) -> int:
    companies = await Company.find(
        Company.workspace_id == workspace_id
    ).to_list()

    if not companies:
        return 0

    company_ids = [str(company.id) for company in companies]

    docs = await DocumentModel.find(
        {
            "company_id": {"$in": company_ids},
            "status": "indexed",
        }
    ).to_list()

    return len({doc.company_id for doc in docs})


async def _to_response(ws: Workspace) -> WorkspaceResponse:
    data = ws.model_dump()

    data["id"] = str(ws.id)
    data["owner_id"] = str(ws.owner_id)
    data["document_count"] = await _document_count_for_workspace(ws.id)

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


async def get_workspace_response(
    workspace_id: str,
    current_user: User,
) -> WorkspaceResponse:

    ws = await get_workspace(workspace_id, current_user)
    return await _to_response(ws)


async def update_workspace(
    workspace_id: str,
    payload: WorkspaceUpdate,
    current_user: User,
) -> WorkspaceResponse:

    ws = await get_workspace(workspace_id, current_user)

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(ws, field, value)

    ws.updated_at = datetime.now(timezone.utc)

    await ws.save()

    return await _to_response(ws)


async def list_workspace_documents(
    workspace_id: str,
    current_user: User,
) -> list[dict]:
    """
    Return every document belonging to companies inside this
    workspace, for the Settings > Manage Disclosures modal.
    """

    ws = await get_workspace(workspace_id, current_user)  # ownership check

    companies = await Company.find(
        Company.workspace_id == ws.id
    ).to_list()

    if not companies:
        return []

    company_ids = [str(company.id) for company in companies]

    documents = await DocumentModel.find(
        {"company_id": {"$in": company_ids}}
    ).sort("-created_at").to_list()

    return [
        {
            "document_id": doc.document_id,
            "filename": doc.filename,
            "file_size": doc.file_size,
            "page_count": doc.page_count,
            "chunk_count": doc.chunk_count,
            "status": doc.status,
            "company_id": doc.company_id,
            "created_at": doc.created_at,
        }
        for doc in documents
    ]


async def delete_workspace(
    workspace_id: str,
    current_user: User,
) -> None:

    ws = await get_workspace(workspace_id, current_user)
    await ws.delete()