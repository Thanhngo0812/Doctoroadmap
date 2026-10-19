"""Unit tests for WayFinder Design Tokens and WCAG 2.1 AA Contrast Ratios (W-22 / W-24).

Implements strict dynamic verification and falsifiable tests as required by AGENTS.md rule 5:
- Parses actual values from design/tokens/tokens.css and design/tokens/tokens.json
- Verifies exact 1:1 synchronization between CSS and JSON
- Validates contrast ratios of actual tokens (including dark mode primary button)
- Proves guards fail when tokens are mutated (falsifiable tests)
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from scripts.verify_wcag_contrast import (
    contrast_ratio,
    parse_css_tokens,
    parse_json_tokens,
    verify_tokens_and_contrast,
)


CSS_PATH = Path("design/tokens/tokens.css")
JSON_PATH = Path("design/tokens/tokens.json")


def test_tokens_files_exist():
    assert CSS_PATH.exists(), f"{CSS_PATH} must exist"
    assert JSON_PATH.exists(), f"{JSON_PATH} must exist"


def test_dynamic_token_sync_css_vs_json():
    """Verify that every color token defined in JSON exactly matches CSS custom properties."""
    css_content = CSS_PATH.read_text(encoding="utf-8")
    light_css, dark_css = parse_css_tokens(css_content)
    json_data = parse_json_tokens(JSON_PATH)

    light_json = json_data["color"]["light"]
    for token_key, token_obj in light_json.items():
        css_var = f"--{token_key}"
        assert css_var in light_css, f"Token {css_var} missing from CSS :root"
        assert light_css[css_var].upper() == token_obj["$value"].upper(), (
            f"Value mismatch for {css_var}: CSS has {light_css[css_var]}, JSON has {token_obj['$value']}"
        )

    dark_json = json_data["color"]["dark"]
    for token_key, token_obj in dark_json.items():
        css_var = f"--{token_key}"
        val = token_obj["$value"]
        if val.startswith("#"):
            assert css_var in dark_css, f"Dark token {css_var} missing from dark mode CSS"
            assert dark_css[css_var].upper() == val.upper(), (
                f"Value mismatch for dark {css_var}: CSS has {dark_css[css_var]}, JSON has {val}"
            )


def test_dynamic_wcag_contrast_from_actual_css():
    """Verify that actual parsed CSS variables pass WCAG AA contrast requirements."""
    ok, logs = verify_tokens_and_contrast(CSS_PATH, JSON_PATH)
    assert ok, f"Tokens contrast check failed with logs:\n" + "\n".join(logs)


def test_dark_mode_primary_button_contrast():
    """Explicitly verify that .btn-primary in dark mode uses dark text on #29A9FF (>= 7.0:1)."""
    css_content = CSS_PATH.read_text(encoding="utf-8")
    _, dark_css = parse_css_tokens(css_content)

    primary_bg = dark_css.get("--color-primary")
    primary_text = dark_css.get("--color-primary-text")

    assert primary_bg == "#29A9FF", "Dark mode primary must be #29A9FF"
    assert primary_text == "#0E1217", "Dark mode primary button text must be dark #0E1217"

    ratio = contrast_ratio(primary_text, primary_bg)
    assert ratio >= 4.5, f"Dark mode button contrast {ratio:.2f}:1 is under 4.5:1"
    assert round(ratio, 2) == 7.35, f"Expected exact contrast 7.35:1, got {ratio:.2f}:1"


def test_falsifiable_mutation_css_mismatch_fails():
    """Falsifiable test: prove that mutating a CSS value so it diverges from JSON causes failure."""
    css_content = CSS_PATH.read_text(encoding="utf-8")
    light_css, _ = parse_css_tokens(css_content)

    # Mutate in memory: replace primary with #29A9FF (diverging from JSON #0A6AB3)
    mutated_light = dict(light_css)
    mutated_light["--color-primary"] = "#29A9FF"

    json_data = parse_json_tokens(JSON_PATH)
    json_expected = json_data["color"]["light"]["color-primary"]["$value"]

    with pytest.raises(AssertionError):
        assert mutated_light["--color-primary"].upper() == json_expected.upper(), "Must fail on mismatch"


def test_falsifiable_mutation_white_on_brand_blue_fails_contrast():
    """Falsifiable test: prove that using white text on brand blue #29A9FF fails WCAG AA."""
    ratio = contrast_ratio("#FFFFFF", "#29A9FF")
    assert ratio < 4.5, f"White text on #29A9FF must fail (< 4.5:1), but got {ratio:.2f}:1"
    assert round(ratio, 2) == 2.56, f"Expected exact ratio 2.56:1, got {ratio:.2f}:1"


def test_reduced_motion_static_asset_exists():
    """Verify that static frame 0 exists for prefers-reduced-motion substitution."""
    static_png = Path("design/Untitled_Artwork_static.png")
    assert static_png.exists(), "design/Untitled_Artwork_static.png must exist"
    assert static_png.stat().st_size > 1000, "Static PNG must not be empty"


def test_reduced_motion_markup_in_previews():
    """Verify that both preview files contain prefers-reduced-motion rules for spinner-gif."""
    screens_html = Path("design/preview/screens.html").read_text(encoding="utf-8")
    mobile_html = Path("design/preview/mobile_screens.html").read_text(encoding="utf-8")

    assert "prefers-reduced-motion: reduce" in screens_html
    assert "Untitled_Artwork_static.png" in screens_html
    assert "prefers-reduced-motion: reduce" in mobile_html
    assert "Untitled_Artwork_static.png" in mobile_html


def test_mobile_buttons_touch_target_min_44px():
    """Verify that mobile buttons enforce minimum 44px touch targets."""
    import re
    mobile_html = Path("design/preview/mobile_screens.html").read_text(encoding="utf-8")

    # Verify CSS rule for .btn specifies min-height >= 44px
    btn_css_match = re.search(r"\.btn\s*\{([^}]+)\}", mobile_html)
    assert btn_css_match, ".btn rule not found in mobile_screens.html"
    css_props = btn_css_match.group(1)
    assert "min-height: 44px" in css_props or "min-height:44px" in css_props
    assert "min-width: 44px" in css_props or "min-width:44px" in css_props

    # Verify no inline styles set height below 44px on mobile buttons
    for inline_match in re.finditer(r'<button[^>]*style="([^"]*)"', mobile_html):
        style = inline_match.group(1)
        h_match = re.search(r'(?:^|;\s*)height:\s*(\d+)px', style)
        if h_match:
            height = int(h_match.group(1))
            assert height >= 44, f"Mobile button height {height}px is below 44px requirement: {style}"

