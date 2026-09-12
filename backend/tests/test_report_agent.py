# tests/test_report_agent.py
"""
Tests for the Report Agent (services/report_service.py,
agents/report_agent/*).

Mocked, for the same reasons test_comparison_agent.py mocks its
external calls -- these stay fast unit tests instead of integration
tests requiring a running Ollama instance, real uploaded documents,
and a real Atlas/GridFS connection:

  - services.report_service.get_workspace is monkeypatched (no real
    Workspace document needed -- we just need something with a
    matching `.id`).
  - services.report_service.get_latest_document_for_company and
    fetch_document_text are monkeypatched, the same way
    test_comparison_agent.py avoids exercising real document
    resolution.
  - services.report_service.run_extraction is monkeypatched to return
    a canned ExtractionResponse-shaped dict (real run_extraction()
    calls Ollama).
  - services.report_service.run_report_narrative is monkeypatched to
    avoid a real Ollama call (mirrors run_comparison_narrative being
    mocked in the comparison tests).
  - services.report_service.build_report_pdf is monkeypatched to
    avoid exercising reportlab in every test; report_builder has its
    own focused tests below.
  - services.report_service._gridfs_bucket is monkeypatched with an
    in-memory fake, since mongomock_motor does not implement GridFS.

NOTE: importing `main` here assumes routes/report.py has been wired
into main.py (see the 3 manual steps called out when this agent was
delivered). The route-level test at the bottom will 404 if that
hasn't been done yet -- the service-level tests do not depend on it.
"""
from types import SimpleNamespace

import pytest
import pytest_asyncio
from bson import ObjectId
from beanie import init_beanie, PydanticObjectId
from mongomock_motor import AsyncMongoMockClient
from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport

from models.company import Company
from models.red_flag import RedFlagResult, RedFlag
from models.comparison_result import ComparisonResult, RatioComparison, IndustryRanking
from models.report import Report
from models.user import User

from services import report_service


# ---------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------

class _FakeUser:
    email = "test@example.com"


async def _override_get_current_user():
    return _FakeUser()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client["test_db"],
        document_models=[User, Company, ComparisonResult, RedFlagResult, Report],
    )
    yield


@pytest_asyncio.fixture
async def http_client():
    from main import app
    from core.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = _override_get_current_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _make_company(name: str, ticker: str, workspace_id: PydanticObjectId) -> Company:
    company = Company(name=name, ticker=ticker, workspace_id=workspace_id)
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


class _FakeDocument:
    document_id = "D_TEST"


class _FakeGridFSBucket:
    """In-memory stand-in for AsyncIOMotorGridFSBucket -- mongomock_motor
    does not implement GridFS, so real Atlas/GridFS behavior is only
    verified in a real environment, not here."""

    def __init__(self):
        self._store: dict[str, bytes] = {}

    async def upload_from_stream(self, filename, data):
        file_id = ObjectId()
        self._store[str(file_id)] = data
        return file_id

    async def open_download_stream(self, file_id):
        data = self._store[str(file_id)]

        class _Stream:
            async def read(_self):
                return data

        return _Stream()

    async def delete(self, file_id):
        self._store.pop(str(file_id), None)


@pytest.fixture(autouse=True)
def mock_common_dependencies(monkeypatch):
    """Applied to every test: workspace resolution, document
    resolution, extraction, narrative, PDF rendering, and GridFS are
    all mocked so tests exercise only Report Agent's own orchestration
    logic (section gating, comparison dedupe, error handling)."""

    async def _fake_get_workspace(workspace_id, current_user):
        return SimpleNamespace(id=PydanticObjectId(workspace_id))

    monkeypatch.setattr(
        "services.workspace_service.get_workspace", _fake_get_workspace, raising=False
    )

    async def _fake_get_latest_document(company):
        return _FakeDocument()

    monkeypatch.setattr(
        report_service, "get_latest_document_for_company", _fake_get_latest_document
    )

    monkeypatch.setattr(
        report_service, "fetch_document_text", lambda document_id: "fake filing text"
    )

    monkeypatch.setattr(
        report_service,
        "run_extraction",
        lambda text, document_id: _fake_extraction("Nvidia Corporation", 100_000, 20_000, 500_000, 200_000),
    )

    async def _fake_narrative(**kwargs):
        return {
            "executive_summary": "Fake executive summary.",
            "outlook": "Fake outlook.",
        }

    monkeypatch.setattr(report_service, "run_report_narrative", _fake_narrative)

    monkeypatch.setattr(
        report_service, "build_report_pdf", lambda **kwargs: b"%PDF-FAKE-CONTENT"
    )

    fake_bucket = _FakeGridFSBucket()
    monkeypatch.setattr(report_service, "_gridfs_bucket", lambda: fake_bucket)

    return fake_bucket


