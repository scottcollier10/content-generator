# services/content_generator.py
# Builds prompts with brand context and calls Claude to generate
# three distinct email variations per campaign.

import os
import json
import re
from typing import Optional

import anthropic

from models import BrandContext, EmailVariation
from utils import get_app_logger

logger = get_app_logger(__name__)

# Model to use for generation
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Banned phrases that make copy feel AI-generated
BANNED_PHRASES = [
    "delve", "landscape", "robust", "game-changer", "unlock", "leverage",
    "revolutionize", "cutting-edge", "next-level", "paradigm", "synergy",
    "elevate", "empower", "seamless", "holistic", "innovative",
]


def build_prompt(
    topic: str,
    audience: str,
    goal: str,
    brand_context: BrandContext,
) -> str:
    """Build the Claude prompt with injected brand context and anti-AI-writing rules."""
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

=== WRITING STYLE: SOUND HUMAN, NOT AI ===

Write like a real human marketer, not a language model. Follow these rules strictly:

1. NEVER use em dashes (—). Use regular hyphens (-), commas, or periods instead.
2. BANNED WORDS - never use: {', '.join(BANNED_PHRASES)}
3. Use contractions naturally: don't, we're, you'll, it's, won't, that's
4. Vary sentence length. Short sentences punch. Then follow with something longer that builds on the idea.
5. Be direct and conversational. Skip the corporate fluff.
6. Write like you're emailing a colleague, not drafting a press release.
===
"""

    return f"""You are an expert marketing copywriter who writes like a real person.

{brand_section}

Generate 3 distinct email variations for a campaign about: {topic}

Target Audience: {audience}
Campaign Goal: {goal}

For each variation, use a different strategic approach:

Variation 1: BENEFIT-FOCUSED
- Lead with the biggest customer benefit
- Use clear value propositions
- Include social proof or stats if relevant
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
    """Generates 3 brand-aware email variations using the Claude API."""

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
        """Call Claude and return a list of EmailVariation objects."""
        prompt = build_prompt(topic, audience, goal, brand_context)
        logger.info(f"Generating variations for topic: {topic}")

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4000,
            temperature=0.8,
            messages=[{"role": "user", "content": prompt}],
        )

        # Concatenate all text content blocks from the response
        response_text = "".join(
            block.text for block in response.content if block.type == "text"
        )

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
        """Parse Claude's response, stripping any markdown code fences."""
        # Strip ```json ... ``` fences if present
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
        if json_match:
            text = json_match.group(1)

        # Find outermost JSON object boundaries
        json_start = text.find("{")
        json_end = text.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            text = text[json_start:json_end]

        return json.loads(text)
