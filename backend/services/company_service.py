from fastapi import HTTPException, status
from beanie import PydanticObjectId

from models.company import Company
from schemas.company_schema import CompanyCreate, CompanyUpdate, CompanyResponse


def _to_response(company: Company) -> CompanyResponse:
    return CompanyResponse(
        id=str(company.id),
        name=company.name,
        ticker=company.ticker.upper(),
        industry=company.industry,
        sector=company.sector,
        created_at=company.created_at,
    )


async def create_company(payload: CompanyCreate) -> CompanyResponse:
    existing = await Company.find_one(Company.ticker == payload.ticker.upper())
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Company with ticker '{payload.ticker.upper()}' already exists",
        )

    company = Company(
        name=payload.name,
        ticker=payload.ticker.upper(),
        industry=payload.industry,
        sector=payload.sector,
    )
    await company.insert()
    return _to_response(company)


async def list_companies(skip: int = 0, limit: int = 50) -> list[CompanyResponse]:
    companies = await Company.find_all().skip(skip).limit(limit).to_list()
    return [_to_response(c) for c in companies]


async def get_company(company_id: str) -> CompanyResponse:
    try:
        obj_id = PydanticObjectId(company_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid company id")

    company = await Company.get(obj_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return _to_response(company)


async def get_company_by_ticker(ticker: str) -> CompanyResponse:
    company = await Company.find_one(Company.ticker == ticker.upper())
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{ticker.upper()}' not found")
    return _to_response(company)


async def update_company(company_id: str, payload: CompanyUpdate) -> CompanyResponse:
    try:
        obj_id = PydanticObjectId(company_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid company id")

    company = await Company.get(obj_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    await company.save()
    return _to_response(company)


async def delete_company(company_id: str) -> None:
    try:
        obj_id = PydanticObjectId(company_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid company id")

    company = await Company.get(obj_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    await company.delete()