# ---------------------------------------------------------------
# Prerequisite / error handling
# ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_report_without_linked_document_raises_422(monkeypatch):
    workspace_id = PydanticObjectId()
    nvidia = await _make_company("NVIDIA Corporation", "NVDA", workspace_id)

    async def _no_document(company):
        return None

    monkeypatch.setattr(report_service, "get_latest_document_for_company", _no_document)

    with pytest.raises(HTTPException) as exc_info:
        await report_service.generate_report(
            company_id=str(nvidia.id),
            workspace_id=str(workspace_id),
            current_user=_FakeUser(),
        )
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_generate_report_rejects_company_outside_workspace():
    real_workspace_id = PydanticObjectId()
    nvidia = await _make_company("NVIDIA Corporation", "NVDA", real_workspace_id)

    other_workspace_id = str(PydanticObjectId())
    with pytest.raises(HTTPException) as exc_info:
        await report_service.generate_report(
            company_id=str(nvidia.id),
            workspace_id=other_workspace_id,
            current_user=_FakeUser(),
        )
    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------
# Section gating -- report must complete even when optional/required
# sections have no data, with section_status reflecting reality
# ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_report_without_red_flags_or_comparisons_still_completes():
    workspace_id = PydanticObjectId()
    nvidia = await _make_company("NVIDIA Corporation", "NVDA", workspace_id)

    result = await report_service.generate_report(
        company_id=str(nvidia.id),
        workspace_id=str(workspace_id),
        current_user=_FakeUser(),
    )

    assert result.status == "completed"
    assert result.section_status.key_financials is True
    assert result.section_status.red_flags is False
    assert result.section_status.company_comparison is False
    assert result.comparisons_included == []


@pytest.mark.asyncio
async def test_generate_report_includes_red_flags_when_present():
    workspace_id = PydanticObjectId()
    nvidia = await _make_company("NVIDIA Corporation", "NVDA", workspace_id)

    red_flags = RedFlagResult(
        document_id="D_TEST",
        company="NVIDIA Corporation",
        fiscal_year=2025,
        metric_id="M001",
        flags=[
            RedFlag(
                category="rising_debt",
                title="Rising debt load",
                severity="MEDIUM",
                explanation="Liabilities grew faster than assets.",
                evidence="Balance sheet trend.",
            )
        ],
        overall_risk="MEDIUM",
        status="completed",
    )
    await red_flags.insert()

    result = await report_service.generate_report(
        company_id=str(nvidia.id),
        workspace_id=str(workspace_id),
        current_user=_FakeUser(),
    )

    assert result.section_status.red_flags is True


# ---------------------------------------------------------------
# Comparison handling -- the multi-comparison ("Nvidia vs 4 companies")
# scenario: auto-include all, dedupe re-runs of the same pair
# ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_report_auto_includes_all_comparisons_deduped():
    workspace_id = PydanticObjectId()
    nvidia = await _make_company("NVIDIA Corporation", "NVDA", workspace_id)
    walmart = await _make_company("Walmart Inc.", "WMT", workspace_id)
    pepsico = await _make_company("PepsiCo Inc.", "PEP", workspace_id)

    # Nvidia vs Walmart, run twice (simulates re-running the same pair)
    older = ComparisonResult(
        company_ids=[nvidia.id, walmart.id],
        tickers=["NVDA", "WMT"],
        ratio_comparisons=[
            RatioComparison(ratio_name="revenue", values={"NVDA": 100_000, "WMT": 600_000})
        ],
        industry_rankings=[
            IndustryRanking(ticker="NVDA", rank=2),
            IndustryRanking(ticker="WMT", rank=1),
        ],
        status="completed",
    )
    await older.insert()

    newer = ComparisonResult(
        company_ids=[nvidia.id, walmart.id],
        tickers=["NVDA", "WMT"],
        ratio_comparisons=[
            RatioComparison(ratio_name="revenue", values={"NVDA": 110_000, "WMT": 610_000})
        ],
        industry_rankings=[
            IndustryRanking(ticker="NVDA", rank=2),
            IndustryRanking(ticker="WMT", rank=1),
        ],
        status="completed",
    )
    await newer.insert()
    # Force `newer` to actually be newer regardless of insert timing.
    import datetime
    newer.completed_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=5)
    await newer.save()

    # Nvidia vs Pepsico, run once
    nvda_pep = ComparisonResult(
        company_ids=[nvidia.id, pepsico.id],
        tickers=["NVDA", "PEP"],
        status="completed",
    )
    await nvda_pep.insert()

    result = await report_service.generate_report(
        company_id=str(nvidia.id),
        workspace_id=str(workspace_id),
        current_user=_FakeUser(),
    )

    assert result.section_status.company_comparison is True
    assert len(result.comparisons_included) == 2  # deduped NVDA/WMT group + NVDA/PEP group

    included_ids = {c.comparison_id for c in result.comparisons_included}
    assert str(newer.id) in included_ids   # latest of the duplicate pair
    assert str(older.id) not in included_ids  # stale duplicate excluded
    assert str(nvda_pep.id) in included_ids


