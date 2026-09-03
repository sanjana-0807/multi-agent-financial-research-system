# tests/test_comparison_agent.py
"""
Tests for the comparison API and service (routes/comparison.py,
services/comparison_service.py) now that the real Comparison Agent is
wired in.

Two things are mocked so these stay fast unit tests instead of
integration tests requiring a running Ollama instance and real
uploaded documents:

  - agents.comparison_agent.data_fetcher.get_extractions_for_companies
    is monkeypatched to return canned ExtractionResponse-shaped dicts,
    the same shape agents/extraction_agent/tasks.py:run_extraction
    returns.
  - services.comparison_service.run_comparison_narrative is
    monkeypatched to avoid a real Ollama call.
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


def _fake_extraction(company: str, revenue: float, net_profit: float,
                      assets: float, liabilities: float) -> dict:
    return {
        "metric_id": "M001",
        "document_id": "D_TEST",
        "company": company,
        "fiscal_year": 2025,
        "revenue": revenue,
        "net_profit": net_profit,
        "assets": assets,
        "liabilities": liabilities,
        "cash_flow": net_profit * 1.1,
        "eps": 2.5,
        "ratios": {
            "current_ratio": 1.5,
            "debt_to_equity": liabilities / (assets - liabilities),
            "net_profit_margin": (net_profit / revenue) * 100,
        },
    }


@pytest.fixture(autouse=True)
def mock_narrative(monkeypatch):
    async def _fake_narrative(comparison_context: str) -> dict:
        return {
            "summary": "AAPL outperforms MSFT on revenue and margin.",
            "highlights": [
                {"metric": "revenue", "finding": "AAPL leads on revenue."}
            ],
        }

    monkeypatch.setattr(
        comparison_service, "run_comparison_narrative", _fake_narrative
    )


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
async def test_run_comparison_without_linked_documents_raises_422(monkeypatch):
    """
    Companies with no linked/processed document must produce a clear
    error, never fabricated numbers.
    """
    apple = await _make_company("Apple Inc.", "AAPL")
    msft = await _make_company("Microsoft", "MSFT")

    async def _no_data(companies):
        return {}, [c.ticker for c in companies]

    monkeypatch.setattr(
        comparison_service, "get_extractions_for_companies", _no_data
    )

    with pytest.raises(Exception) as exc_info:
        await comparison_service.run_comparison([str(apple.id), str(msft.id)])

    assert "422" in str(exc_info.value) or getattr(
        exc_info.value, "status_code", None
    ) == 422


@pytest.mark.asyncio
async def test_run_comparison_with_extracted_data_returns_completed_result():
    apple = await _make_company("Apple Inc.", "AAPL")
    msft = await _make_company("Microsoft", "MSFT")

    extracted_data = {
        "AAPL": _fake_extraction("Apple Inc.", 100_000, 25_000, 400_000, 200_000),
        "MSFT": _fake_extraction("Microsoft", 80_000, 15_000, 350_000, 180_000),
    }

    result = await comparison_service.run_comparison(
        [str(apple.id), str(msft.id)], extracted_data=extracted_data
    )

    assert result.status == "completed"
    assert set(result.tickers) == {"AAPL", "MSFT"}
    assert result.summary == "AAPL outperforms MSFT on revenue and margin."

    ratio_names = {r.ratio_name for r in result.ratio_comparisons}
    assert "revenue" in ratio_names
    assert "debt_to_equity" in ratio_names

    revenue_comparison = next(
        r for r in result.ratio_comparisons if r.ratio_name == "revenue"
    )
    assert revenue_comparison.best_performer == "AAPL"  # higher revenue wins
    assert revenue_comparison.values == {"AAPL": 100_000.0, "MSFT": 80_000.0}

    liabilities_comparison = next(
        r for r in result.ratio_comparisons if r.ratio_name == "liabilities"
    )
    assert liabilities_comparison.best_performer == "MSFT"  # lower liabilities wins

    assert len(result.industry_rankings) == 2
    ranks = sorted(r.rank for r in result.industry_rankings)
    assert ranks == [1, 2]


@pytest.mark.asyncio
async def test_comparison_run_endpoint_with_missing_documents_returns_422(client):
    apple = await _make_company("Apple Inc.", "AAPL")
    msft = await _make_company("Microsoft", "MSFT")

    response = await client.post(
        "/comparison/run",
        json={"company_ids": [str(apple.id), str(msft.id)]},
    )
    # No documents linked to either company in this test DB.
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_comparison_run_endpoint_rejects_single_company(client):
    apple = await _make_company("Apple Inc.", "AAPL")

    response = await client.post("/comparison/run", json={"company_ids": [str(apple.id)]})
    assert response.status_code == 422  # fails ComparisonRequest's min_length=2


@pytest.mark.asyncio
async def test_get_comparison_endpoint(client):
    apple = await _make_company("Apple Inc.", "AAPL")
    msft = await _make_company("Microsoft", "MSFT")

    extracted_data = {
        "AAPL": _fake_extraction("Apple Inc.", 100_000, 25_000, 400_000, 200_000),
        "MSFT": _fake_extraction("Microsoft", 80_000, 15_000, 350_000, 180_000),
    }
    result = await comparison_service.run_comparison(
        [str(apple.id), str(msft.id)], extracted_data=extracted_data
    )

    response = await client.get(f"/comparison/{result.id}")
    assert response.status_code == 200
    assert response.json()["id"] == result.id


@pytest.mark.asyncio
async def test_get_comparison_not_found(client):
    response = await client.get("/comparison/000000000000000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_comparisons_endpoint(client):
    apple = await _make_company("Apple Inc.", "AAPL")
    msft = await _make_company("Microsoft", "MSFT")

    extracted_data = {
        "AAPL": _fake_extraction("Apple Inc.", 100_000, 25_000, 400_000, 200_000),
        "MSFT": _fake_extraction("Microsoft", 80_000, 15_000, 350_000, 180_000),
    }
    await comparison_service.run_comparison(
        [str(apple.id), str(msft.id)], extracted_data=extracted_data
    )

    response = await client.get("/comparison/")
    assert response.status_code == 200
    assert len(response.json()) == 1