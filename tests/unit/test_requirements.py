"""Test that required dependencies are available."""

import pytest


def test_httpx_importable():
    """Verify httpx can be imported."""
    import httpx

    assert hasattr(httpx, "AsyncClient")


def test_tenacity_importable():
    """Verify tenacity can be imported."""
    import tenacity

    assert hasattr(tenacity, "retry")


@pytest.mark.skipif(
    not pytest.importorskip("vcr", reason="vcrpy is optional"),
    reason="vcrpy not installed",
)
def test_vcrpy_importable():
    """Verify vcrpy can be imported for testing (optional dependency)."""
    import vcr

    assert hasattr(vcr, "VCR")
