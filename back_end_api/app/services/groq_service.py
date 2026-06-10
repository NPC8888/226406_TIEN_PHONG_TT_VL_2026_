from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass
from html import escape
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.schemas.post_generation_schemas import (
    GeneratedArticlePayload,
    GeneratedSection,
    PostCreate,
    TemplatePlan,
)
from app.services.post_prompt_service import (
    ARTICLE_SYSTEM_PROMPT,
    JSON_REPAIR_SYSTEM_PROMPT,
    build_article_user_prompt,
    build_json_repair_user_prompt,
    build_regeneration_user_prompt,
    build_section_outline_suggestions_prompt,
    build_template_plan_user_prompt,
    build_writing_style_suggestions_prompt,
)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
WORD_TOLERANCE_RATIO = 0.2
MAX_SECTION_REGENERATIONS_PER_ARTICLE = 2


@dataclass
class ArticleGenerationResult:
    title: str
    content: str
    template_plan: dict | None = None
    diagnostics: dict | None = None
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class GroqCallTracker:
    request_id: str
    total_calls: int = 0
    template_calls: int = 0
    article_calls: int = 0
    repair_calls: int = 0
    regeneration_calls: int = 0
    retries: int = 0

    def log_call(self, stage: str, title: str | None = None, extra: str | None = None):
        self.total_calls += 1
        if stage == "template":
            self.template_calls += 1
        elif stage == "article":
            self.article_calls += 1
        elif stage == "repair":
            self.repair_calls += 1
        elif stage == "regeneration":
            self.regeneration_calls += 1
        message = f"[GroqCall][{self.request_id}] #{self.total_calls} stage={stage}"
        if title:
            message += f" title={title}"
        if extra:
            message += f" {extra}"
        print(message)

    def log_retry(self, stage: str, title: str | None, attempt: int, error: Exception):
        self.retries += 1
        message = f"[GroqRetry][{self.request_id}] stage={stage} attempt={attempt}"
        if title:
            message += f" title={title}"
        message += f" error={error}"
        print(message)

    def summary(self) -> dict[str, int | str]:
        return {
            "request_id": self.request_id,
            "total_calls": self.total_calls,
            "template_calls": self.template_calls,
            "article_calls": self.article_calls,
            "repair_calls": self.repair_calls,
            "regeneration_calls": self.regeneration_calls,
            "retries": self.retries,
        }


def _get_client():
    if not GROQ_API_KEY:
        raise RuntimeError("Missing GROQ_API_KEY in environment configuration.")
    return OpenAI(
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
    )


def _is_retryable_groq_error(error: Exception) -> bool:
    message = str(error)
    retry_markers = (
        "503",
        "Service Unavailable",
        "Rate limit",
        "429",
        "timeout",
        "timed out",
    )
    return any(marker.lower() in message.lower() for marker in retry_markers)


def _extract_json_object(text: str) -> str:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("Model did not return a JSON object.")
    return match.group(0)


def _normalize_json_text(text: str) -> str:
    normalized = text.strip().replace("\ufeff", "")
    normalized = re.sub(r"\\u(?![0-9a-fA-F]{4})", r"\\\\u", normalized)
    normalized = re.sub(r"\\(?![\"\\/bfnrtu])", r"\\\\", normalized)
    return normalized


def _strip_html_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text).strip()


def _sanitize_plain_text(text: str) -> str:
    cleaned = _strip_html_tags(text or "")
    return re.sub(r"\s+", " ", cleaned).strip()


def _section_plain_text(section: GeneratedSection) -> str:
    parts = [*section.paragraphs, *section.bullets]
    if not parts and section.html:
        parts = [_strip_html_tags(section.html)]
    return " ".join(_sanitize_plain_text(part) for part in parts)


def _count_vietnamese_words(text: str) -> int:
    text = _strip_html_tags(text)
    if not text:
        return 0
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))


def _section_bounds(target_word_count: int) -> tuple[int, int]:
    return (
        max(1, int(target_word_count * (1 - WORD_TOLERANCE_RATIO))),
        max(1, int(target_word_count * (1 + WORD_TOLERANCE_RATIO))),
    )


