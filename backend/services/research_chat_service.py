import re
import json

import chromadb

from fastapi import HTTPException
from jose import JWTError, jwt

from config.settings import settings
from models.comparison_result import ComparisonResult
from models.company import Company
from models.document import DocumentModel
from models.user import User
from services.workspace_service import get_workspace, list_workspaces

from agents.research_agent.agent import llm
from agents.research_agent.research_agent import answer_research_question


SESSION_ALGORITHM = settings.ALGORITHM

# Number of previous questions remembered for conversational follow-ups.
MAX_CONVERSATION_HISTORY = 5


# =========================================================
# CHROMA DOCUMENT LOOKUP
# =========================================================

def _normalize_filename_value(value: str) -> str:
    """
    Normalize company names and filenames so punctuation differences
    such as:

        Tesla, Inc.
        Tesla
        tesla_2025_annual_report

    can be matched safely.
    """

    value = (value or "").lower().strip()

    value = value.replace("_", " ")
    value = value.replace("-", " ")

    value = re.sub(r"[^a-z0-9]+", " ", value)

    return " ".join(value.split())


def _company_core_name(company_name: str) -> str:
    """
    Remove common legal company suffixes.

    Example:
        Tesla, Inc. -> Tesla
        Walmart Inc. -> Walmart
        Target Corporation -> Target
    """

    value = _normalize_filename_value(company_name)

    suffixes = {
        "inc",
        "incorporated",
        "corp",
        "corporation",
        "co",
        "company",
        "ltd",
        "limited",
        "llc",
        "plc",
    }

    tokens = [
        token
        for token in value.split()
        if token not in suffixes
    ]

    return " ".join(tokens)


def _chroma_document_exists(document_id: str) -> bool:
    """
    Check whether a document ID actually exists in Chroma.
    """

    if not document_id:
        return False

    try:
        client = chromadb.PersistentClient(
            path="vectorstore/chroma_data"
        )

        collection = client.get_collection(
            "financial_documents"
        )

        result = collection.get(
            where={
                "document_id": str(document_id)
            },
            limit=1,
        )

        return bool(result.get("ids"))

    except Exception:
        return False


def _find_chroma_document_id(
    company_name: str,
    ticker: str,
) -> str | None:
    """
    Find the actual indexed Chroma document ID for a company.

    Matching order:

    1. Full normalized company name
    2. Core company name without legal suffix
    3. Ticker token
    """

    try:
        client = chromadb.PersistentClient(
            path="vectorstore/chroma_data"
        )

        collection = client.get_collection(
            "financial_documents"
        )

        result = collection.get(
            include=["metadatas"]
        )

        normalized_company = _normalize_filename_value(
            company_name
        )

        core_company = _company_core_name(
            company_name
        )

        normalized_ticker = _normalize_filename_value(
            ticker
        )

        metadatas = result.get(
            "metadatas",
            []
        )

        # -----------------------------------------------------
        # PASS 1
        # Full company name
        # -----------------------------------------------------

        if normalized_company:

            for metadata in metadatas:

                if not metadata:
                    continue

                filename = str(
                    metadata.get(
                        "filename",
                        ""
                    )
                )

                document_id = metadata.get(
                    "document_id"
                )

                if not document_id:
                    continue

                normalized_filename = (
                    _normalize_filename_value(
                        filename
                    )
                )

                if (
                    normalized_company
                    and normalized_company
                    in normalized_filename
                ):
                    return str(document_id)

        # -----------------------------------------------------
        # PASS 2
        # Core company name
        # -----------------------------------------------------

        if core_company:

            for metadata in metadatas:

                if not metadata:
                    continue

                filename = str(
                    metadata.get(
                        "filename",
                        ""
                    )
                )

                document_id = metadata.get(
                    "document_id"
                )

                if not document_id:
                    continue

                normalized_filename = (
                    _normalize_filename_value(
                        filename
                    )
                )

                if (
                    core_company
                    and core_company
                    in normalized_filename
                ):
                    return str(document_id)

        # -----------------------------------------------------
        # PASS 3
        # Ticker token
        # -----------------------------------------------------

        if normalized_ticker:

            for metadata in metadatas:

                if not metadata:
                    continue

                filename = str(
                    metadata.get(
                        "filename",
                        ""
                    )
                )

                document_id = metadata.get(
                    "document_id"
                )

                if not document_id:
                    continue

                normalized_filename = (
                    _normalize_filename_value(
                        filename
                    )
                )

                filename_tokens = set(
                    normalized_filename.split()
                )

                if normalized_ticker in filename_tokens:
                    return str(document_id)

        return None

    except Exception:
        return None


# =========================================================
# SESSION FUNCTIONS
# =========================================================

def _create_session(data: dict) -> str:
    """
    Create a signed stateless research-chat session.
    """

    return jwt.encode(
        data,
        settings.SECRET_KEY,
        algorithm=SESSION_ALGORITHM,
    )


