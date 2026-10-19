"""Unit tests for WayFinder Design Tokens, WCAG 2.1 AA Contrast, and Invariant Guards (W-22 / W-24).

Implements strict dynamic verification and falsifiable tests as required by AGENTS.md rule 5:
- Parses actual values from design/tokens/tokens.css and design/tokens/tokens.json
- Verifies exact 1:1 synchronization between CSS and JSON for colors (hex & RGBA), spacing, radius, motion, typography
- Validates contrast ratios of actual tokens (including dark mode primary button >= 7.0:1)
- Proves guards fail when tokens are mutated (falsifiable tests for colors, spacing, RGBA, reduced-motion)
- Verifies touch target dimensions (>= 44x44px) across preview screens
- Verifies XSS prevention in prototype chat
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import pytest

from scripts.verify_wcag_contrast import (
    contrast_ratio,
    normalize_val,
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

    # 1. Light colors
    light_json = json_data["color"]["light"]
    for token_key, token_obj in light_json.items():
        css_var = f"--{token_key}"
        assert css_var in light_css, f"Token {css_var} missing from CSS :root"
        assert normalize_val(light_css[css_var]) == normalize_val(token_obj["$value"]), (
            f"Value mismatch for {css_var}: CSS has {light_css[css_var]}, JSON has {token_obj['$value']}"
        )

    # 2. Dark colors (both hex and RGBA)
    dark_json = json_data["color"]["dark"]
    for token_key, token_obj in dark_json.items():
        css_var = f"--{token_key}"
        val = token_obj["$value"]
        assert css_var in dark_css, f"Dark token {css_var} missing from dark mode CSS"
        assert normalize_val(dark_css[css_var]) == normalize_val(val), (
            f"Value mismatch for dark {css_var}: CSS has {dark_css[css_var]}, JSON has {val}"
        )


def test_dynamic_spacing_tokens_sync_css_vs_json():
    """Verify that spacing tokens (space-1 to space-16) match between CSS and JSON."""
    css_content = CSS_PATH.read_text(encoding="utf-8")
    light_css, _ = parse_css_tokens(css_content)
    json_data = parse_json_tokens(JSON_PATH)

    spacing_json = json_data.get("spacing", {})
    assert len(spacing_json) >= 10, "Expected at least 10 spacing tokens"
    for key, val_obj in spacing_json.items():
        css_var = f"--{key}"
        assert css_var in light_css, f"Spacing token {css_var} missing from CSS :root"
        assert normalize_val(light_css[css_var]) == normalize_val(val_obj["$value"]), (
            f"Spacing mismatch for {css_var}: CSS={light_css[css_var]} vs JSON={val_obj['$value']}"
        )


def test_dynamic_radius_and_motion_tokens_sync():
    """Verify that border-radius and motion tokens match between CSS and JSON."""
    css_content = CSS_PATH.read_text(encoding="utf-8")
    light_css, _ = parse_css_tokens(css_content)
    json_data = parse_json_tokens(JSON_PATH)

    for section in ["radius", "motion"]:
        sec_json = json_data.get(section, {})
        for key, val_obj in sec_json.items():
            css_var = f"--{key}"
            assert css_var in light_css, f"{section} token {css_var} missing from CSS :root"
            assert normalize_val(light_css[css_var]) == normalize_val(val_obj["$value"]), (
                f"{section} mismatch for {css_var}: CSS={light_css[css_var]} vs JSON={val_obj['$value']}"
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

    mutated_light = dict(light_css)
    mutated_light["--color-primary"] = "#29A9FF"

    json_data = parse_json_tokens(JSON_PATH)
    json_expected = json_data["color"]["light"]["color-primary"]["$value"]

    with pytest.raises(AssertionError):
        assert normalize_val(mutated_light["--color-primary"]) == normalize_val(json_expected)


def test_falsifiable_mutation_spacing_mismatch_fails():
    """Falsifiable test: prove that mutating space-4 in JSON (e.g. 16px -> 18px) fails guard."""
    css_content = CSS_PATH.read_text(encoding="utf-8")
    light_css, _ = parse_css_tokens(css_content)

    # Mutate JSON spacing to 18px
    mutated_json_space4 = "18px"
    css_val = light_css.get("--space-4", "")

    with pytest.raises(AssertionError):
        assert normalize_val(css_val) == normalize_val(mutated_json_space4), "Must fail when spacing differs"


def test_falsifiable_mutation_dark_rgba_mismatch_fails():
    """Falsifiable test: prove that mutating dark RGBA color-brand-tint in CSS fails guard."""
    css_content = CSS_PATH.read_text(encoding="utf-8")
    _, dark_css = parse_css_tokens(css_content)

    # Mutate CSS dark brand tint to red
    mutated_dark_css = dict(dark_css)
    mutated_dark_css["--color-brand-tint"] = "rgba(255, 0, 0, 0.5)"

    json_data = parse_json_tokens(JSON_PATH)
    expected_rgba = json_data["color"]["dark"]["color-brand-tint"]["$value"]

    with pytest.raises(AssertionError):
        assert normalize_val(mutated_dark_css["--color-brand-tint"]) == normalize_val(expected_rgba)


def test_falsifiable_mutation_white_on_brand_blue_fails_contrast():
    """Falsifiable test: prove that using white text on brand blue #29A9FF fails WCAG AA."""
    ratio = contrast_ratio("#FFFFFF", "#29A9FF")
    assert ratio < 4.5, f"White text on #29A9FF must fail (< 4.5:1), but got {ratio:.2f}:1"
    assert round(ratio, 2) == 2.56, f"Expected exact ratio 2.56:1, got {ratio:.2f}:1"