@pytest.mark.asyncio
async def test_generate_report_respects_explicit_comparison_ids_override():
    workspace_id = PydanticObjectId()
    nvidia = await _make_company("NVIDIA Corporation", "NVDA", workspace_id)
    walmart = await _make_company("Walmart Inc.", "WMT", workspace_id)
    pepsico = await _make_company("PepsiCo Inc.", "PEP", workspace_id)

    nvda_wmt = ComparisonResult(
        company_ids=[nvidia.id, walmart.id], tickers=["NVDA", "WMT"], status="completed",
    )
    await nvda_wmt.insert()
    nvda_pep = ComparisonResult(
        company_ids=[nvidia.id, pepsico.id], tickers=["NVDA", "PEP"], status="completed",
    )
    await nvda_pep.insert()

    result = await report_service.generate_report(
        company_id=str(nvidia.id),
        workspace_id=str(workspace_id),
        current_user=_FakeUser(),
        comparison_ids=[str(nvda_pep.id)],  # explicitly ask for only this one
    )

    assert len(result.comparisons_included) == 1
    assert result.comparisons_included[0].comparison_id == str(nvda_pep.id)


@pytest.mark.asyncio
async def test_generate_report_rejects_comparison_id_not_involving_company():
    workspace_id = PydanticObjectId()
    nvidia = await _make_company("NVIDIA Corporation", "NVDA", workspace_id)
    walmart = await _make_company("Walmart Inc.", "WMT", workspace_id)
    pepsico = await _make_company("PepsiCo Inc.", "PEP", workspace_id)

    # A comparison that does NOT involve Nvidia at all.
    unrelated = ComparisonResult(
        company_ids=[walmart.id, pepsico.id], tickers=["WMT", "PEP"], status="completed",
    )
    await unrelated.insert()

    with pytest.raises(HTTPException) as exc_info:
        await report_service.generate_report(
            company_id=str(nvidia.id),
            workspace_id=str(workspace_id),
            current_user=_FakeUser(),
            comparison_ids=[str(unrelated.id)],
        )
    assert exc_info.value.status_code == 400


# ---------------------------------------------------------------
# Retrieval / download / delete
# ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_list_download_and_delete_report(mock_common_dependencies):
    workspace_id = PydanticObjectId()
    nvidia = await _make_company("NVIDIA Corporation", "NVDA", workspace_id)

    generated = await report_service.generate_report(
        company_id=str(nvidia.id),
        workspace_id=str(workspace_id),
        current_user=_FakeUser(),
    )

    fetched = await report_service.get_report(generated.id)
    assert fetched.id == generated.id

    listed = await report_service.list_reports_for_company(str(nvidia.id))
    assert len(listed) == 1
    assert listed[0].id == generated.id

    pdf_bytes, filename = await report_service.download_report_pdf(generated.id)
    assert pdf_bytes == b"%PDF-FAKE-CONTENT"
    assert filename == "NVDA_report.pdf"

    await report_service.delete_report(generated.id)
    with pytest.raises(HTTPException) as exc_info:
        await report_service.get_report(generated.id)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_report_not_found():
    with pytest.raises(HTTPException) as exc_info:
        await report_service.get_report(str(ObjectId()))
    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------
# Route-level smoke test (requires routes/report.py wired into main.py)
# ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_report_endpoint(http_client):
    workspace_id = PydanticObjectId()
    nvidia = await _make_company("NVIDIA Corporation", "NVDA", workspace_id)

    response = await http_client.post(
        "/report/generate",
        json={"company_id": str(nvidia.id), "workspace_id": str(workspace_id)},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["ticker"] == "NVDA"