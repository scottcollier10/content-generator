# application/tests/test_content_generator.py
from unittest.mock import Mock, patch
from services.content_generator import ContentGenerator, build_prompt
from models import BrandContext


def test_build_prompt_includes_topic():
    """Prompt should include the campaign topic."""
    brand = BrandContext(voice_tone="Be friendly")
    prompt = build_prompt(
        topic="summer sale",
        audience="customers",
        goal="conversions",
        brand_context=brand,
    )
    assert "summer sale" in prompt
    assert "customers" in prompt
    assert "conversions" in prompt


def test_build_prompt_includes_brand_context():
    """Prompt should include brand voice and positioning."""
    brand = BrandContext(
        voice_tone="Be professional and concise",
        positioning="We are industry leaders",
    )
    prompt = build_prompt(
        topic="product launch",
        audience="prospects",
        goal="awareness",
        brand_context=brand,
    )
    assert "professional" in prompt
    assert "industry leaders" in prompt
