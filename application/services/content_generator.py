# application/services/content_generator.py
import os
import json
from typing import Optional

import anthropic

from models import BrandContext, EmailVariation
from utils import get_app_logger

logger = get_app_logger(__name__)


def build_prompt(
    topic: str,
    audience: str,
    goal: str,
    brand_context: BrandContext,
) -> str:
    """Build the Claude prompt with brand context."""
    brand_section = f"""
=== BRAND CONTEXT ===

BRAND VOICE & TONE:
{brand_context.voice_tone}

POSITIONING & MESSAGING:
{brand_context.positioning}

TARGET AUDIENCE:
{brand_context.target_audience}

EXAMPLE COPY THAT MATCHES THIS BRAND:
{brand_context.example_copy}

=== CRITICAL ===
You MUST write in this exact brand voice. Match the tone, style, and positioning shown above.

===
"""

    return f"""You are an expert marketing copywriter.

{brand_section}

Generate 3 distinct email variations for a campaign about: {topic}

Target Audience: {audience}
Campaign Goal: {goal}

For each variation, use a different strategic approach:

Variation 1: BENEFIT-FOCUSED
- Lead with the biggest customer benefit
- Use clear value propositions
- Include social proof or stats
- Professional and direct tone

Variation 2: STORY-DRIVEN
- Start with a relatable problem or scenario
- Use narrative structure
- More conversational tone
- Connect emotionally

Variation 3: URGENCY-BASED
- Create FOMO (fear of missing out)
- Time-sensitive angle
- Action-oriented language
- Clear deadline or scarcity

For each email, provide:
1. Subject line (compelling, under 60 chars)
2. Preview text (first line, under 100 chars)
3. Email body (150-250 words, HTML formatted)
4. CTA button text (3-5 words)

Return ONLY valid JSON in this exact format:
{{
  "variations": [
    {{
      "approach": "benefit-focused",
      "subject": "...",
      "preview": "...",
      "body_html": "...",
      "cta_text": "..."
    }},
    {{
      "approach": "story-driven",
      "subject": "...",
      "preview": "...",
      "body_html": "...",
      "cta_text": "..."
    }},
    {{
      "approach": "urgency-based",
      "subject": "...",
      "preview": "...",
      "body_html": "...",
      "cta_text": "..."
    }}
  ]
}}

Use proper HTML in body_html: <p> for paragraphs, <strong> for emphasis, <ul><li> for lists. No markdown."""


class ContentGenerator:
    """Generates email variations using Claude API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate_variations(
        self,
        topic: str,
        audience: str,
        goal: str,
        brand_context: BrandContext,
    ) -> list[EmailVariation]:
        """Generate 3 email variations."""
        prompt = build_prompt(topic, audience, goal, brand_context)

        logger.info(f"Generating variations for topic: {topic}")

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            temperature=0.8,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract text content
        response_text = ""
        for block in response.content:
            if block.type == "text":
                response_text += block.text

        # Parse JSON from response
        parsed = self._parse_response(response_text)

        return [
            EmailVariation(
                approach=v["approach"],
                subject=v["subject"],
                preview=v["preview"],
                body_html=v["body_html"],
                cta_text=v["cta_text"],
            )
            for v in parsed["variations"]
        ]

    def _parse_response(self, text: str) -> dict:
        """Parse Claude's JSON response, handling markdown code blocks."""
        # Try to extract JSON from markdown code blocks
        import re
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
        if json_match:
            text = json_match.group(1)

        # Find JSON object boundaries
        json_start = text.find("{")
        json_end = text.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            text = text[json_start:json_end]

        return json.loads(text)