def _sanitize_inner_html(fragment: str) -> str:
    cleaned = (fragment or "").strip()
    cleaned = re.sub(r"^<section[^>]*>|</section>$", "", cleaned, flags=re.DOTALL).strip()
    cleaned = re.sub(r"^<h2[^>]*>.*?</h2>", "", cleaned, flags=re.DOTALL).strip()
    return cleaned


def _paragraphs_from_legacy_html(fragment: str) -> list[str]:
    blocks = re.findall(r"<p[^>]*>(.*?)</p>", fragment or "", flags=re.DOTALL)
    if blocks:
        return [_sanitize_plain_text(block) for block in blocks if _sanitize_plain_text(block)]
    text = _sanitize_plain_text(fragment or "")
    return [text] if text else []


def _normalize_generated_section(section: GeneratedSection, planned_title: str) -> GeneratedSection:
    paragraphs = [_sanitize_plain_text(item) for item in section.paragraphs if _sanitize_plain_text(item)]
    bullets = [_sanitize_plain_text(item) for item in section.bullets if _sanitize_plain_text(item)]
    if not paragraphs and section.html:
        paragraphs = _paragraphs_from_legacy_html(section.html)
    if not paragraphs:
        paragraphs = [""]
    normalized = section.model_copy(
        update={
            "title": planned_title,
            "paragraphs": paragraphs,
            "bullets": bullets,
            "html": None,
            "estimated_word_count": _count_vietnamese_words(" ".join([*paragraphs, *bullets])),
        }
    )
    return normalized


def _assemble_article_html(title: str, article_payload: GeneratedArticlePayload) -> str:
    section_blocks = []
    for section in article_payload.sections:
        paragraph_blocks = [f"    <p>{escape(paragraph)}</p>" for paragraph in section.paragraphs if paragraph.strip()]
        bullet_block = []
        if section.bullets:
            bullet_block = [
                "    <ul>",
                *[f"      <li>{escape(item)}</li>" for item in section.bullets if item.strip()],
                "    </ul>",
            ]
        section_blocks.append(
            "\n".join(
                [
                    '  <section class="generated-article-section">',
                    f"    <h2>{escape(section.title)}</h2>",
                    *paragraph_blocks,
                    *bullet_block,
                    "  </section>",
                ]
            )
        )

    return "\n".join(
        [
            '<article class="generated-article">',
            '  <header class="generated-article-header">',
            f"    <h1>{escape(title)}</h1>",
            "  </header>",
            *section_blocks,
            "</article>",
        ]
    )


def _build_generation_diagnostics(template_plan: TemplatePlan, article_payload: GeneratedArticlePayload) -> dict:
    section_diagnostics = []
    for plan_section, rendered_section in zip(template_plan.sections, article_payload.sections):
        actual_word_count = _count_vietnamese_words(_section_plain_text(rendered_section))
        min_words, max_words = _section_bounds(plan_section.target_word_count)
        section_diagnostics.append(
            {
                "title": rendered_section.title,
                "target_word_count": plan_section.target_word_count,
                "estimated_word_count": rendered_section.estimated_word_count,
                "actual_word_count": actual_word_count,
                "allowed_min": min_words,
                "allowed_max": max_words,
                "within_range": min_words <= actual_word_count <= max_words,
            }
        )
    return {"sections": section_diagnostics}


def _word_count_distance(actual_word_count: int, min_words: int, max_words: int) -> int:
    if actual_word_count < min_words:
        return min_words - actual_word_count
    if actual_word_count > max_words:
        return actual_word_count - max_words
    return 0


async def _repair_malformed_json(client: OpenAI, tracker: GroqCallTracker, raw_text: str, stage_label: str, title: str | None) -> str:
    tracker.log_call("repair", title=title, extra=f"source={stage_label}")
    response = await asyncio.to_thread(
        client.responses.create,
        model=GROQ_MODEL,
        input=[
            {"role": "system", "content": [{"type": "input_text", "text": JSON_REPAIR_SYSTEM_PROMPT}]},
            {"role": "user", "content": [{"type": "input_text", "text": build_json_repair_user_prompt(raw_text)}]},
        ],
    )
    repaired_text = response.output_text.strip()
    return _normalize_json_text(_extract_json_object(repaired_text))


