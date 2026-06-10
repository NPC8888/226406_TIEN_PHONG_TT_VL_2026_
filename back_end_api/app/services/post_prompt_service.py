from __future__ import annotations

from json import dumps

from app.schemas.post_generation_schemas import PostCreate, Section, TemplatePlan
from app.schemas.repo_schemas import PostResponse

WORD_TOLERANCE_RATIO = 0.2


ARTICLE_SYSTEM_PROMPT = """You are a senior Vietnamese SEO content strategist and structured article writer.

Global rules:
- Final content must be 100% natural Vietnamese.
- Never output Markdown, code fences, XML, explanations, or meta commentary.
- Follow the requested structure exactly.
- Keep the same presentation pattern for every article in the same batch.
- Prefer concrete, useful, non-repetitive writing.
- Respect section order, section scope, and section word targets.
- When returning JSON, every string value must be valid JSON with escaped double quotes.
- Never write HTML tags or inline CSS in article content fields.
- Write content only; the application will render all HTML and visual style.
"""


JSON_REPAIR_SYSTEM_PROMPT = """You repair malformed model outputs into valid JSON.

Rules:
- Return JSON only.
- Preserve the original meaning as much as possible.
- Do not add explanations.
- Escape quotes correctly.
- If the payload contains HTML fragments, keep them as strings and make the JSON syntactically valid.
"""


def _section_payload(section: Section) -> dict:
    return {
        "title": section.title,
        "role": section.role,
        "description": section.description,
        "target_word_count": section.word_count,
        "allowed_word_range": {
            "min": max(1, int(section.word_count * (1 - WORD_TOLERANCE_RATIO))),
            "max": max(1, int(section.word_count * (1 + WORD_TOLERANCE_RATIO))),
        },
    }


def build_template_plan_user_prompt(post: PostCreate) -> str:
    payload = {
        "style": post.style.strip(),
        "sections": [_section_payload(section) for section in post.sections],
        "task": {
            "goal": "Create one reusable batch template plan shared by every article title in this request.",
            "requirements": [
                "Return JSON only.",
                "Preserve the exact section titles and order.",
                "For each section, define required_elements and subsection_strategy.",
                "Keep the plan title-agnostic so it can be reused across all titles in the batch.",
                "Keep the same content structure for all articles in the batch.",
                "Do not create an extra conclusion section unless it already exists in the provided sections.",
            ],
            "json_shape": {
                "html_pattern_notes": ["string"],
                "sections": [
                    {
                        "title": "string",
                        "role": "string",
                        "description": "string",
                        "target_word_count": 250,
                        "required_elements": ["string"],
                        "subsection_strategy": "string",
                    }
                ],
            },
        },
    }
    return dumps(payload, ensure_ascii=False, indent=2)


def build_article_user_prompt(title: str, style: str, template_plan: TemplatePlan) -> str:
    payload = {
        "title": title,
        "style": style.strip(),
        "template_plan": template_plan.model_dump(),
        "task": {
            "goal": "Write one full Vietnamese article payload as strict JSON.",
            "requirements": [
                "Return JSON only.",
                "Use the exact same section titles and order from template_plan.sections.",
                "Do not add or remove sections.",
                "Do not write HTML, Markdown, headings, code fences, or inline styling.",
                "Each section paragraphs array must contain plain Vietnamese paragraphs only.",
                "Only use bullets when the section genuinely needs a short list; otherwise return an empty bullets array.",
                "Each section must stay close to target_word_count and estimate it honestly.",
                "If quotation marks appear in text, escape them correctly for JSON.",
                "Do not create a separate conclusion field or extra closing section unless the provided outline already includes one.",
                "Do not create an introduction block before section 1.",
            ],
            "json_shape": {
                "sections": [
                    {
                        "title": "string",
                        "paragraphs": ["string"],
                        "bullets": ["string"],
                        "estimated_word_count": 250,
                    }
                ],
            },
        },
    }
    return dumps(payload, ensure_ascii=False, indent=2)


def build_regeneration_user_prompt(
    title: str,
    style: str,
    template_plan: TemplatePlan,
    section_index: int,
    actual_word_count: int,
) -> str:
    target_section = template_plan.sections[section_index]
    payload = {
        "title": title,
        "style": style.strip(),
        "template_plan": template_plan.model_dump(),
        "target_section": {
            "index": section_index,
            "title": target_section.title,
            "role": target_section.role,
            "description": target_section.description,
            "target_word_count": target_section.target_word_count,
            "allowed_word_range": {
                "min": max(1, int(target_section.target_word_count * (1 - WORD_TOLERANCE_RATIO))),
                "max": max(1, int(target_section.target_word_count * (1 + WORD_TOLERANCE_RATIO))),
            },
            "required_elements": target_section.required_elements,
            "subsection_strategy": target_section.subsection_strategy,
        },
        "current_issue": {
            "actual_word_count": actual_word_count,
            "problem": "Section word count is outside the allowed range or the content drifted from the requested scope.",
        },
        "task": {
            "goal": "Rewrite only this section as strict JSON.",
            "requirements": [
                "Return JSON only.",
                "Do not write the full article.",
                "Keep the exact same section title.",
                "Return only one object with title, paragraphs, bullets, estimated_word_count.",
                "Do not write HTML, Markdown, headings, code fences, or inline styling.",
                "The paragraphs array must contain plain Vietnamese paragraphs only.",
                "Only use bullets when useful; otherwise return an empty bullets array.",
                "Bring the section back within the allowed word range.",
                "If quotation marks appear in text, escape them correctly for JSON.",
            ],
            "json_shape": {
                "title": "string",
                "paragraphs": ["string"],
                "bullets": ["string"],
                "estimated_word_count": 250,
            },
        },
    }
    return dumps(payload, ensure_ascii=False, indent=2)


