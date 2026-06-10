from datetime import datetime
from typing import Literal, Optional
import unicodedata

from pydantic import BaseModel, Field, field_validator


class Section(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., min_length=1, max_length=500)
    word_count: int = Field(..., ge=50, le=5000)
    description: str = Field(..., min_length=1, max_length=2000)

    @field_validator("title", "role", "description", mode="before")
    @classmethod
    def normalize_text(cls, v):
        if isinstance(v, str):
            return unicodedata.normalize("NFC", v)
        return v


class PostCreate(BaseModel):
    titles: list[str]
    style: str
    sections: list[Section]
    ai_provider: Literal["groq", "vertex_gemini"] = "groq"
    ai_model: Optional[str] = None

    @field_validator("titles", mode="before")
    @classmethod
    def normalize_titles(cls, v):
        if isinstance(v, list):
            return [unicodedata.normalize("NFC", item) if isinstance(item, str) else item for item in v]
        return v

    @field_validator("style", mode="before")
    @classmethod
    def normalize_style(cls, v):
        if isinstance(v, str):
            return unicodedata.normalize("NFC", v)
        return v

    @field_validator("ai_model", mode="before")
    @classmethod
    def normalize_ai_model(cls, v):
        if isinstance(v, str):
            return unicodedata.normalize("NFC", v).strip() or None
        return v


class WritingStyleSuggestionRequest(BaseModel):
    titles: list[str] = Field(default_factory=list)

    @field_validator("titles", mode="before")
    @classmethod
    def normalize_titles(cls, v):
        if isinstance(v, list):
            return [unicodedata.normalize("NFC", item).strip() if isinstance(item, str) else item for item in v]
        return v


class WritingStyleSuggestionResponse(BaseModel):
    suggestions: list[str]


class SectionOutlineSuggestionRequest(BaseModel):
    titles: list[str] = Field(default_factory=list)
    style: str = ""
    description: str = ""

    @field_validator("titles", mode="before")
    @classmethod
    def normalize_titles(cls, v):
        if isinstance(v, list):
            return [unicodedata.normalize("NFC", item).strip() if isinstance(item, str) else item for item in v]
        return v

    @field_validator("style", "description", mode="before")
    @classmethod
    def normalize_text(cls, v):
        if isinstance(v, str):
            return unicodedata.normalize("NFC", v).strip()
        return v


class SectionOutlineOption(BaseModel):
    name: str
    summary: str
    sections: list[Section]


class SectionOutlineSuggestionResponse(BaseModel):
    layouts: list[SectionOutlineOption]


class SectionResponse(BaseModel):
    title: str
    role: str
    word_count: int
    description: str

    @field_validator("title", "role", "description", mode="before")
    @classmethod
    def normalize_text(cls, v):
        if isinstance(v, str):
            return unicodedata.normalize("NFC", v)
        return v


class PostHistoryResponse(BaseModel):
    id: int
    post_id: int
    title: str
    prompt: Optional[str]
    content: Optional[str]
    outline_json: Optional[list[SectionResponse]] = None
    input_tokens: int = 0
    output_tokens: int = 0
    credit_cost: float = 0
    status: str
    changed_at: datetime

    @field_validator("title", "prompt", "content", mode="before")
    @classmethod
    def normalize_text(cls, v):
        if isinstance(v, str):
            return unicodedata.normalize("NFC", v)
        return v

    class Config:
        from_attributes = True


class GenerationEstimateResponse(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    credit_cost: float
    credit_balance: float
    has_enough_credits: bool
    model: str


class TemplateSectionPlan(BaseModel):
    title: str
    role: str
    description: str
    target_word_count: int = Field(..., ge=50, le=5000)
    required_elements: list[str] = Field(default_factory=list)
    subsection_strategy: str


class TemplatePlan(BaseModel):
    html_pattern_notes: list[str] = Field(default_factory=list)
    sections: list[TemplateSectionPlan]


class GeneratedSection(BaseModel):
    title: str
    paragraphs: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)
    html: Optional[str] = None
    estimated_word_count: int = Field(..., ge=0)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_generated_text(cls, v):
        if isinstance(v, str):
            return unicodedata.normalize("NFC", v)
        return v

    @field_validator("paragraphs", "bullets", mode="before")
    @classmethod
    def normalize_text_list(cls, v):
        if isinstance(v, str):
            return [unicodedata.normalize("NFC", v)]
        if isinstance(v, list):
            return [unicodedata.normalize("NFC", item) if isinstance(item, str) else item for item in v]
        return v


class GeneratedArticlePayload(BaseModel):
    sections: list[GeneratedSection]