def _read_session(session_id: str) -> dict:
    """
    Decode and verify a research-chat session.
    """

    try:

        return jwt.decode(
            session_id,
            settings.SECRET_KEY,
            algorithms=[SESSION_ALGORITHM],
        )

    except JWTError:

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired research session.",
        )


def _session_data(session_id: str) -> dict:
    return _read_session(session_id)


def _new_session(**updates) -> str:
    """
    Create a new stateless session.

    conversation_history stores only recent user questions.
    Answers are not stored in the JWT because answers can become
    large and would unnecessarily increase token size.
    """

    data = {
        "workspace_id": None,
        "mode": None,
        "company_ids": [],
        "company_names": [],
        "document_ids": [],
        "conversation_history": [],
    }

    data.update(updates)

    return _create_session(data)


# =========================================================
# CONVERSATION HISTORY
# =========================================================

def _get_conversation_history(
    session: dict,
) -> list[str]:
    """
    Safely retrieve recent conversation questions.
    """

    history = session.get(
        "conversation_history",
        [],
    )

    if not isinstance(history, list):
        return []

    cleaned_history = []

    for item in history:

        if isinstance(item, str):

            value = item.strip()

            if value:
                cleaned_history.append(value)

        elif isinstance(item, dict):

            value = str(
                item.get(
                    "question",
                    ""
                )
            ).strip()

            if value:
                cleaned_history.append(value)

    return cleaned_history[-MAX_CONVERSATION_HISTORY:]


def _append_conversation_question(
    history: list[str],
    question: str,
) -> list[str]:
    """
    Add the latest user question while keeping only a small
    recent history.
    """

    updated_history = list(history)

    cleaned_question = (
        question or ""
    ).strip()

    if cleaned_question:
        updated_history.append(
            cleaned_question
        )

    return updated_history[
        -MAX_CONVERSATION_HISTORY:
    ]


def _build_single_company_question(
    question: str,
    company_name: str,
    conversation_history: list[str],
) -> str:
    """
    Build the Research Agent prompt for a one-company
    conversational request.
    """

    if not conversation_history:
        return question.strip()

    previous_questions = "\n".join(
        f"{index}. {item}"
        for index, item in enumerate(
            conversation_history,
            start=1,
        )
    )

    return f"""
You are the Financial Research Agent answering a conversational
financial research question for ONE selected company.

SELECTED COMPANY:
{company_name}

PREVIOUS CONVERSATION QUESTIONS:
{previous_questions}

CURRENT USER QUESTION:
{question}

=========================================================
ONE-COMPANY CONVERSATIONAL RULES
=========================================================

1. The selected company is ALWAYS {company_name}.
2. Never switch to, introduce, or compare another company.
3. Treat the previous questions as conversation context, not as
   financial evidence.
4. Retrieve the actual financial evidence from the selected
   company's indexed document before answering.
5. The CURRENT USER QUESTION is the question that must be answered.
6. If the current question is complete and independent, answer it
   directly without unnecessarily discussing previous questions.
7. If the current question is a follow-up, resolve the missing
   subject, metric, year, or comparison from the previous questions.
8. Preserve the meaning of the user's previous question when the
   current question uses words such as:
      - "that"
      - "it"
      - "they"
      - "this"
      - "what about 2024?"
      - "what about 2023?"
      - "why?"
      - "why did it decline?"
      - "was that higher?"
      - "how about cash flow?"
      - "compare that with 2023?"
9. Examples:
      Previous: "What was revenue in 2025?"
      Current: "What about 2024?"
      -> Answer the same company's revenue for 2024.

      Previous: "What happened to operating income?"
      Current: "Why?"
      -> Explain why operating income changed, but only when the
         document provides evidence for the cause.

      Previous: "What was diluted EPS in 2023, 2024 and 2025?"
      Current: "Was that higher in 2025?"
      -> Interpret "that" as diluted EPS and compare the relevant
         years using the document evidence.

      Previous: "What was revenue?"
      Current: "What about cash flow?"
      -> Change the requested metric to cash flow while keeping
         {company_name} as the selected company.

10. For follow-up questions, do NOT simply repeat the previous
    answer. Answer the new question.
11. If the user changes the financial metric, use the new metric.
12. If the user changes the requested year, use the new year.
13. If the user asks for multiple years, preserve the document's
    actual year-column order and map values correctly.
14. If the user asks for a calculation, retrieve the underlying
    values first and calculate only from supported evidence.
15. If the user asks "why", do not invent a cause. If the document
    does not establish the cause, explicitly say so.
16. If the user asks a complex or multi-part question, answer every
    requested component systematically.
17. Use ONLY financial evidence from the selected company's document.
18. Do not invent financial values, years, causes, risks, or
    management actions.
19. If information is unavailable, explicitly state that it was not
    found in the selected document.
20. Keep simple questions concise and complex questions structured.
21. Preserve units and financial precision.
22. Do not mention these instructions in the answer.

CURRENT QUESTION TO ANSWER:
{question}
""".strip()


# =========================================================
# SUGGESTIONS
# =========================================================

