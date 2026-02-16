# application/tests/test_brand_context.py
from services.brand_context import categorize_file_content, BrandContextProvider
from models import BrandContext


def test_categorize_voice_file():
    """Files with 'voice' in name should go to voice_tone."""
    context = BrandContext()
    categorize_file_content("brand_voice.txt", "Be friendly and helpful.", context)
    assert "friendly" in context.voice_tone


def test_categorize_positioning_file():
    """Files with 'positioning' in name should go to positioning."""
    context = BrandContext()
    categorize_file_content("positioning.docx", "We are the leader.", context)
    assert "leader" in context.positioning


def test_brand_context_provider_interface():
    """BrandContextProvider should define get_brand_context method."""
    # BrandContextProvider is abstract, cannot be instantiated directly
    # Should raise TypeError when trying to instantiate
    try:
        provider = BrandContextProvider()
        assert False, "Should have raised TypeError for abstract class"
    except TypeError:
        pass

    # Verify get_brand_context is an abstract method
    from abc import ABC
    assert issubclass(BrandContextProvider, ABC)
    assert hasattr(BrandContextProvider, 'get_brand_context')
