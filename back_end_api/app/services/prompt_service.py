from app.schemas.post_schemas import PostCreate
from app.schemas.repo_schemas import PostResponse


def build_prompts_from_json(client_data: PostCreate) -> list[PostResponse]:
    style = client_data.style.strip()
    results: list[PostResponse] = []

    for article_title in client_data.titles:
        prompt = f"""You are a senior Vietnamese SEO content strategist, editor, and HTML article writer.

Your task is to write ONE complete article in VIETNAMESE for this title:
"{article_title}"

Overall writing style:
"{style}"

IMPORTANT LANGUAGE RULE:
- Write the INSTRUCTIONS mentally in English, but the FINAL ARTICLE CONTENT must be 100% in natural Vietnamese.
- Do not output English explanations, notes, JSON, Markdown, or code fences.

OUTPUT FORMAT REQUIREMENTS:
- Return only valid HTML.
- The output must start with <article> and end with </article>.
- Do not include ```html, Markdown, JSON, XML, or any explanation outside the HTML.

APPROVED HTML TAGS:
- Structural tags: <article>, <header>, <section>, <nav>, <footer>
- Heading tags: <h1>, <h2>, <h3>
- Text tags: <p>, <strong>, <em>, <span>
- List tags: <ul>, <ol>, <li>
- Supporting tags: <blockquote>

HTML STRUCTURE RULES:
1. Use exactly one <h1> for the article title.
2. Add a short introduction below the <h1>.
3. Each main section must use one <section> with an <h2>.
4. If a section naturally needs sub-points, use <h3> for subsections.
5. Do not skip heading levels. Use h1 -> h2 -> h3 only.
6. Do not create meaningless subsections. Only add <h3> when the content clearly benefits from it.
7. Keep the article readable, well spaced, and logically segmented.

CSS / PRESENTATION RULES:
- Use clean semantic HTML first.
- Avoid heavy inline CSS.
- Inline CSS is allowed only in small amounts for readability, for example on the root <article> or for simple spacing containers.
- If inline CSS is used, keep it minimal, modern, and production-safe.
- Do not use JavaScript, external CSS, <style>, <script>, <table>, or form elements.

SEO REQUIREMENTS:
- The article must be SEO-friendly and useful for real readers.
- Naturally include the main topic from the title in the introduction, some headings, and body text.
- Write a compelling introduction that clarifies search intent.
- Use clear, descriptive section headings.
- Include scannable content such as bullet lists or numbered lists where useful.
- End with a concise conclusion or action-oriented closing section.
- Do not keyword stuff.

CONTENT QUALITY REQUIREMENTS:
- The article must feel like a polished editorial piece, not AI filler.
- Be specific, useful, and logically structured.
- Avoid repetition, generic empty claims, and placeholder text.
- Do not mention that you are an AI or that this content was generated.
- Match the requested tone consistently across the whole article.

SECTION EXECUTION RULES:
- Follow the exact section order provided below.
- If a section naturally needs subsections, create a small number of h3 blocks.
- Keep the structure neat and render-ready for a modern web interface.

ARTICLE BLUEPRINT:
"""
        for index, section in enumerate(client_data.sections, start=1):
            prompt += (
                f"\nSection {index}:\n"
                f"- Section title: {section.title}\n"
                f"- Content brief: {section.desc}\n"
            )

        prompt += """

FINAL EXECUTION CHECKLIST:
- Output only HTML.
- Write the article in Vietnamese.
- Use one <h1>, multiple <h2>, and only use <h3> when needed.
- Make the article SEO-friendly, readable, and high quality.
- Keep structure aligned with the provided sections.
- Ensure the result is ready to render directly on a modern web interface.
"""

        results.append(PostResponse(title=article_title, content=prompt))

    return results