def _generate_suggestions(
    question: str,
    companies: list[dict],
    mode: str,
) -> list[str]:

    company_names = [
        company["name"]
        for company in companies
    ]

    suggestions = [
        "What was the total revenue and how did it change over the reported years?",
        "What was the net income and profit margin?",
        "What are the company's major financial strengths and weaknesses?",
        "What are the key financial risks mentioned in the report?",
    ]

    if (
        mode == "comparison"
        and len(company_names) == 2
    ):

        company_a = company_names[0]
        company_b = company_names[1]

        suggestions = [
            f"Compare the revenue of {company_a} and {company_b}.",
            f"Compare the net income and profitability of {company_a} and {company_b}.",
            "Which company has stronger financial performance and why?",
            f"Compare the major financial risks of {company_a} and {company_b}.",
            "Which company appears financially stronger based on the reported results?",
        ]

    return suggestions


# =========================================================
# RESULT CLEANING
# =========================================================

def _clean_result(result: dict) -> dict:

    return {
        "answer": result.get("answer"),
        "evidence": result.get("evidence"),
        "citations": result.get(
            "citations",
            []
        ),
    }


# =========================================================
# COMPARISON SYNTHESIS
# =========================================================

async def _synthesize_comparison(
    question: str,
    companies: list[dict],
    results: list[dict],
) -> dict:

    company_sections = []

    for company, result in zip(
        companies,
        results,
    ):

        company_sections.append(
            f"""
COMPANY: {company['name']}

ANSWER:
{result.get('answer', '')}

EVIDENCE:
{result.get('evidence', '')}

CITATIONS:
{result.get('citations', [])}
"""
        )

    prompt = f"""
You are the comparison layer of a financial research system.

Answer the user's question using ONLY the research results supplied below.

USER QUESTION:
{question}

SELECTED COMPANIES:
{', '.join(company['name'] for company in companies)}

RESEARCH RESULTS:
{''.join(company_sections)}

Instructions:
1. Directly answer the user's question.
2. Compare the companies clearly when comparison is requested.
3. Preserve numerical values exactly when they are supported by the research results.
4. Do not invent financial values.
5. If information is unavailable, explicitly say that it was not found.
6. Explain important differences when relevant.
7. Handle complex, multi-part questions systematically.
8. Keep the answer clear and structured.
"""

    try:

        answer = llm.call(
            prompt
        )

        return {
            "answer": str(answer),
            "evidence": (
                "Comparison synthesized from the selected "
                "companies' financial research results."
            ),
        }

    except Exception:

        return {
            "answer": (
                "I could not create the combined comparison summary. "
                "The individual company research results are provided below."
            ),
            "evidence": None,
        }


# =========================================================
# START RESEARCH CHAT
# =========================================================

async def start_research_chat(
    current_user: User,
) -> dict:

    session_id = _new_session()

    workspaces = await list_workspaces(
        current_user
    )

    return {
        "message": "Research chat started.",
        "session_id": session_id,
        "workspaces": [
            {
                "id": str(workspace.id),
                "name": workspace.name,
                "description": workspace.description,
                "objective": workspace.objective,
            }
            for workspace in workspaces
        ],
        "next_step": "Select a workspace.",
    }


# =========================================================
# SELECT WORKSPACE
# =========================================================

async def select_workspace(
    session_id: str,
    workspace_id: str,
    current_user: User,
) -> dict:

    workspace = await get_workspace(
        workspace_id=workspace_id,
        current_user=current_user,
    )

    _session_data(session_id)

    new_session = _new_session(
        workspace_id=str(workspace.id),
        mode=None,
        company_ids=[],
        company_names=[],
        document_ids=[],
        conversation_history=[],
    )

    companies = await Company.find(
        Company.workspace_id == workspace.id
    ).to_list()

    company_list = [
        {
            "id": str(company.id),
            "name": company.name,
            "ticker": company.ticker,
            "industry": company.industry,
            "sector": company.sector,
        }
        for company in companies
    ]

    return {
        "message": "Workspace selected.",
        "session_id": new_session,
        "workspace": {
            "id": str(workspace.id),
            "name": workspace.name,
            "description": workspace.description,
            "objective": workspace.objective,
        },
        "companies": company_list,
        "next_step": (
            "Do you want to research one company "
            "or compare two companies?"
        ),
    }


# =========================================================
# SELECT MODE
# =========================================================

async def select_mode(
    session_id: str,
    compare: bool,
) -> dict:

    session = _session_data(
        session_id
    )

    if not session.get("workspace_id"):

        raise HTTPException(
            status_code=400,
            detail=(
                "Select a workspace before "
                "selecting research mode."
            ),
        )

    mode = (
        "comparison"
        if compare
        else "single"
    )

    new_session = _new_session(
        workspace_id=session["workspace_id"],
        mode=mode,
        company_ids=[],
        company_names=[],
        document_ids=[],
        conversation_history=[],
    )

    return {
        "message": "Research mode selected.",
        "session_id": new_session,
        "mode": mode,
        "required_companies": (
            2 if compare else 1
        ),
        "next_step": (
            "Please select exactly 2 companies."
            if compare
            else "Please select exactly 1 company."
        ),
    }


