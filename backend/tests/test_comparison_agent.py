# tests/test_comparison_agent.py
"""
Tests for the comparison API and service (routes/comparison.py,
services/comparison_service.py).

These test the Milestone 2 placeholder-ratio behavior. Once the real
Comparison Agent lands in Milestone 3, add cases that pass `extracted_data`
into comparison_service.run_comparison and assert it overrides the
placeholder values.
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
from services import comparison_service


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


async def _make_company(name: str, ticker: str) -> Company:
    company = Company(name=name, ticker=ticker)
    await company.insert()
    return company


@pytest.mark.asyncio
async def test_run_comparison_requires_at_least_two_companies():
    apple = await _make_company("Apple Inc.", "AAPL")

    with pytest.raises(Exception):
        await comparison_service.run_comparison([str(apple.id)])


@pytest.mark.asyncio
async def test_run_comparison_rejects_unknown_company():
    apple = await _make_company("Apple Inc.", "AAPL")

    with pytest.raises(Exception):
        await comparison_service.run_comparison([str(apple.id), "000000000000000000000000"])


@pytest.mark.asyncio
async def test_run_comparison_returns_completed_result_with_ratios():
    apple = await _make_company("Apple Inc.", "AAPL")
    msft = await _make_company("Microsoft", "MSFT")

    result = await comparison_service.run_comparison([str(apple.id), str(msft.id)])

    assert result.status == "completed"
    assert set(result.tickers) == {"AAPL", "MSFT"}
    assert len(result.ratio_comparisons) == 3  # current_ratio, debt_to_equity, net_profit_margin
    for ratio in result.ratio_comparisons:
        assert set(ratio.values.keys()) == {"AAPL", "MSFT"}
        assert ratio.best_performer in {"AAPL", "MSFT"}
    assert len(result.industry_rankings) == 2
    ranks = sorted(r.rank for r in result.industry_rankings)
    assert ranks == [1, 2]


@pytest.mark.asyncio
async def test_run_comparison_is_deterministic():
    apple = await _make_company("Apple Inc.", "AAPL")
    msft = await _make_company("Microsoft", "MSFT")

    first = await comparison_service.run_comparison([str(apple.id), str(msft.id)])
    second = await comparison_service.run_comparison([str(apple.id), str(msft.id)])

    first_values = {r.ratio_name: r.values for r in first.ratio_comparisons}
    second_values = {r.ratio_name: r.values for r in second.ratio_comparisons}
    assert first_values == second_values


@pytest.mark.asyncio
async def test_comparison_run_endpoint(client):
    apple = await _make_company("Apple Inc.", "AAPL")
    msft = await _make_company("Microsoft", "MSFT")

    response = await client.post(
        "/comparison/run",
        json={"company_ids": [str(apple.id), str(msft.id)]},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert set(body["tickers"]) == {"AAPL", "MSFT"}


@pytest.mark.asyncio
async def test_comparison_run_endpoint_rejects_single_company(client):
    apple = await _make_company("Apple Inc.", "AAPL")

    response = await client.post("/comparison/run", json={"company_ids": [str(apple.id)]})
    assert response.status_code == 422  # fails ComparisonRequest's min_length=2


@pytest.mark.asyncio
async def test_get_comparison_endpoint(client):
    apple = await _make_company("Apple Inc.", "AAPL")
    msft = await _make_company("Microsoft", "MSFT")

    created = await client.post(
        "/comparison/run",
        json={"company_ids": [str(apple.id), str(msft.id)]},
    )
    comparison_id = created.json()["id"]

    response = await client.get(f"/comparison/{comparison_id}")
    assert response.status_code == 200
    assert response.json()["id"] == comparison_id


@pytest.mark.asyncio
async def test_get_comparison_not_found(client):
    response = await client.get("/comparison/000000000000000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_comparisons_endpoint(client):
    apple = await _make_company("Apple Inc.", "AAPL")
    msft = await _make_company("Microsoft", "MSFT")
    await client.post("/comparison/run", json={"company_ids": [str(apple.id), str(msft.id)]})

    response = await client.get("/comparison/")
    assert response.status_code == 200
    assert len(response.json()) == 1