async def _create_response_json(
    client: OpenAI,
    tracker: GroqCallTracker,
    stage_label: str,
    system_prompt: str,
    user_prompt: str,
    title: str | None = None,
) -> dict:
    tracker.log_call(stage_label, title=title)
    response = await asyncio.to_thread(
        client.responses.create,
        model=GROQ_MODEL,
        input=[
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
        ],
    )
    raw_text = response.output_text.strip()
    json_text = _normalize_json_text(_extract_json_object(raw_text))
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        repaired = await _repair_malformed_json(client, tracker, json_text, stage_label, title)
        return json.loads(_normalize_json_text(repaired))


async def _create_response_json_with_retry(
    client: OpenAI,
    tracker: GroqCallTracker,
    stage_label: str,
    system_prompt: str,
    user_prompt: str,
    title: str | None = None,
) -> dict:
    attempts = 3
    last_error = None
    for attempt in range(attempts):
        try:
            return await _create_response_json(client, tracker, stage_label, system_prompt, user_prompt, title)
        except Exception as error:
            last_error = error
            if attempt < attempts - 1 and (isinstance(error, json.JSONDecodeError) or _is_retryable_groq_error(error)):
                tracker.log_retry(stage_label, title, attempt + 1, error)
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            raise last_error
    raise last_error


async def _generate_template_plan(post: PostCreate, tracker: GroqCallTracker) -> TemplatePlan:
    client = _get_client()
    template_json = await _create_response_json_with_retry(
        client,
        tracker,
        "template",
        ARTICLE_SYSTEM_PROMPT,
        build_template_plan_user_prompt(post),
    )
    template_plan = TemplatePlan.model_validate(template_json)

    if len(template_plan.sections) != len(post.sections):
        raise ValueError("Template plan returned a different number of sections than requested.")

    normalized_sections = []
    for requested_section, planned_section in zip(post.sections, template_plan.sections):
        normalized_sections.append(
            planned_section.model_copy(
                update={
                    "title": requested_section.title,
                    "role": requested_section.role,
                    "description": requested_section.description,
                    "target_word_count": requested_section.word_count,
                }
            )
        )

    return template_plan.model_copy(update={"sections": normalized_sections})


async def _regenerate_section(
    client: OpenAI,
    tracker: GroqCallTracker,
    title: str,
    style: str,
    template_plan: TemplatePlan,
    section_index: int,
    actual_word_count: int,
) -> GeneratedSection:
    target_section = template_plan.sections[section_index]
    regen_json = await _create_response_json_with_retry(
        client,
        tracker,
        "regeneration",
        ARTICLE_SYSTEM_PROMPT,
        build_regeneration_user_prompt(title, style, template_plan, section_index, actual_word_count),
        title,
    )
    regenerated = GeneratedSection.model_validate(regen_json)
    return _normalize_generated_section(regenerated, target_section.title)
async def _generate_one(
    title: str,
    style: str,
    template_plan: TemplatePlan,
    tracker: GroqCallTracker,
) -> ArticleGenerationResult:
    client = _get_client()
    article_json = await _create_response_json_with_retry(
        client,
        tracker,
        "article",
        ARTICLE_SYSTEM_PROMPT,
        build_article_user_prompt(title, style, template_plan),
        title,
    )
    article_payload = GeneratedArticlePayload.model_validate(article_json)

    if len(article_payload.sections) != len(template_plan.sections):
        raise ValueError(f"Article '{title}' returned {len(article_payload.sections)} sections, expected {len(template_plan.sections)}.")

    normalized_sections: list[GeneratedSection] = []
    regenerate_candidates: list[dict[str, Any]] = []
    for index, (planned_section, generated_section) in enumerate(zip(template_plan.sections, article_payload.sections)):
        normalized = _normalize_generated_section(generated_section, planned_section.title)
        actual_word_count = _count_vietnamese_words(_section_plain_text(normalized))
        min_words, max_words = _section_bounds(planned_section.target_word_count)
        title_matches = generated_section.title.strip().lower() == planned_section.title.strip().lower()
        normalized_sections.append(normalized)
        if (not title_matches) or not (min_words <= actual_word_count <= max_words):
            regenerate_candidates.append(
                {
                    "index": index,
                    "actual_word_count": actual_word_count,
                    "distance": _word_count_distance(actual_word_count, min_words, max_words) + (100000 if not title_matches else 0),
                }
            )

    regenerate_candidates.sort(key=lambda item: item["distance"], reverse=True)
    selected_candidates = regenerate_candidates[:MAX_SECTION_REGENERATIONS_PER_ARTICLE]
    if regenerate_candidates:
        print(
            f"[GroqRegenPlan][{tracker.request_id}] title={title} "
            f"candidates={len(regenerate_candidates)} selected={len(selected_candidates)} "
            f"max_per_article={MAX_SECTION_REGENERATIONS_PER_ARTICLE}"
        )

    for candidate in selected_candidates:
        regenerated = await _regenerate_section(
            client,
            tracker,
            title,
            style,
            template_plan,
            candidate["index"],
            candidate["actual_word_count"],
        )
        normalized_sections[candidate["index"]] = regenerated

    article_payload = article_payload.model_copy(
        update={
            "sections": normalized_sections,
        }
    )

    diagnostics = _build_generation_diagnostics(template_plan, article_payload)
    diagnostics["call_summary"] = tracker.summary()
    html = _assemble_article_html(title, article_payload)
    return ArticleGenerationResult(
        title=title,
        content=html,
        template_plan=template_plan.model_dump(),
        diagnostics=diagnostics,
    )