# =========================================================
# SELECT COMPANIES
# =========================================================

async def select_companies(
    session_id: str,
    company_ids: list[str],
) -> dict:

    session = _session_data(
        session_id
    )

    workspace_id = session.get(
        "workspace_id"
    )

    mode = session.get(
        "mode"
    )

    if not workspace_id:

        raise HTTPException(
            status_code=400,
            detail="Select a workspace first.",
        )

    if not mode:

        raise HTTPException(
            status_code=400,
            detail="Select research mode first.",
        )

    required_count = (
        2
        if mode == "comparison"
        else 1
    )

    if len(company_ids) != required_count:

        raise HTTPException(
            status_code=400,
            detail=(
                f"{mode.capitalize()} mode requires exactly "
                f"{required_count} company"
                f"{'ies' if required_count == 2 else ''}."
            ),
        )

    if len(set(company_ids)) != len(company_ids):

        raise HTTPException(
            status_code=400,
            detail="Duplicate companies are not allowed.",
        )

    selected_companies = []

    # Keep workspace_id local and explicit before company validation.
    workspace_id = session.get("workspace_id")
    if not workspace_id:
        raise HTTPException(status_code=400, detail="Workspace has not been selected.")

    # ---------------------------------------------------------
    # VERIFY COMPANIES
    # ---------------------------------------------------------

    for company_id in company_ids:

        company = await Company.get(
            company_id
        )

        if not company:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Company not found: {company_id}"
                ),
            )

        if str(company.workspace_id) != str(
            workspace_id
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    f"Company {company.ticker} does not belong "
                    "to the selected workspace."
                ),
            )

        selected_companies.append(
            company
        )

    # ---------------------------------------------------------
    # FIND DOCUMENT IDS
    # ---------------------------------------------------------

    document_ids = []

    for company in selected_companies:

        document = await DocumentModel.find(
            DocumentModel.company_id
            == str(company.id),
            DocumentModel.status
            == "indexed",
        ).sort(
            "-created_at"
        ).first_or_none()

        if not document:

            document = await DocumentModel.find(
                DocumentModel.company_id
                == company.id,
                DocumentModel.status
                == "indexed",
            ).sort(
                "-created_at"
            ).first_or_none()

        document_id = None

        # -----------------------------------------------------
        # TRY MONGODB DOCUMENT
        # -----------------------------------------------------

        if document:

            candidate_document_id = (
                document.document_id
            )

            if _chroma_document_exists(
                candidate_document_id
            ):

                document_id = (
                    candidate_document_id
                )

        # -----------------------------------------------------
        # FALL BACK TO CHROMA
        # -----------------------------------------------------

        if not document_id:

            document_id = _find_chroma_document_id(
                company_name=company.name,
                ticker=company.ticker,
            )

        # -----------------------------------------------------
        # NO DOCUMENT
        # -----------------------------------------------------

        if not document_id:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"No indexed financial document was found for "
                    f"{company.name} ({company.ticker})."
                ),
            )

        document_ids.append(
            str(document_id)
        )

    company_names = [
        company.name
        for company in selected_companies
    ]

    company_details = [
        {
            "id": str(company.id),
            "name": company.name,
            "ticker": company.ticker,
        }
        for company in selected_companies
    ]

    # ---------------------------------------------------------
    # CREATE UPDATED SESSION
    # ---------------------------------------------------------

    new_session = _new_session(
        workspace_id=workspace_id,
        mode=mode,
        company_ids=[
            str(company.id)
            for company in selected_companies
        ],
        company_names=company_names,
        document_ids=document_ids,
        conversation_history=[],
    )

    return {
        "message": "Companies selected successfully.",
        "session_id": new_session,
        "mode": mode,
        "companies": company_details,
        "documents_loaded": len(
            document_ids
        ),
        "document_ids": document_ids,
        "next_step": (
            "The selected financial document has been loaded internally. "
            "I am now ready to answer your financial research questions."
        ),
        "suggestions": _generate_suggestions(
            question="",
            companies=company_details,
            mode=mode,
        ),
    }


# =========================================================
# TWO-COMPANY CONVERSATION / COMPARISON HELPERS
# =========================================================

