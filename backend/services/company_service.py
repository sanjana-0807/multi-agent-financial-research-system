from fastapi import HTTPException, status
from beanie import PydanticObjectId

from models.company import Company
from models.user import User
from schemas.company_schema import CompanyCreate, CompanyUpdate, CompanyResponse
from services.workspace_service import get_workspace


def _to_response(company: Company) -> CompanyResponse:
    return CompanyResponse(
        id=str(company.id),
        workspace_id=str(company.workspace_id),
        name=company.name,
        ticker=company.ticker.upper(),
        industry=company.industry,
        sector=company.sector,
        created_at=company.created_at,
    )


async def create_company(payload: CompanyCreate, current_user: User) -> CompanyResponse:
    workspace = await get_workspace(payload.workspace_id, current_user)  # 404/403 if not owner

    existing = await Company.find_one(
        Company.ticker == payload.ticker.upper(),
        Company.workspace_id == workspace.id,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Company with ticker '{payload.ticker.upper()}' already exists in this workspace",
        )

    company = Company(
        workspace_id=workspace.id,
        name=payload.name,
        ticker=payload.ticker.upper(),
        industry=payload.industry,
        sector=payload.sector,
    )
    await company.insert()
    return _to_response(company)


async def list_companies(workspace_id: str, current_user: User, skip: int = 0, limit: int = 50) -> list[CompanyResponse]:
    workspace = await get_workspace(workspace_id, current_user)
    companies = (
        await Company.find(Company.workspace_id == workspace.id)
        .skip(skip)
        .limit(limit)
        .to_list()
    )
    return [_to_response(c) for c in companies]


async def _get_owned_company(company_id: str, current_user: User) -> Company:
    """Fetch a company and verify current_user owns its workspace."""
    try:
        obj_id = PydanticObjectId(company_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid company id")

    company = await Company.get(obj_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Raises 404/403 if the workspace doesn't exist or isn't owned by current_user
    await get_workspace(str(company.workspace_id), current_user)
    return company


async def get_company(company_id: str, current_user: User) -> CompanyResponse:
    company = await _get_owned_company(company_id, current_user)
    return _to_response(company)


async def get_company_by_ticker(ticker: str, workspace_id: str, current_user: User) -> CompanyResponse:
    workspace = await get_workspace(workspace_id, current_user)
    company = await Company.find_one(
        Company.ticker == ticker.upper(),
        Company.workspace_id == workspace.id,
    )
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{ticker.upper()}' not found")
    return _to_response(company)


async def update_company(company_id: str, payload: CompanyUpdate, current_user: User) -> CompanyResponse:
    company = await _get_owned_company(company_id, current_user)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    await company.save()
    return _to_response(company)


async def delete_company(company_id: str, current_user: User) -> None:
    company = await _get_owned_company(company_id, current_user)
    await company.delete()