async def call_ai_api(post: PostCreate):
    tracker = GroqCallTracker(request_id=f"{len(post.titles)}t-{len(post.sections)}s")
    template_plan = await _generate_template_plan(post, tracker)
    tasks = (_generate_one(title, post.style, template_plan, tracker) for title in post.titles)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    normalized_results: list[ArticleGenerationResult] = []
    for title, result in zip(post.titles, results):
        if isinstance(result, Exception):
            print(f"Groq error for {title}: {result}")
            normalized_results.append(
                ArticleGenerationResult(
                    title=title,
                    content=f"AI_ERROR: {result}",
                    template_plan=template_plan.model_dump(),
                )
            )
        else:
            normalized_results.append(result)

    print(f"[GroqSummary][{tracker.request_id}] {tracker.summary()}")
    return normalized_results


async def suggest_writing_styles(titles: list[str]) -> list[str]:
    cleaned_titles = [title.strip() for title in titles if isinstance(title, str) and title.strip()]
    fallback = [
        "SEO chuyên gia, rõ ràng",
        "Thân thiện như tư vấn",
        "Editorial tối giản",
        "Persuasive, tập trung chuyển đổi",
        "Storytelling có ví dụ thực tế",
        "Hướng dẫn từng bước",
        "So sánh khách quan",
        "Chuyên sâu nhưng dễ hiểu",
    ]
    if not cleaned_titles:
        return fallback

    try:
        client = _get_client()
        tracker = GroqCallTracker(request_id=f"style-{len(cleaned_titles)}t")
        payload = await _create_response_json_with_retry(
            client,
            tracker,
            "style_suggestions",
            ARTICLE_SYSTEM_PROMPT,
            build_writing_style_suggestions_prompt(cleaned_titles),
        )
        suggestions = payload.get("suggestions", [])
        cleaned = []
        for item in suggestions:
            if isinstance(item, str):
                value = item.strip()
                if value and value not in cleaned:
                    cleaned.append(value[:90])
        return cleaned[:12] or fallback
    except Exception as error:
        print(f"Groq style suggestion error: {error}")
        return fallback


