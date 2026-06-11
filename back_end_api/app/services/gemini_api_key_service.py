from __future__ import annotations

import asyncio
import json
import os
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.schemas.post_generation_schemas import GeneratedArticlePayload, GeneratedSection, PostCreate, TemplatePlan
from app.services.groq_service import (
    ArticleGenerationResult,
    GroqCallTracker,
    _assemble_article_html,
    _build_generation_diagnostics,
    _contains_any_batch_title,
    _fallback_outline_layouts,
    _layout_mentions_batch_titles,
    _normalize_generated_section,
)
from app.services.post_prompt_service import (
    ARTICLE_SYSTEM_PROMPT,
    build_article_user_prompt,
    build_section_outline_suggestions_prompt,
    build_template_plan_user_prompt,
    build_writing_style_suggestions_prompt,
)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
GEMINI_API_MAX_CONCURRENCY = int(os.getenv("GEMINI_API_MAX_CONCURRENCY", "6"))
_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


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


def _usage_from_response(response) -> dict[str, int]:
    usage = getattr(response, "usage_metadata", None)
    input_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
    output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
    total_tokens = int(getattr(usage, "total_token_count", 0) or (input_tokens + output_tokens))
    return {"input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": total_tokens}


def _get_client():
    if _client is None:
        raise RuntimeError("Missing GEMINI_API_KEY. Set it in .env or admin environment settings.")
    return _client


def _is_retryable_gemini_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(marker in message for marker in ("429", "500", "502", "503", "504", "timeout", "temporarily", "unavailable"))


async def _create_gemini_json(
    tracker: GroqCallTracker,
    stage_label: str,
    system_prompt: str,
    user_prompt: str,
    model: str,
    title: str | None = None,
) -> tuple[dict, dict[str, int]]:
    tracker.log_call(stage_label, title=title, extra=f"provider=gemini_api_key model={model}")
    started_at = time.perf_counter()
    response = await _get_client().aio.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.75,
            max_output_tokens=8192,
            response_mime_type="application/json",
        ),
    )
    elapsed = time.perf_counter() - started_at
    print(f"[GeminiApiKeyCall][{tracker.request_id}] stage={stage_label} title={title or '-'} elapsed={elapsed:.2f}s")
    json_text = _normalize_json_text(_extract_json_object(response.text or ""))
    return json.loads(json_text), _usage_from_response(response)


async def _create_gemini_json_with_retry(
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
            return await _create_gemini_json(tracker, stage_label, system_prompt, user_prompt, model, title)
        except Exception as error:
            last_error = error
            if attempt < 2 and (isinstance(error, json.JSONDecodeError) or _is_retryable_gemini_error(error)):
                tracker.log_retry(stage_label, title, attempt + 1, error)
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            raise last_error
    raise last_error


async def _generate_template_plan(post: PostCreate, tracker: GroqCallTracker, model: str) -> tuple[TemplatePlan, dict[str, int]]:
    template_json, usage = await _create_gemini_json_with_retry(
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
    article_json, usage = await _create_gemini_json_with_retry(
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
    diagnostics["provider"] = "gemini_api_key"
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


async def call_gemini_api_key_api(post: PostCreate):
    model = post.ai_model or GEMINI_MODEL
    tracker = GroqCallTracker(request_id=f"gemini-key-{len(post.titles)}t-{len(post.sections)}s")
    template_plan, template_usage = await _generate_template_plan(post, tracker, model)

    semaphore = asyncio.Semaphore(max(1, GEMINI_API_MAX_CONCURRENCY))

    async def generate_with_limit(title: str):
        async with semaphore:
            return await _generate_one(title, post.style, template_plan, tracker, model)

    tasks = (generate_with_limit(title) for title in post.titles)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    article_usage = _empty_usage()
    normalized_results: list[ArticleGenerationResult] = []
    for title, result in zip(post.titles, results):
        if isinstance(result, Exception):
            print(f"Gemini API key error for {title}: {result}")
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
    print(f"[GeminiApiKeySummary][{tracker.request_id}] {tracker.summary()} usage={run_usage}")
    return normalized_results


async def suggest_writing_styles_with_api_key(titles: list[str]) -> list[str]:
    cleaned_titles = [title.strip() for title in titles if isinstance(title, str) and title.strip()]
    fallback = [
        "SEO gioi thieu tung chu de",
        "Chuyen gia de hieu",
        "Than thien nhu tu van",
        "Cam nang thuc te",
        "Storytelling nhe, giau hinh anh",
        "Giao duc pho thong, de doc",
        "Editorial toi gian",
        "Chuyen sau nhung gan gui",
    ]
    if not cleaned_titles:
        return fallback

    try:
        tracker = GroqCallTracker(request_id=f"gemini-key-style-{len(cleaned_titles)}t")
        payload, _usage = await _create_gemini_json_with_retry(
            tracker,
            "style_suggestions",
            ARTICLE_SYSTEM_PROMPT,
            build_writing_style_suggestions_prompt(cleaned_titles),
            GEMINI_MODEL,
        )
        suggestions = payload.get("suggestions", [])
        cleaned = []
        for item in suggestions:
            if isinstance(item, str):
                value = item.strip()
                if value and not _contains_any_batch_title(value, cleaned_titles) and value not in cleaned:
                    cleaned.append(value[:90])
        return cleaned[:12] or fallback
    except Exception as error:
        print(f"Gemini API key style suggestion error: {error}")
        return fallback


async def suggest_section_outlines_with_api_key(titles: list[str], style: str, description: str = "") -> list[dict]:
    cleaned_titles = [title.strip() for title in titles if isinstance(title, str) and title.strip()]
    if not cleaned_titles:
        return _fallback_outline_layouts()

    try:
        tracker = GroqCallTracker(request_id=f"gemini-key-outline-{len(cleaned_titles)}t")
        payload, _usage = await _create_gemini_json_with_retry(
            tracker,
            "outline_suggestions",
            ARTICLE_SYSTEM_PROMPT,
            build_section_outline_suggestions_prompt(cleaned_titles, style.strip(), description.strip()),
            GEMINI_MODEL,
        )
        layouts = payload.get("layouts", [])
        normalized_layouts = []
        for layout in layouts:
            if not isinstance(layout, dict):
                continue
            sections = []
            for section in layout.get("sections", []):
                if not isinstance(section, dict):
                    continue
                try:
                    word_count = int(section.get("word_count", 250))
                except (TypeError, ValueError):
                    word_count = 250
                sections.append(
                    {
                        "title": str(section.get("title", "")).strip()[:200],
                        "role": str(section.get("role", "")).strip()[:500],
                        "word_count": max(50, min(5000, word_count)),
                        "description": str(section.get("description", "")).strip()[:2000],
                    }
                )
            sections = [section for section in sections if section["title"] and section["role"] and section["description"]]
            normalized = {
                "name": str(layout.get("name", "Bo cuc goi y")).strip()[:120],
                "summary": str(layout.get("summary", "")).strip()[:300],
                "sections": sections[:6],
            }
            if sections and not _layout_mentions_batch_titles(normalized, cleaned_titles):
                normalized_layouts.append(normalized)
        return normalized_layouts[:3] or _fallback_outline_layouts()
    except Exception as error:
        print(f"Gemini API key outline suggestion error: {error}")
        return _fallback_outline_layouts()
