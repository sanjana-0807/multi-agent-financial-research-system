# tests/test_companies.py
"""
Tests for the Companies API (routes/companies.py, services/company_service.py).

Uses mongomock-motor as an in-memory MongoDB double so tests don't need a
real MongoDB instance, and overrides get_current_user so tests don't need a
real JWT.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from main import app
from core.dependencies import get_current_user
from models.company import Company
from models.comparison_result import ComparisonResult
from models.user import User


class _FakeUser:
    email = "test@example.com"


async def _override_get_current_user():
    return _FakeUser()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client["test_db"],
        document_models=[User, Company, ComparisonResult],
    )
    app.dependency_overrides[get_current_user] = _override_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_company(client):
    response = await client.post(
        "/companies/",
        json={"name": "Apple Inc.", "ticker": "AAPL", "industry": "Technology", "sector": "Consumer Electronics"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["ticker"] == "AAPL"
    assert body["name"] == "Apple Inc."


@pytest.mark.asyncio
async def test_create_company_duplicate_ticker_conflicts(client):
    payload = {"name": "Apple Inc.", "ticker": "AAPL"}
    first = await client.post("/companies/", json=payload)
    assert first.status_code == 201

    second = await client.post("/companies/", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_list_companies(client):
    await client.post("/companies/", json={"name": "Apple Inc.", "ticker": "AAPL"})
    await client.post("/companies/", json={"name": "Microsoft", "ticker": "MSFT"})

    response = await client.get("/companies/")
    assert response.status_code == 200
    tickers = {c["ticker"] for c in response.json()}
    assert tickers == {"AAPL", "MSFT"}


@pytest.mark.asyncio
async def test_get_company_by_ticker(client):
    await client.post("/companies/", json={"name": "Apple Inc.", "ticker": "AAPL"})

    response = await client.get("/companies/ticker/AAPL")
    assert response.status_code == 200
    assert response.json()["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_get_company_by_ticker_not_found(client):
    response = await client.get("/companies/ticker/ZZZZ")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_company(client):
    created = await client.post("/companies/", json={"name": "Apple Inc.", "ticker": "AAPL"})
    company_id = created.json()["id"]

    response = await client.patch(f"/companies/{company_id}", json={"industry": "Tech"})
    assert response.status_code == 200
    assert response.json()["industry"] == "Tech"


@pytest.mark.asyncio
async def test_delete_company(client):
    created = await client.post("/companies/", json={"name": "Apple Inc.", "ticker": "AAPL"})
    company_id = created.json()["id"]

    response = await client.delete(f"/companies/{company_id}")
    assert response.status_code == 204

    follow_up = await client.get(f"/companies/{company_id}")
    assert follow_up.status_code == 404