def _fallback_outline_layouts() -> list[dict]:
    return [
        {
            "name": "Bố cục hướng dẫn thực hành",
            "summary": "Đi từ vấn đề đến các bước làm cụ thể, phù hợp bài giải thích và tutorial.",
            "sections": [
                {
                    "title": "Mở đầu vấn đề",
                    "role": "Nêu bối cảnh ngắn gọn, chỉ ra lý do người đọc nên quan tâm ngay.",
                    "word_count": 180,
                    "description": "Giới thiệu chủ đề, pain point chính và kết quả người đọc sẽ nhận được.",
                },
                {
                    "title": "Nguyên nhân cốt lõi",
                    "role": "Phân tích rõ nguyên nhân, tránh nói chung chung hoặc liệt kê quá dài.",
                    "word_count": 260,
                    "description": "Làm rõ các yếu tố khiến vấn đề xuất hiện và tác động tới người đọc.",
                },
                {
                    "title": "Cách triển khai từng bước",
                    "role": "Viết như một hướng dẫn thực tế, có trình tự và ví dụ dễ áp dụng.",
                    "word_count": 420,
                    "description": "Đưa ra các bước xử lý, lưu ý quan trọng và mẹo để tránh sai lầm.",
                },
                {
                    "title": "Kết luận và hành động tiếp theo",
                    "role": "Tóm tắt ngắn, nhấn mạnh việc nên làm ngay sau khi đọc.",
                    "word_count": 160,
                    "description": "Chốt lại insight chính và gợi ý hành động cụ thể cho người đọc.",
                },
            ],
        },
        {
            "name": "Bố cục chuyên gia phân tích",
            "summary": "Phù hợp bài chuyên sâu, cần tạo niềm tin và giải thích có lập luận.",
            "sections": [
                {
                    "title": "Bức tranh tổng quan",
                    "role": "Đặt vấn đề ở góc nhìn rộng, thể hiện hiểu biết chuyên môn.",
                    "word_count": 220,
                    "description": "Mô tả bối cảnh thị trường, xu hướng hoặc nhu cầu liên quan tới chủ đề.",
                },
                {
                    "title": "Các tiêu chí đánh giá",
                    "role": "Đưa ra khung phân tích rõ ràng để người đọc hiểu cách ra quyết định.",
                    "word_count": 320,
                    "description": "Nêu tiêu chí, yếu tố cần cân nhắc và vì sao chúng quan trọng.",
                },
                {
                    "title": "Phân tích giải pháp",
                    "role": "So sánh ưu nhược điểm, viết cân bằng và có chiều sâu.",
                    "word_count": 420,
                    "description": "Phân tích các hướng tiếp cận, trường hợp nên dùng và rủi ro cần tránh.",
                },
                {
                    "title": "Khuyến nghị cuối cùng",
                    "role": "Đưa lời khuyên rõ, có điều kiện áp dụng thay vì kết luận mơ hồ.",
                    "word_count": 180,
                    "description": "Tổng hợp nhận định và đề xuất lựa chọn phù hợp cho từng nhóm người đọc.",
                },
            ],
        },
        {
            "name": "Bố cục thuyết phục chuyển đổi",
            "summary": "Tập trung nhu cầu người đọc, lợi ích rõ ràng và lời kêu gọi hành động mềm.",
            "sections": [
                {
                    "title": "Nỗi đau của người đọc",
                    "role": "Viết gần gũi, đánh trúng tình huống người đọc đang gặp.",
                    "word_count": 220,
                    "description": "Mô tả vấn đề bằng ngôn ngữ đời thường và hệ quả nếu không xử lý.",
                },
                {
                    "title": "Lợi ích khi làm đúng",
                    "role": "Chuyển trọng tâm sang kết quả, lợi ích cụ thể và dễ hình dung.",
                    "word_count": 300,
                    "description": "Làm rõ giá trị người đọc nhận được sau khi áp dụng hướng giải quyết.",
                },
                {
                    "title": "Cách áp dụng hiệu quả",
                    "role": "Đưa giải pháp thực tế, ưu tiên tính khả thi và ví dụ minh họa.",
                    "word_count": 380,
                    "description": "Trình bày phương pháp, checklist hoặc ví dụ giúp người đọc hành động.",
                },
                {
                    "title": "Lời khuyên chốt",
                    "role": "Kết thúc tự nhiên, thúc đẩy hành động mà không quá bán hàng.",
                    "word_count": 160,
                    "description": "Nhắc lại điểm đáng nhớ nhất và gợi ý bước tiếp theo.",
                },
            ],
        },
    ]


async def suggest_section_outlines(titles: list[str], style: str, description: str = "") -> list[dict]:
    cleaned_titles = [title.strip() for title in titles if isinstance(title, str) and title.strip()]
    if not cleaned_titles:
        return _fallback_outline_layouts()

    try:
        client = _get_client()
        tracker = GroqCallTracker(request_id=f"outline-{len(cleaned_titles)}t")
        payload = await _create_response_json_with_retry(
            client,
            tracker,
            "outline_suggestions",
            ARTICLE_SYSTEM_PROMPT,
            build_section_outline_suggestions_prompt(cleaned_titles, style.strip(), description.strip()),
        )
        layouts = payload.get("layouts", [])
        normalized_layouts = []
        for layout in layouts:
            sections = []
            for section in layout.get("sections", []):
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
            if sections:
                normalized_layouts.append(
                    {
                        "name": str(layout.get("name", "Bố cục gợi ý")).strip()[:120],
                        "summary": str(layout.get("summary", "")).strip()[:300],
                        "sections": sections[:6],
                    }
                )
        return normalized_layouts[:3] or _fallback_outline_layouts()
    except Exception as error:
        print(f"Groq outline suggestion error: {error}")
        return _fallback_outline_layouts()


