from __future__ import annotations

import asyncio
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from app.schemas.post_generation_schemas import GeneratedArticlePayload, GeneratedSection, PostCreate, TemplatePlan
from app.services.groq_service import (
    ArticleGenerationResult,
    GroqCallTracker,
    _assemble_article_html,
    _build_generation_diagnostics,
    _normalize_generated_section,
)
from app.services.post_prompt_service import ARTICLE_SYSTEM_PROMPT, build_article_user_prompt, build_template_plan_user_prompt

load_dotenv()

DEFAULT_SERVICE_ACCOUNT_FILE = Path(__file__).resolve().parents[2] / "service-account.json"
VERTEX_SERVICE_ACCOUNT_FILE = os.getenv("VERTEX_SERVICE_ACCOUNT_FILE", str(DEFAULT_SERVICE_ACCOUNT_FILE))
VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "global")
VERTEX_GEMINI_MODEL = os.getenv("VERTEX_GEMINI_MODEL", "gemini-2.5-flash-lite")
VERTEX_MAX_CONCURRENCY = int(os.getenv("VERTEX_MAX_CONCURRENCY", "6"))
VERTEX_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
_credentials_lock = threading.Lock()
_cached_credentials = None
_cached_project_id = None


def _empty_usage() -> dict[str, int]:
    return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


def _combine_usage(*items: dict | None) -> dict[str, int]:
    combined = _empty_usage()
    for item in items:
        if not item:
            continue
        combined["input_tokens"] += int(item.get("input_tokens") or 0)
        combined["output_tokens"] += int(item.get("output_tokens") or 0)
        combined["total_tokens"] += int(item.get("total_tokens") or ((item.get("input_tokens") or 0) + (item.get("output_tokens") or 0)))
    return combined


def _extract_vertex_usage(payload: dict) -> dict[str, int]:
    usage = payload.get("usageMetadata") or {}
    input_tokens = int(usage.get("promptTokenCount") or 0)
    output_tokens = int(usage.get("candidatesTokenCount") or 0)
    total_tokens = int(usage.get("totalTokenCount") or (input_tokens + output_tokens))
    return {"input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": total_tokens}


def _load_credentials_from_file():
    if not Path(VERTEX_SERVICE_ACCOUNT_FILE).exists():
        raise RuntimeError(f"Missing Vertex service account file: {VERTEX_SERVICE_ACCOUNT_FILE}")

    return service_account.Credentials.from_service_account_file(
        VERTEX_SERVICE_ACCOUNT_FILE,
        scopes=[VERTEX_SCOPE],
    )


def _get_credentials():
    global _cached_credentials
    global _cached_project_id

    with _credentials_lock:
        if _cached_credentials is None:
            _cached_credentials = _load_credentials_from_file()
            _cached_project_id = _get_project_id(_cached_credentials)

        if not _cached_credentials.valid or _cached_credentials.expired:
            _cached_credentials.refresh(Request())

        return _cached_credentials, _cached_project_id


def _get_project_id(credentials) -> str:
    project_id = VERTEX_PROJECT_ID or getattr(credentials, "project_id", None)
    if not project_id:
        raise RuntimeError("Missing Vertex project id. Set VERTEX_PROJECT_ID or include project_id in service-account.json.")
    return project_id


def _vertex_endpoint(project_id: str, model: str) -> str:
    if VERTEX_LOCATION == "global":
        host = "aiplatform.googleapis.com"
    else:
        host = f"{VERTEX_LOCATION}-aiplatform.googleapis.com"
    return (
        f"https://{host}/v1/projects/{project_id}/locations/{VERTEX_LOCATION}"
        f"/publishers/google/models/{model}:generateContent"
    )


def _extract_vertex_text(payload: dict) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        raise ValueError("Vertex Gemini returned no candidates.")
    parts = candidates[0].get("content", {}).get("parts") or []
    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
    if not text.strip():
        raise ValueError("Vertex Gemini returned an empty text response.")
    return text.strip()


def _extract_json_object(text: str) -> str:
    cleaned = text.strip().replace("\ufeff", "")
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.DOTALL).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError("Gemini response did not contain a JSON object.")
    return match.group(0)


def _normalize_json_text(text: str) -> str:
    normalized = text.strip().replace("\ufeff", "")
    normalized = re.sub(r"\\u(?![0-9a-fA-F]{4})", r"\\\\u", normalized)
    normalized = re.sub(r"\\(?![\"\\/bfnrtu])", r"\\\\", normalized)
    return normalized