def build_json_repair_user_prompt(raw_text: str) -> str:
    payload = {
        "task": "Repair this malformed JSON into valid JSON only.",
        "raw_text": raw_text,
    }
    return dumps(payload, ensure_ascii=False, indent=2)


def build_writing_style_suggestions_prompt(titles: list[str]) -> str:
    payload = {
        "batch_article_titles": titles,
        "product_context": {
            "purpose": "The product generates one independent article for each title in a batch.",
            "example": "If titles are Hoa Mai and Hoa Dao, suggest styles for writing one article about Hoa Mai and another separate article about Hoa Dao. Do not suggest a combined article comparing Hoa Mai and Hoa Dao.",
        },
        "task": {
            "goal": "Suggest concise reusable Vietnamese writing styles for many independent articles that share the same topic pattern.",
            "requirements": [
                "Return JSON only.",
                "Return 8 to 12 options.",
                "Each suggestion must be short enough for a UI chip.",
                "Treat each title as a separate article, not as parts of one combined article.",
                "Do not connect, compare, or merge the provided titles into one topic.",
                "Do not mention any exact provided title in the suggestions.",
                "Make the options describe tone and method, for example: SEO giới thiệu từng chủ đề, chuyên gia dễ hiểu, storytelling nhẹ, cẩm nang thực tế.",
                "Make the options varied: SEO, expert, friendly, persuasive, storytelling, practical guide, and educational when relevant.",
                "Use natural Vietnamese.",
            ],
            "json_shape": {
                "suggestions": ["string"],
            },
        },
    }
    return dumps(payload, ensure_ascii=False, indent=2)


def build_section_outline_suggestions_prompt(titles: list[str], style: str, description: str) -> str:
    payload = {
        "batch_article_titles": titles,
        "style": style,
        "extra_description": description,
        "product_context": {
            "purpose": "The product generates one independent article per title using the same reusable section layout.",
            "critical_rule": "The layout must be a template for each single title. It must not create sections that compare, connect, or discuss multiple titles together.",
            "example": "For titles Hoa Mai and Hoa Dao, create sections like Nguon goc, Dac diem, Y nghia, Cach cham soc for each flower article. Do not create sections like Hoa Mai va Hoa Dao trong ngay Tet.",
        },
        "task": {
            "goal": "Suggest 3 alternative reusable section layouts for many independent Vietnamese articles in a batch.",
            "requirements": [
                "Return JSON only.",
                "Return exactly 3 layouts.",
                "Each layout must have 3 to 6 sections.",
                "Each section must include title, role, word_count, and description.",
                "Section titles must be generic and reusable for one article at a time.",
                "Every section should apply to the current article title only.",
                "Do not connect, compare, group, or merge the provided titles.",
                "Do not mention any exact provided title in layout names, summaries, section titles, roles, or descriptions.",
                "Use phrases like 'chủ đề này', 'đối tượng này', or 'tiêu đề hiện tại' when referring to the current article subject.",
                "Descriptions must be practical writing briefs, not generic labels.",
                "word_count must be between 120 and 700.",
                "Use natural Vietnamese.",
                "Make the 3 layouts meaningfully different: introductory profile, expert analysis, and practical guide/storytelling when relevant.",
            ],
            "json_shape": {
                "layouts": [
                    {
                        "name": "string",
                        "summary": "string",
                        "sections": [
                            {
                                "title": "string",
                                "role": "string",
                                "word_count": 250,
                                "description": "string",
                            }
                        ],
                    }
                ],
            },
        },
    }
    return dumps(payload, ensure_ascii=False, indent=2)


def build_prompts_from_json(client_data: PostCreate) -> list[PostResponse]:
    """Legacy compatibility for older services that still expect one prompt per title."""
    template_like_plan = TemplatePlan(
        html_pattern_notes=["Use one header, then one section per provided section title."],
        sections=[
            {
                "title": section.title,
                "role": section.role,
                "description": section.description,
                "target_word_count": section.word_count,
                "required_elements": [],
                "subsection_strategy": "Use h3 only when the section clearly benefits from it.",
            }
            for section in client_data.sections
        ],
    )
    return [
        PostResponse(
            title=title,
            content=build_article_user_prompt(title, client_data.style, template_like_plan),
        )
        for title in client_data.titles
    ]