def _contains_any_batch_title(text: str, titles: list[str]) -> bool:
    normalized_text = (text or "").strip().lower()
    return any(title.strip().lower() in normalized_text for title in titles if title.strip())


def _layout_mentions_batch_titles(layout: dict, titles: list[str]) -> bool:
    text_parts = [
        str(layout.get("name", "")),
        str(layout.get("summary", "")),
    ]
    for section in layout.get("sections", []):
        text_parts.extend(
            [
                str(section.get("title", "")),
                str(section.get("role", "")),
                str(section.get("description", "")),
            ]
        )
    return _contains_any_batch_title(" ".join(text_parts), titles)


def _fallback_outline_layouts() -> list[dict]:
    return [
        {
            "name": "Bố cục giới thiệu từng chủ đề",
            "summary": "Dùng chung cho mỗi bài riêng lẻ: giới thiệu, đặc điểm, ý nghĩa và lưu ý thực tế.",
            "sections": [
                {
                    "title": "Tổng quan về chủ đề",
                    "role": "Giới thiệu ngắn gọn chủ đề hiện tại, không nhắc hoặc so sánh với các tiêu đề khác.",
                    "word_count": 180,
                    "description": "Mở bài cho riêng tiêu đề hiện tại, nêu điều người đọc sẽ hiểu sau khi đọc.",
                },
                {
                    "title": "Đặc điểm nổi bật",
                    "role": "Mô tả các đặc điểm riêng của đối tượng trong tiêu đề hiện tại.",
                    "word_count": 260,
                    "description": "Làm rõ hình dáng, tính chất, điểm nhận biết hoặc thuộc tính quan trọng của chủ đề.",
                },
                {
                    "title": "Ý nghĩa và giá trị",
                    "role": "Giải thích ý nghĩa, giá trị văn hóa, ứng dụng hoặc lợi ích của chủ đề này.",
                    "word_count": 300,
                    "description": "Viết theo hướng giúp người đọc hiểu vì sao chủ đề hiện tại đáng quan tâm.",
                },
                {
                    "title": "Lưu ý khi tìm hiểu hoặc sử dụng",
                    "role": "Đưa các lưu ý thực tế, mẹo áp dụng hoặc thông tin cần tránh hiểu sai.",
                    "word_count": 220,
                    "description": "Cung cấp phần thực tế cho riêng chủ đề hiện tại, không liên kết sang tiêu đề khác.",
                },
            ],
        },
        {
            "name": "Bố cục chuyên gia chuyên sâu",
            "summary": "Dùng cho mỗi bài độc lập cần phân tích kỹ nguồn gốc, đặc trưng và vai trò.",
            "sections": [
                {
                    "title": "Nguồn gốc và bối cảnh",
                    "role": "Trình bày nguồn gốc hoặc bối cảnh của chủ đề hiện tại bằng giọng chuyên gia.",
                    "word_count": 220,
                    "description": "Giúp người đọc hiểu chủ đề này đến từ đâu và vì sao nó được quan tâm.",
                },
                {
                    "title": "Đặc trưng nhận biết",
                    "role": "Phân tích các đặc trưng riêng, có ví dụ hoặc tiêu chí nhận diện rõ ràng.",
                    "word_count": 320,
                    "description": "Nêu những dấu hiệu, thuộc tính hoặc yếu tố khiến chủ đề hiện tại khác biệt.",
                },
                {
                    "title": "Vai trò trong đời sống",
                    "role": "Phân tích vai trò, ứng dụng hoặc ảnh hưởng của chủ đề này trong thực tế.",
                    "word_count": 420,
                    "description": "Liên hệ đời sống, văn hóa, thói quen sử dụng hoặc nhu cầu của người đọc.",
                },
                {
                    "title": "Kết luận ngắn gọn",
                    "role": "Tóm tắt riêng về chủ đề hiện tại và chốt lại điểm đáng nhớ.",
                    "word_count": 180,
                    "description": "Kết thúc bài bằng nhận định rõ ràng, không nhắc tới các tiêu đề khác trong batch.",
                },
            ],
        },
        {
            "name": "Bố cục kể chuyện dễ đọc",
            "summary": "Dùng cho mỗi bài riêng lẻ cần giọng văn mềm, giàu hình ảnh và dễ tiếp cận.",
            "sections": [
                {
                    "title": "Ấn tượng đầu tiên",
                    "role": "Mở bài bằng hình ảnh hoặc cảm nhận về chủ đề hiện tại.",
                    "word_count": 220,
                    "description": "Tạo cảm xúc ban đầu cho người đọc trước khi đi vào thông tin chính.",
                },
                {
                    "title": "Câu chuyện phía sau",
                    "role": "Kể nguồn gốc, ý nghĩa hoặc bối cảnh thú vị của riêng chủ đề này.",
                    "word_count": 300,
                    "description": "Đưa các chi tiết giàu hình ảnh để bài viết có chiều sâu và dễ nhớ.",
                },
                {
                    "title": "Điểm đáng chú ý",
                    "role": "Liệt kê và giải thích các điểm nổi bật nhưng vẫn giữ giọng văn tự nhiên.",
                    "word_count": 360,
                    "description": "Làm rõ các đặc điểm, giá trị hoặc ứng dụng nổi bật của chủ đề hiện tại.",
                },
                {
                    "title": "Gợi ý ghi nhớ",
                    "role": "Chốt bài nhẹ nhàng, giúp người đọc nhớ ý chính về chủ đề hiện tại.",
                    "word_count": 160,
                    "description": "Tóm tắt thông điệp chính bằng ngôn ngữ gần gũi.",
                },
            ],
        },
    ]