def _post_vertex_json(url: str, token: str, body: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Vertex Gemini HTTP {error.code}: {detail}") from error


def _is_retryable_vertex_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(marker in message for marker in ("429", "500", "502", "503", "504", "timeout", "temporarily"))


async def _create_vertex_json(
    tracker: GroqCallTracker,
    stage_label: str,
    system_prompt: str,
    user_prompt: str,
    model: str,
    title: str | None = None,
) -> tuple[dict, dict[str, int]]:
    tracker.log_call(stage_label, title=title, extra=f"provider=vertex_gemini model={model}")
    credentials, project_id = await asyncio.to_thread(_get_credentials)
    body = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.75,
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json",
        },
    }
    started_at = time.perf_counter()
    response_payload = await asyncio.to_thread(
        _post_vertex_json,
        _vertex_endpoint(project_id, model),
        credentials.token,
        body,
    )
    elapsed = time.perf_counter() - started_at
    print(f"[VertexGeminiCall][{tracker.request_id}] stage={stage_label} title={title or '-'} elapsed={elapsed:.2f}s")
    json_text = _normalize_json_text(_extract_json_object(_extract_vertex_text(response_payload)))
    return json.loads(json_text), _extract_vertex_usage(response_payload)


async def _create_vertex_json_with_retry(
    tracker: GroqCallTracker,
    stage_label: str,
    system_prompt: str,
    user_prompt: str,
    model: str,
    title: str | None = None,
) -> tuple[dict, dict[str, int]]:
    last_error = None
    for attempt in range(3):
        try:
            return await _create_vertex_json(tracker, stage_label, system_prompt, user_prompt, model, title)
        except Exception as error:
            last_error = error
            if attempt < 2 and (isinstance(error, json.JSONDecodeError) or _is_retryable_vertex_error(error)):
                tracker.log_retry(stage_label, title, attempt + 1, error)
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            raise last_error
    raise last_error


async def _generate_template_plan(post: PostCreate, tracker: GroqCallTracker, model: str) -> tuple[TemplatePlan, dict[str, int]]:
    template_json, usage = await _create_vertex_json_with_retry(
        tracker,
        "template",
        ARTICLE_SYSTEM_PROMPT,
        build_template_plan_user_prompt(post),
        model,
    )
    template_plan = TemplatePlan.model_validate(template_json)
    normalized_sections = [
        planned_section.model_copy(
            update={
                "title": requested_section.title,
                "role": requested_section.role,
                "description": requested_section.description,
                "target_word_count": requested_section.word_count,
            }
        )
        for requested_section, planned_section in zip(post.sections, template_plan.sections)
    ]
    return template_plan.model_copy(update={"sections": normalized_sections}), usage


async def _generate_one(title: str, style: str, template_plan: TemplatePlan, tracker: GroqCallTracker, model: str):
    article_json, usage = await _create_vertex_json_with_retry(
        tracker,
        "article",
        ARTICLE_SYSTEM_PROMPT,
        build_article_user_prompt(title, style, template_plan),
        model,
        title,
    )
    article_payload = GeneratedArticlePayload.model_validate(article_json)
    normalized_sections: list[GeneratedSection] = []
    for planned_section, generated_section in zip(template_plan.sections, article_payload.sections):
        normalized_sections.append(_normalize_generated_section(generated_section, planned_section.title))

    article_payload = article_payload.model_copy(update={"sections": normalized_sections})
    diagnostics = _build_generation_diagnostics(template_plan, article_payload)
    diagnostics["call_summary"] = tracker.summary()
    diagnostics["provider"] = "vertex_gemini"
    diagnostics["model"] = model
    diagnostics["usage"] = usage
    return ArticleGenerationResult(
        title=title,
        content=_assemble_article_html(title, article_payload),
        template_plan=template_plan.model_dump(),
        diagnostics=diagnostics,
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
    )


async def call_vertex_gemini_api(post: PostCreate):
    model = post.ai_model or VERTEX_GEMINI_MODEL
    tracker = GroqCallTracker(request_id=f"vertex-{len(post.titles)}t-{len(post.sections)}s")
    template_plan, template_usage = await _generate_template_plan(post, tracker, model)

    semaphore = asyncio.Semaphore(max(1, VERTEX_MAX_CONCURRENCY))

    async def generate_with_limit(title: str):
        async with semaphore:
            return await _generate_one(title, post.style, template_plan, tracker, model)

    tasks = (generate_with_limit(title) for title in post.titles)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    article_usage = _empty_usage()
    normalized_results: list[ArticleGenerationResult] = []
    for title, result in zip(post.titles, results):
        if isinstance(result, Exception):
            print(f"Vertex Gemini error for {title}: {result}")
            normalized_results.append(
                ArticleGenerationResult(
                    title=title,
                    content=f"AI_ERROR: {result}",
                    template_plan=template_plan.model_dump(),
                )
            )
        else:
            article_usage = _combine_usage(article_usage, {"input_tokens": result.input_tokens, "output_tokens": result.output_tokens})
            normalized_results.append(result)

    run_usage = _combine_usage(template_usage, article_usage)
    if normalized_results:
        normalized_results[0].diagnostics = {
            **(normalized_results[0].diagnostics or {}),
            "run_usage": run_usage,
            "template_usage": template_usage,
        }
    print(f"[VertexGeminiSummary][{tracker.request_id}] {tracker.summary()} usage={run_usage}")
    return normalized_results