def _build_comparison_context_question(
    question: str,
    companies: list[dict],
    conversation_history: list[str],
) -> str:

    company_names = [
        company.get("name", "")
        for company in companies
    ]

    if not conversation_history:
        previous_questions = "No previous questions."
    else:
        previous_questions = "\n".join(
            f"{index}. {item}"
            for index, item in enumerate(
                conversation_history,
                start=1,
            )
        )

    return f"""
You are the Financial Research Agent answering a question about
EXACTLY TWO selected companies.

SELECTED COMPANIES:
1. {company_names[0]}
2. {company_names[1]}

PREVIOUS CONVERSATION QUESTIONS:
{previous_questions}

CURRENT USER QUESTION:
{question}

COMPARISON CONVERSATION RULES:

1. Keep the same two selected companies throughout the conversation.
2. Never switch companies and never introduce a third company.
3. Resolve follow-ups such as:
   - "What about 2024?"
   - "What about revenue?"
   - "Which one was higher?"
   - "Why?"
   - "What about EPS?"
   - "Compare that with 2023."
   using the previous questions as context.
4. If the current question is complete, answer that question directly.
5. If the user changes the metric, use the new metric.
6. If the user changes the year, use the new year.
7. If the user asks for a comparison, compare the same metric and
   same reporting period for both companies whenever the data exists.
8. Do not confuse total-company amounts with per-share metrics.
9. Do not invent values, causes, risks, trends, or conclusions.
10. Use the supplied Comparison Agent result as the comparison
    evidence. If a requested item is not in that result, say so.
11. If the user asks "why", only state causes supported by the supplied
    comparison evidence.
12. Answer the CURRENT USER QUESTION, not every previous question.
13. Simple questions should receive concise answers; complex questions
    should be structured.
14. Preserve reported units and financial precision.
""".strip()


async def _load_stored_comparison(
    company_ids: list[str],
    tickers: list[str],
):

    try:

        comparison = await ComparisonResult.find_one(
            {
                "company_ids": {
                    "$all": [
                        str(company_ids[0]),
                        str(company_ids[1]),
                    ]
                },
                "status": "completed",
            }
        )

        if comparison:
            return comparison

    except Exception:
        pass

    try:

        comparison = await ComparisonResult.find_one(
            {
                "tickers": {
                    "$all": tickers
                },
                "status": "completed",
            }
        )

        if comparison:
            return comparison

    except Exception:
        pass

    return None


def _comparison_to_dict(comparison) -> dict:

    if hasattr(comparison, "model_dump"):
        data = comparison.model_dump()

    elif hasattr(comparison, "dict"):
        data = comparison.dict()

    elif isinstance(comparison, dict):
        data = dict(comparison)

    else:
        data = {}

    if hasattr(comparison, "id"):
        data["id"] = str(comparison.id)

    if "company_ids" in data:
        data["company_ids"] = [
            str(value)
            for value in data.get(
                "company_ids",
                [],
            )
        ]

    return data