async def suggest_writing_styles(titles: list[str]) -> list[str]:
    cleaned_titles = [title.strip() for title in titles if isinstance(title, str) and title.strip()]
    fallback = [
        "SEO giới thiệu từng chủ đề",
        "Chuyên gia dễ hiểu",
        "Thân thiện như tư vấn",
        "Cẩm nang thực tế",
        "Storytelling nhẹ, giàu hình ảnh",
        "Giáo dục phổ thông, dễ đọc",
        "Editorial tối giản",
        "Chuyên sâu nhưng gần gũi",
    ]
    if not cleaned_titles:
        return fallback

    try:
        client = _get_client()
        tracker = GroqCallTracker(request_id=f"style-{len(cleaned_titles)}t")
        payload = await _create_response_json_with_retry(
            client,
            tracker,
            "style_suggestions",
            ARTICLE_SYSTEM_PROMPT,
            build_writing_style_suggestions_prompt(cleaned_titles),
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
        print(f"Groq style suggestion error: {error}")
        return fallback


async def suggest_section_outlines(titles: list[str], style: str, description: str = "") -> list[dict]:
    cleaned_titles = [title.strip() for title in titles if isinstance(title, str) and title.strip()]
    if not cleaned_titles:
        return _fallback_outline_layouts()

    try:
        client = _get_client()
        tracker = GroqCallTracker(request_id=f"outline-{len(cleaned_titles)}t")
        payload = await _create_response_json_with_retry(
            client,
            tracker,
            "outline_suggestions",
            ARTICLE_SYSTEM_PROMPT,
            build_section_outline_suggestions_prompt(cleaned_titles, style.strip(), description.strip()),
        )
        layouts = payload.get("layouts", [])
        normalized_layouts = []
        for layout in layouts:
            sections = []
            for section in layout.get("sections", []):
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
                "name": str(layout.get("name", "Bố cục gợi ý")).strip()[:120],
                "summary": str(layout.get("summary", "")).strip()[:300],
                "sections": sections[:6],
            }
            if sections and not _layout_mentions_batch_titles(normalized, cleaned_titles):
                normalized_layouts.append(normalized)
        return normalized_layouts[:3] or _fallback_outline_layouts()
    except Exception as error:
        print(f"Groq outline suggestion error: {error}")
        return _fallback_outline_layouts()
