from __future__ import annotations

from json import dumps

from app.schemas.post_generation_schemas import PostCreate, Section, TemplatePlan
from app.schemas.repo_schemas import PostResponse

WORD_TOLERANCE_RATIO = 0.2


ARTICLE_SYSTEM_PROMPT = """Bạn là chuyên gia chiến lược nội dung SEO tiếng Việt và là người viết bài có cấu trúc rõ ràng.

Quy tắc chung:
- Nội dung cuối cùng phải là tiếng Việt tự nhiên 100%.
- Không xuất Markdown, code fence, XML, giải thích hoặc bình luận meta.
- Bám chính xác cấu trúc được yêu cầu.
- Giữ cùng một kiểu trình bày cho mọi bài trong cùng một batch.
- Ưu tiên nội dung cụ thể, hữu ích, không lặp ý.
- Tôn trọng thứ tự section, phạm vi từng section và mục tiêu số từ.
- Khi trả JSON, mọi giá trị chuỗi phải là JSON hợp lệ và escape dấu ngoặc kép đúng cách.
- Không viết HTML tag hoặc inline CSS trong các trường nội dung bài viết.
- Chỉ viết nội dung; ứng dụng sẽ tự render toàn bộ HTML và kiểu hiển thị.
"""


JSON_REPAIR_SYSTEM_PROMPT = """Bạn sửa output bị sai định dạng thành JSON hợp lệ.

Quy tắc:
- Chỉ trả JSON.
- Giữ nguyên ý nghĩa gốc nhiều nhất có thể.
- Không thêm giải thích.
- Escape dấu ngoặc kép đúng cách.
- Nếu payload có đoạn HTML, giữ chúng dưới dạng chuỗi và sửa cú pháp JSON cho hợp lệ.
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
            "goal": "Tạo một template plan dùng chung cho tất cả tiêu đề bài viết trong request này.",
            "requirements": [
                "Chỉ trả JSON.",
                "Giữ nguyên chính xác tiêu đề section và thứ tự section.",
                "Với mỗi section, xác định required_elements và subsection_strategy.",
                "Giữ plan độc lập với tiêu đề cụ thể để có thể dùng lại cho mọi tiêu đề trong batch.",
                "Giữ cùng một cấu trúc nội dung cho tất cả bài viết trong batch.",
                "Không tạo thêm section kết luận nếu section đó không có sẵn trong danh sách section được cung cấp.",
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
            "goal": "Viết payload cho một bài viết tiếng Việt hoàn chỉnh dưới dạng JSON nghiêm ngặt.",
            "requirements": [
                "Chỉ trả JSON.",
                "Dùng chính xác tiêu đề section và thứ tự section từ template_plan.sections.",
                "Không thêm hoặc xóa section.",
                "Không viết HTML, Markdown, heading, code fence hoặc inline styling.",
                "Mảng paragraphs của mỗi section chỉ được chứa các đoạn văn tiếng Việt thuần.",
                "Chỉ dùng bullets khi section thật sự cần danh sách ngắn; nếu không, trả mảng bullets rỗng.",
                "Mỗi section phải bám sát target_word_count và ước lượng số từ trung thực.",
                "Nếu trong nội dung có dấu ngoặc kép, phải escape đúng cách cho JSON.",
                "Không tạo field kết luận riêng hoặc section kết bài bổ sung nếu outline được cung cấp chưa có section đó.",
                "Không tạo block mở bài trước section 1.",
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
            "problem": "Số từ của section nằm ngoài khoảng cho phép hoặc nội dung bị lệch khỏi phạm vi yêu cầu.",
        },
        "task": {
            "goal": "Chỉ viết lại section này dưới dạng JSON nghiêm ngặt.",
            "requirements": [
                "Chỉ trả JSON.",
                "Không viết lại toàn bộ bài.",
                "Giữ nguyên chính xác tiêu đề section.",
                "Chỉ trả một object gồm title, paragraphs, bullets, estimated_word_count.",
                "Không viết HTML, Markdown, heading, code fence hoặc inline styling.",
                "Mảng paragraphs chỉ được chứa các đoạn văn tiếng Việt thuần.",
                "Chỉ dùng bullets khi hữu ích; nếu không, trả mảng bullets rỗng.",
                "Đưa section về lại trong khoảng số từ cho phép.",
                "Nếu trong nội dung có dấu ngoặc kép, phải escape đúng cách cho JSON.",
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
        "task": "Sửa JSON bị sai định dạng này thành JSON hợp lệ. Chỉ trả JSON.",
        "raw_text": raw_text,
    }
    return dumps(payload, ensure_ascii=False, indent=2)


def build_writing_style_suggestions_prompt(titles: list[str]) -> str:
    payload = {
        "batch_article_titles": titles,
        "product_context": {
            "purpose": "Sản phẩm tạo một bài viết độc lập cho mỗi tiêu đề trong batch.",
            "example": "Nếu tiêu đề là Hoa Mai và Hoa Đào, hãy gợi ý phong cách để viết một bài riêng về Hoa Mai và một bài riêng về Hoa Đào. Không gợi ý bài viết tổng hợp so sánh Hoa Mai và Hoa Đào.",
        },
        "task": {
            "goal": "Gợi ý các phong cách viết tiếng Việt ngắn gọn, có thể dùng lại cho nhiều bài độc lập cùng một dạng chủ đề.",
            "requirements": [
                "Chỉ trả JSON.",
                "Trả 8 đến 12 lựa chọn.",
                "Mỗi gợi ý phải đủ ngắn để hiển thị trong UI chip.",
                "Xem mỗi tiêu đề là một bài riêng, không phải các phần của một bài tổng hợp.",
                "Không liên kết, so sánh hoặc gộp các tiêu đề đã cung cấp thành một chủ đề.",
                "Không nhắc chính xác bất kỳ tiêu đề đã cung cấp nào trong gợi ý.",
                "Các lựa chọn nên mô tả giọng văn và phương pháp viết, ví dụ: SEO giới thiệu từng chủ đề, chuyên gia dễ hiểu, storytelling nhẹ, cẩm nang thực tế.",
                "Tạo lựa chọn đa dạng: SEO, chuyên gia, thân thiện, thuyết phục, storytelling, hướng dẫn thực tế và giáo dục nếu phù hợp.",
                "Dùng tiếng Việt tự nhiên.",
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
            "purpose": "Sản phẩm tạo một bài viết độc lập cho mỗi tiêu đề, dùng cùng một bố cục section có thể tái sử dụng.",
            "critical_rule": "Bố cục phải là template cho từng tiêu đề riêng lẻ. Không được tạo section so sánh, kết nối hoặc bàn về nhiều tiêu đề cùng lúc.",
            "example": "Với các tiêu đề Hoa Mai và Hoa Đào, hãy tạo các section như Nguồn gốc, Đặc điểm, Ý nghĩa, Cách chăm sóc cho từng bài về từng loài hoa. Không tạo section kiểu Hoa Mai và Hoa Đào trong ngày Tết.",
        },
        "task": {
            "goal": "Gợi ý 3 bố cục section khác nhau, có thể dùng lại cho nhiều bài tiếng Việt độc lập trong một batch.",
            "requirements": [
                "Chỉ trả JSON.",
                "Trả đúng 3 layout.",
                "Mỗi layout phải có 3 đến 6 section.",
                "Mỗi section phải có title, role, word_count và description.",
                "Tiêu đề section phải đủ tổng quát và có thể dùng lại cho từng bài riêng lẻ.",
                "Mỗi section chỉ nên áp dụng cho tiêu đề hiện tại của một bài.",
                "Không liên kết, so sánh, nhóm hoặc gộp các tiêu đề đã cung cấp.",
                "Không nhắc chính xác bất kỳ tiêu đề đã cung cấp nào trong tên layout, summary, title section, role hoặc description.",
                "Dùng các cụm như 'chủ đề này', 'đối tượng này' hoặc 'tiêu đề hiện tại' khi nói về chủ đề của bài hiện tại.",
                "Description phải là brief viết bài thực tế, không phải nhãn chung chung.",
                "word_count phải nằm trong khoảng 120 đến 700.",
                "Dùng tiếng Việt tự nhiên.",
                "Làm cho 3 layout khác nhau rõ rệt: hồ sơ giới thiệu, phân tích chuyên gia, và hướng dẫn thực tế/storytelling nếu phù hợp.",
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
    """Tương thích legacy cho các service cũ vẫn cần một prompt cho mỗi title."""
    template_like_plan = TemplatePlan(
        html_pattern_notes=["Dùng một header, sau đó mỗi tiêu đề section được cung cấp tương ứng với một section."],
        sections=[
            {
                "title": section.title,
                "role": section.role,
                "description": section.description,
                "target_word_count": section.word_count,
                "required_elements": [],
                "subsection_strategy": "Chỉ dùng h3 khi section thật sự cần chia nhỏ để rõ ý hơn.",
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
