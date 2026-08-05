from fastapi import APIRouter, Depends, Query

from schemas.company_schema import CompanyCreate, CompanyUpdate, CompanyResponse
from services import company_service
from core.dependencies import get_current_user

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post("/", response_model=CompanyResponse, status_code=201)
async def create_company(
    payload: CompanyCreate,
    current_user=Depends(get_current_user),
):
    return await company_service.create_company(payload)


@router.get("/", response_model=list[CompanyResponse])
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    current_user=Depends(get_current_user),
):
    return await company_service.list_companies(skip=skip, limit=limit)


@router.get("/ticker/{ticker}", response_model=CompanyResponse)
async def get_company_by_ticker(
    ticker: str,
    current_user=Depends(get_current_user),
):
    return await company_service.get_company_by_ticker(ticker)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    current_user=Depends(get_current_user),
):
    return await company_service.get_company(company_id)


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    payload: CompanyUpdate,
    current_user=Depends(get_current_user),
):
    return await company_service.update_company(company_id, payload)


@router.delete("/{company_id}", status_code=204)
async def delete_company(
    company_id: str,
    current_user=Depends(get_current_user),
):
    await company_service.delete_company(company_id)