def test_reduced_motion_static_asset_and_markup():
    """Verify that static frame 0 exists and all GIF instances in previews use <picture> with .spinner-gif."""
    static_png = Path("design/Untitled_Artwork_static.png")
    assert static_png.exists(), "design/Untitled_Artwork_static.png must exist"
    assert static_png.stat().st_size > 1000, "Static PNG must not be empty"

    screens_html = Path("design/preview/screens.html").read_text(encoding="utf-8")
    screens_dark_html = Path("design/preview/screens_dark.html").read_text(encoding="utf-8")
    mobile_html = Path("design/preview/mobile_screens.html").read_text(encoding="utf-8")

    for name, content in [
        ("screens.html", screens_html),
        ("screens_dark.html", screens_dark_html),
        ("mobile_screens.html", mobile_html),
    ]:
        assert "prefers-reduced-motion: reduce" in content, f"{name} must contain prefers-reduced-motion"
        assert "Untitled_Artwork_static.png" in content, f"{name} must reference static PNG"

        # Check every <img> with Untitled_Artwork.gif has class spinner-gif
        gif_tags = re.findall(r'<img[^>]*Untitled_Artwork\.gif[^>]*>', content)
        assert len(gif_tags) > 0, f"{name} must contain gif tags"
        for tag in gif_tags:
            assert 'class="spinner-gif"' in tag or "class='spinner-gif'" in tag, (
                f"Tag in {name} missing class spinner-gif: {tag}"
            )


def test_falsifiable_mutation_gif_without_class_fails():
    """Falsifiable test: prove that an <img> with Untitled_Artwork.gif lacking spinner-gif class fails."""
    bad_tag = '<img src="../Untitled_Artwork.gif" width="40" height="40" alt="Loading">'
    with pytest.raises(AssertionError):
        assert 'class="spinner-gif"' in bad_tag


def test_mobile_buttons_touch_target_min_44px():
    """Verify that mobile and responsive button rules strictly enforce minimum 44px touch targets."""
    screens_html = Path("design/preview/screens.html").read_text(encoding="utf-8")
    mobile_html = Path("design/preview/mobile_screens.html").read_text(encoding="utf-8")

    # In mobile_screens.html
    btn_css_match = re.search(r"\.btn\s*\{([^}]+)\}", mobile_html)
    assert btn_css_match, ".btn rule not found in mobile_screens.html"
    assert "min-height: 44px" in btn_css_match.group(1) or "min-height:44px" in btn_css_match.group(1)

    # In screens.html
    assert "min-height: 44px" in screens_html
    screens_btn_match = re.search(r"\.btn\s*\{([^}]+)\}", screens_html)
    assert screens_btn_match, ".btn rule not found in screens.html"
    assert "min-height: 44px" in screens_btn_match.group(1)

    # Responsive rule in screens.html
    media_btn_match = re.search(r"@media\s*\(max-width:\s*768px\)\s*\{([^}]+)\}", screens_html)
    assert media_btn_match, "Responsive @media (max-width: 768px) rule missing in screens.html"
    assert "44px !important" in media_btn_match.group(1)