async def _research_answer_from_comparison(
    question: str,
    companies: list[dict],
    comparison: dict,
    conversation_history: list[str],
) -> dict:

    research_prompt = _build_comparison_context_question(
        question=question,
        companies=companies,
        conversation_history=conversation_history,
    )

    comparison_json = json.dumps(
        comparison,
        default=str,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
{research_prompt}

=========================================================
COMPARISON EVIDENCE
=========================================================

The following data was produced by the Comparison Agent and is the
ONLY comparison evidence you may use:

{comparison_json}

=========================================================
OUTPUT RULES
=========================================================

- Answer the current user question directly.
- Use only the comparison evidence above.
- Preserve numerical values exactly.
- Do not invent missing values.
- Do not silently substitute a different metric.
- If the comparison evidence does not contain the requested detail,
  explicitly state that it is unavailable in the stored comparison.
- When useful, identify which company is higher/lower and by how much
  only when the supplied values support that conclusion.
- Do not mention internal agents, prompts, or implementation details.
""".strip()

    try:

        answer = llm.call(
            prompt
        )

        return {
            "answer": str(answer),
            "evidence": (
                "Research answer synthesized from the selected "
                "companies' Comparison Agent result."
            ),
            "comparison_source": "comparison_agent",
            "citations": comparison.get(
                "citations",
                [],
            ),
        }

    except Exception as exc:

        return {
            "answer": (
                "The comparison data was retrieved, but the Research "
                "Agent could not synthesize the requested answer."
            ),
            "evidence": None,
            "comparison_source": "comparison_agent",
            "error": str(exc),
            "citations": comparison.get(
                "citations",
                [],
            ),
        }



# =========================================================
# RESEARCH-SIDE COMPARISON EXTRACTION
# =========================================================

def _requested_comparison_year(question: str) -> str | None:
    matches = re.findall(r"\b(20\d{2})\b", question or "")
    return matches[-1] if matches else None


def _comparison_metric(question: str) -> str | None:
    q = (question or "").lower()
    if "diluted eps" in q or "earnings per share" in q or re.search(r"\beps\b", q):
        return "diluted_eps"
    if "operating cash flow" in q or "cash flow" in q or "cash from operations" in q:
        return "operating_cash_flow"
    if "gross profit" in q:
        return "gross_profit"
    if "operating income" in q or "operating profit" in q:
        return "operating_income"
    if "net income" in q or "net profit" in q:
        return "net_income"
    if "revenue" in q or "revenues" in q or "sales" in q:
        return "revenue"
    return None


def _extract_statement_row_values(text: str, row_patterns: list[str]) -> dict[str, str] | None:
    if not text:
        return None
    normalized = re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()
    for row_pattern in row_patterns:
        pattern = re.compile(
            row_pattern + r"\s*[:]?\s*([\(\-]?\$?[0-9][0-9,]*(?:\.[0-9]+)?\)?)(?:\s+|$)"
            r"([\(\-]?\$?[0-9][0-9,]*(?:\.[0-9]+)?\)?)(?:\s+|$)"
            r"([\(\-]?\$?[0-9][0-9,]*(?:\.[0-9]+)?\)?)",
            re.IGNORECASE,
        )
        m = pattern.search(normalized)
        if m:
            return {"2025": m.group(1), "2024": m.group(2), "2023": m.group(3)}
    return None


def _extract_authoritative_comparison_fact(result: dict, metric: str, year: str | None) -> dict | None:
    chunks = result.get("retrieved_chunks") or []
    if not chunks:
        return None

    if metric == "revenue":
        patterns = [r"\bTotal revenues\b"]
    elif metric == "gross_profit":
        patterns = [r"\bGross profit\b"]
    elif metric == "operating_income":
        patterns = [r"\bIncome from operations\b", r"\bOperating income\b"]
    elif metric == "net_income":
        patterns = [r"\bConsolidated net income\b", r"\bNet income\b"]
    elif metric == "operating_cash_flow":
        patterns = [r"\bNet cash provided by operating activities\b"]
    else:
        return None

    # Prefer consolidated statement chunks and exact requested row.
    candidates = []
    for chunk in chunks:
        text = chunk.get("text", "") if isinstance(chunk, dict) else str(chunk)
        lower = text.lower()
        if metric == "revenue" and "total revenues" not in lower:
            continue
        if metric in {"revenue", "gross_profit", "operating_income", "net_income"} and "consolidated" not in lower:
            continue
        values = _extract_statement_row_values(text, patterns)
        if values:
            candidates.append((chunk, values))

    if not candidates:
        return None

    chunk, values = candidates[0]
    selected_year = year or "2025"
    value = values.get(selected_year)
    if value is None:
        return None

    return {
        "metric": metric,
        "year": selected_year,
        "value": value,
        "page": chunk.get("page") if isinstance(chunk, dict) else None,
        "document_id": chunk.get("document_id") if isinstance(chunk, dict) else None,
        "filename": chunk.get("filename") if isinstance(chunk, dict) else None,
        "source": chunk.get("source") if isinstance(chunk, dict) else None,
        "text": chunk.get("text", "") if isinstance(chunk, dict) else str(chunk),
    }


def _numeric_value(value: str) -> float | None:
    if value is None:
        return None
    cleaned = str(value).replace("$", "").replace(",", "").strip()
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()")
    try:
        number = float(cleaned)
        return -number if negative else number
    except ValueError:
        return None


def _format_financial_number(number: float) -> str:
    if float(number).is_integer():
        return f"{int(number):,}"
    return f"{number:,.2f}".rstrip("0").rstrip(".")


def _build_deterministic_simple_comparison(question: str, companies: list[dict], facts: list[dict]) -> dict | None:
    metric = _comparison_metric(question)
    year = _requested_comparison_year(question)
    if not metric or not year or len(facts) != 2:
        return None
    if any(f.get("metric") != metric or f.get("year") != year for f in facts):
        return None

    a = _numeric_value(facts[0]["value"])
    b = _numeric_value(facts[1]["value"])
    if a is None or b is None:
        return None

    labels = {
        "revenue": "revenue",
        "gross_profit": "gross profit",
        "operating_income": "operating income",
        "net_income": "net income",
        "operating_cash_flow": "operating cash flow",
    }
    metric_label = labels[metric]
    difference = abs(a - b)
    if a > b:
        higher = companies[0]["name"]
    elif b > a:
        higher = companies[1]["name"]
    else:
        higher = None

    if higher:
        conclusion = f"{higher} was higher by ${_format_financial_number(difference)} million."
    else:
        conclusion = "Both companies reported the same value."

    answer = (
        f"For {year}, {companies[0]['name']} reported {metric_label} of "
        f"${_format_financial_number(a)} million, while {companies[1]['name']} "
        f"reported ${_format_financial_number(b)} million. {conclusion}"
    )

    citations = []
    for fact in facts:
        citation = {
            "document_id": fact.get("document_id"),
            "filename": fact.get("filename"),
            "page": fact.get("page"),
            "source": fact.get("source"),
        }
        if citation["document_id"] or citation["page"]:
            citations.append(citation)

    return {
        "answer": answer,
        "evidence": facts,
        "comparison_source": "research_agent_structured_extraction",
        "citations": citations,
    }


def _build_individual_comparison_question(
    question: str,
    company_name: str,
    other_company_name: str,
    conversation_history: list[str],
) -> str:
    previous = "\n".join(f"{i}. {q}" for i, q in enumerate(conversation_history, 1)) or "No previous questions."
    return f"""
You are the Financial Research Agent analyzing ONLY {company_name}.
The user is comparing {company_name} with {other_company_name}.

USER QUESTION:
{question}

PREVIOUS QUESTIONS:
{previous}

Extract the exact financial fact needed for the {company_name} side of the comparison.
For revenue questions, ALWAYS prefer the consolidated statement's exact 'Total revenues'
row. Do NOT use automotive revenue, segment revenue, deferred revenue, lease revenue,
product revenue, or another component unless the user explicitly requested that component.
For other metrics, use the exact consolidated statement row matching the requested metric.
Return the relevant evidence and citations. Never invent a value.
""".strip()

# =========================================================
# ASK RESEARCH QUESTION
# =========================================================

async def ask_research_question(
    session_id: str,
    question: str,
    current_user: User,
) -> dict:

    # ---------------------------------------------------------
    # VALIDATE QUESTION
    # ---------------------------------------------------------

    if not question or not question.strip():

        raise HTTPException(
            status_code=400,
            detail="Research question cannot be empty.",
        )

    question = question.strip()

    # ---------------------------------------------------------
    # READ SESSION
    # ---------------------------------------------------------

    session = _session_data(
        session_id
    )

    # =========================================================
    # IMPORTANT FIX
    # =========================================================
    # The comparison section needs workspace_id.
    # Previously workspace_id was used without being defined,
    # causing:
    #
    # NameError: name 'workspace_id' is not defined
    #
    # We now load it directly from the authenticated session.
    # =========================================================

    workspace_id = session.get(
        "workspace_id"
    )

    mode = session.get(
        "mode"
    )

    company_ids = session.get(
        "company_ids",
        [],
    )

    company_names = session.get(
        "company_names",
        [],
    )

    document_ids = session.get(
        "document_ids",
        [],
    )

    # ---------------------------------------------------------
    # VALIDATE WORKSPACE
    # ---------------------------------------------------------

    if not workspace_id:

        raise HTTPException(
            status_code=400,
            detail=(
                "Workspace has not been selected."
            ),
        )

    # ---------------------------------------------------------
    # VALIDATE MODE
    # ---------------------------------------------------------

    if not mode:

        raise HTTPException(
            status_code=400,
            detail=(
                "Research mode has not been selected."
            ),
        )

    # ---------------------------------------------------------
    # VALIDATE DOCUMENTS
    # ---------------------------------------------------------

    if not document_ids:

        raise HTTPException(
            status_code=400,
            detail=(
                "Select companies before asking "
                "a research question."
            ),
        )

    # =========================================================
    # SINGLE COMPANY
    # =========================================================

    if mode == "single":

        if not company_ids:

            raise HTTPException(
                status_code=400,
                detail=(
                    "A company must be selected "
                    "before asking a question."
                ),
            )

        company_name = (
            company_names[0]
            if company_names
            else company_ids[0]
        )

        # -----------------------------------------------------
        # LOAD RECENT CONVERSATION CONTEXT
        # -----------------------------------------------------

        conversation_history = (
            _get_conversation_history(
                session
            )
        )

        # -----------------------------------------------------
        # BUILD CONTEXT-AWARE QUESTION
        # -----------------------------------------------------

        research_question = (
            _build_single_company_question(
                question=question,
                company_name=company_name,
                conversation_history=conversation_history,
            )
        )

        # -----------------------------------------------------
        # CALL RESEARCH AGENT
        # -----------------------------------------------------

        result = answer_research_question(
            question=research_question,
            document_id=document_ids[0],
            top_k=5,
        )

        company_details = {
            "id": company_ids[0],
            "name": company_name,
        }

        # -----------------------------------------------------
        # UPDATE CONVERSATION HISTORY
        # -----------------------------------------------------

        updated_history = (
            _append_conversation_question(
                history=conversation_history,
                question=question,
            )
        )

        # -----------------------------------------------------
        # CREATE NEW SESSION
        # -----------------------------------------------------

        new_session = _new_session(
            workspace_id=workspace_id,
            mode="single",
            company_ids=company_ids,
            company_names=company_names,
            document_ids=document_ids,
            conversation_history=updated_history,
        )

        return {
            "session_id": new_session,
            "previous_session_id": session_id,
            "mode": mode,
            "question": question,
            "company": company_details,
            "result": result,
            "conversation": {
                "context_used": bool(
                    conversation_history
                ),
                "history_length": len(
                    updated_history
                ),
                "next_question_uses_session_id": True,
            },
            "suggestions": _generate_suggestions(
                question=question,
                companies=[company_details],
                mode=mode,
            ),
        }

    # =========================================================
    # TWO-COMPANY RESEARCH / COMPARISON FLOW
    # =========================================================

    if mode != "comparison":

        raise HTTPException(
            status_code=400,
            detail=f"Unsupported research mode: {mode}",
        )

    if len(company_ids) != 2 or len(document_ids) != 2:

        raise HTTPException(
            status_code=400,
            detail=(
                "Comparison mode requires exactly "
                "two companies."
            ),
        )

    if len(company_names) != 2:

        raise HTTPException(
            status_code=400,
            detail=(
                "Comparison mode requires exactly "
                "two company names."
            ),
        )

    # ---------------------------------------------------------
    # RESOLVE THE TWO SELECTED COMPANIES
    # ---------------------------------------------------------

    selected_companies = []

    for company_id in company_ids:

        company = await Company.get(
            company_id
        )

        if not company:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Company not found: {company_id}"
                ),
            )

        # -----------------------------------------------------
        # THIS NOW WORKS BECAUSE workspace_id IS DEFINED ABOVE
        # -----------------------------------------------------

        if str(company.workspace_id) != str(
            workspace_id
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    f"Company {company.ticker} does not belong "
                    "to the selected workspace."
                ),
            )

        selected_companies.append(
            company
        )

    # ---------------------------------------------------------
    # COMPANY DETAILS
    # ---------------------------------------------------------

    company_details = [
        {
            "id": str(company.id),
            "name": company.name,
            "ticker": company.ticker,
        }
        for company in selected_companies
    ]

    tickers = [
        str(company.ticker)
        for company in selected_companies
        if company.ticker
    ]

    # ---------------------------------------------------------
    # LOAD COMPARISON CONVERSATION CONTEXT
    # ---------------------------------------------------------

    conversation_history = (
        _get_conversation_history(
            session
        )
    )

    # =========================================================
    # 1. FIRST PREFERENCE: STORED COMPARISON RESULT
    # =========================================================

    existing_comparison = await _load_stored_comparison(
        company_ids=company_ids,
        tickers=tickers,
    )

    comparison_source = None

    if existing_comparison is not None:

        comparison = _comparison_to_dict(
            existing_comparison
        )

        comparison_source = (
            "stored_comparison_result"
        )

    # =========================================================
    # 2. IF NO STORED RESULT: RESEARCH-SIDE FALLBACK
    # =========================================================

    individual_results = []

    if existing_comparison is None:
        for index, company in enumerate(company_details):
            other = company_details[1 - index]
            individual_question = _build_individual_comparison_question(
                question=question,
                company_name=company["name"],
                other_company_name=other["name"],
                conversation_history=conversation_history,
            )
            result = answer_research_question(
                question=individual_question,
                document_id=document_ids[index],
                top_k=8,
            )
            individual_results.append({
                "company": company["name"],
                "ticker": company.get("ticker"),
                "document_id": document_ids[index],
                "result": result,
            })

        facts = []
        metric = _comparison_metric(question)
        year = _requested_comparison_year(question)
        if metric and year:
            for item in individual_results:
                fact = _extract_authoritative_comparison_fact(
                    item["result"], metric, year
                )
                if fact:
                    facts.append(fact)

        deterministic = _build_deterministic_simple_comparison(
            question=question,
            companies=company_details,
            facts=facts,
        )

        if deterministic is not None:
            comparison = {
                "status": "completed",
                "source": "research_agent",
                "answer": deterministic["answer"],
                "summary": deterministic["answer"],
                "company_ids": [str(c["id"]) for c in company_details],
                "tickers": [c.get("ticker") for c in company_details],
                "research_evidence": individual_results,
                "structured_facts": facts,
                "citations": deterministic["citations"],
            }
            research_result = deterministic
            comparison_source = "research_agent_structured_extraction"
        else:
            comparison = {
                "status": "completed",
                "source": "research_agent",
                "company_ids": [str(c["id"]) for c in company_details],
                "tickers": [c.get("ticker") for c in company_details],
                "research_evidence": individual_results,
                "structured_facts": facts,
            }
            research_result = _synthesize_comparison(
                question=question,
                companies=company_details,
                results=[item["result"] for item in individual_results],
            )
            comparison["answer"] = research_result.get("answer")
            comparison["summary"] = research_result.get("answer")
            comparison_source = "research_agent"

    else:
        comparison = _comparison_to_dict(existing_comparison)
        comparison_source = "stored_comparison_result"
        research_result = await _research_answer_from_comparison(
            question=question,
            companies=company_details,
            comparison=comparison,
            conversation_history=conversation_history,
        )

    # =========================================================
    # 3. RESEARCH RESULT IS READY
    # =========================================================

    # =========================================================
    # 4. UPDATE COMPARISON CONVERSATION HISTORY
    # =========================================================

    updated_history = (
        _append_conversation_question(
            history=conversation_history,
            question=question,
        )
    )

    # =========================================================
    # 5. RETURN NEW SESSION
    # =========================================================

    new_session = _new_session(
        workspace_id=workspace_id,
        mode="comparison",
        company_ids=[
            str(company.id)
            for company in selected_companies
        ],
        company_names=[
            company.name
            for company in selected_companies
        ],
        document_ids=[
            str(document_id)
            for document_id in document_ids
        ],
        conversation_history=updated_history,
    )

    return {
        "session_id": new_session,
        "previous_session_id": session_id,
        "mode": mode,
        "question": question,
        "companies": company_details,
        "comparison": comparison,
        "comparison_source": comparison_source,
        "research_result": research_result,
        "conversation": {
            "context_used": bool(
                conversation_history
            ),
            "history_length": len(
                updated_history
            ),
            "next_question_uses_session_id": True,
        },
        "individual_results": individual_results,
        "suggestions": _generate_suggestions(
            question=question,
            companies=company_details,
            mode=mode,
        ),
    }