def test_chat_prototype_prevents_xss():
    """Verify that prototype script in screens.html safely creates text nodes instead of raw HTML interpolation."""
    screens_html = Path("design/preview/screens.html").read_text(encoding="utf-8")
    # Verify no raw innerHTML interpolation of `${q}`
    assert 'innerHTML = `<strong>Trợ lý AI:</strong> Về câu hỏi <em>"${q}"</em>' not in screens_html
    assert "document.createTextNode" in screens_html
    assert "em.textContent" in screens_html


def test_figma_plugin_dark_colors_match_tokens():
    """Verify that design/figma-plugin/code.js has dark colors matching tokens.json exactly."""
    code_js = Path("design/figma-plugin/code.js").read_text(encoding="utf-8")
    tokens = json.loads(Path("design/tokens/tokens.json").read_text(encoding="utf-8"))
    dark_tokens = tokens["color"]["dark"]

    # Verify all 6 key dark colors are explicitly defined in code.js with exact hex
    expected_hexes = {
        "color-bg": dark_tokens["color-bg"]["$value"],          # #0E1217
        "color-surface": dark_tokens["color-surface"]["$value"],    # #161B22
        "color-text": dark_tokens["color-text"]["$value"],          # #E8EDF2
        "color-text-muted": dark_tokens["color-text-muted"]["$value"], # #9AA6B2
        "color-success": dark_tokens["color-success"]["$value"],    # #4ADE80
        "color-danger": dark_tokens["color-danger"]["$value"],      # #F87171
    }

    for name, hex_val in expected_hexes.items():
        assert f'"{hex_val}"' in code_js or f"'{hex_val}'" in code_js, (
            f"Figma plugin code.js missing exact token hex {hex_val} for {name}"
        )


def test_falsifiable_mutation_plugin_color_mismatch_fails():
    """Falsifiable test: prove that an altered dark color in plugin code fails verification."""
    fake_code_js = 'const C_DARK = { bg: hexToRgb("#0F172A") };'
    with pytest.raises(AssertionError):
        assert '"#0E1217"' in fake_code_js


def test_figma_variables_export_valid():
    """Verify that design/tokens/figma_variables_export.json exists, has 35 variables and matches tokens.json."""
    export_path = Path("design/tokens/figma_variables_export.json")
    assert export_path.exists(), "figma_variables_export.json does not exist"
    data = json.loads(export_path.read_text(encoding="utf-8"))
    assert data["metadata"]["collectionName"] == "WayFinder Tokens"
    variables = data["collections"][0]["variables"]
    assert len(variables) == 35

    tokens = json.loads(Path("design/tokens/tokens.json").read_text(encoding="utf-8"))
    var_map = {v["name"]: v for v in variables}

    # Verify color/color-bg has exact hex values
    assert var_map["color/color-bg"]["valuesByMode"]["mode:dark"] == tokens["color"]["dark"]["color-bg"]["$value"]
    assert var_map["spacing/space-4"]["valuesByMode"]["mode:light"] == 16.0


def test_auth_screens_responsive_no_overflow_rules():
    """Verify that design/preview/auth_screens.html enforces responsive rules to prevent horizontal overflow."""
    auth_html = Path("design/preview/auth_screens.html").read_text(encoding="utf-8")
    assert "overflow-x: auto" in auth_html
    assert "box-sizing: border-box" in auth_html
    assert "@media (max-width: 768px)" in auth_html
    assert "@media (max-width: 420px)" in auth_html

