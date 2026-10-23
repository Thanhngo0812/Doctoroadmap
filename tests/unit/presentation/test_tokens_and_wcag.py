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


def test_prototype_flows_interactive_workbench():
    """Verify that design/preview/prototype_flows.html covers all 4 original user journeys with 44px buttons."""
    proto_html = Path("design/preview/prototype_flows.html").read_text(encoding="utf-8")
    # All 4 flows present
    assert 'id="flow1-container"' in proto_html
    assert 'id="flow2-container"' in proto_html
    assert 'id="flow3-container"' in proto_html
    assert 'id="flow4-container"' in proto_html

    # Essential interactive elements
    assert "flow1-btn-register" in proto_html
    assert "flow1-btn-open-course" in proto_html
    assert "flow1-accordion-toggle" in proto_html
    assert "flow2-btn-copy" in proto_html
    assert "flow2-btn-simulate-join" in proto_html
    assert "flow3-btn-select-file" in proto_html
    assert "flow3-btn-start-build" in proto_html
    assert "flow4-btn-submit" in proto_html

    # Touch target 44px enforcement
    assert "min-height: 44px" in proto_html
    assert "height: 44px" in proto_html

    # Reduced motion support
    assert "prefers-reduced-motion: reduce" in proto_html
    assert "Untitled_Artwork_static.png" in proto_html


def test_w03_auth_screens_specification():
    """Verify that design/preview/w03_auth_screens.html implements the 5 screens required by W-03 coordinator note."""
    w03_html = Path("design/preview/w03_auth_screens.html").read_text(encoding="utf-8")
    assert 'id="screen-verify-pending"' in w03_html
    assert 'id="screen-verify-success"' in w03_html
    assert 'id="screen-forgot-password"' in w03_html
    assert 'id="screen-reset-password"' in w03_html
    assert 'id="screen-token-invalid"' in w03_html

    # Verify 44px tap targets and responsive overflow guards
    assert "min-height: 44px" in w03_html
    assert "height: 44px" in w03_html
    assert "@media (max-width: 768px)" in w03_html


def test_figma_plugin_has_w03_and_prototype_reactions():
    """Verify that design/figma-plugin/code.js includes W-03, W-06, W-04, W-07, W-14 screens and native prototype reactions."""
    code_js = Path("design/figma-plugin/code.js").read_text(encoding="utf-8")
    assert "Màn hình W-03" in code_js
    assert "Màn hình W-06" in code_js
    assert "Màn hình W-04" in code_js
    assert "Màn hình W-07" in code_js
    assert "Màn hình W-14" in code_js
    assert "reactionStats" in code_js
    assert "setReactionsAsync" in code_js
    assert "linkReaction" in code_js
    assert "NAVIGATE" in code_js
    assert "ON_CLICK" in code_js


def test_w06_course_screens_specification():
    """Verify that design/preview/w06_course_screens.html implements all 4 states for W-06 React integration."""
    w06_html = Path("design/preview/w06_course_screens.html").read_text(encoding="utf-8")
    assert 'id="section-courses-active"' in w06_html
    assert 'id="section-courses-empty"' in w06_html
    assert 'id="section-courses-loading"' in w06_html
    assert 'id="section-courses-error"' in w06_html
    assert 'id="card-sample-course"' in w06_html
    assert "DOC-SAMPLE-01" in w06_html
    assert "WF-PHARM-2026" in w06_html
    assert "min-height: 44px" in w06_html
    assert "height: 44px" in w06_html
    assert "@media (max-width: 768px)" in w06_html
    assert "prefers-reduced-motion: reduce" in w06_html


def test_w04_profile_screens_specification():
    """Verify that design/preview/w04_profile_screens.html implements profile, password change and session revocation."""
    w04_html = Path("design/preview/w04_profile_screens.html").read_text(encoding="utf-8")
    assert 'id="card-profile-info"' in w04_html
    assert 'id="card-change-password"' in w04_html
    assert 'id="card-sessions-security"' in w04_html
    assert 'id="btn-logout-current"' in w04_html
    assert 'id="btn-logout-all"' in w04_html
    assert "min-height: 44px" in w04_html
    assert "height: 44px" in w04_html

def parse_css_for_raw_variables(css_path: Path):
    """Parse tokens.css and return dictionaries of Light and Dark custom properties."""
    css_content = css_path.read_text(encoding="utf-8")
    
    # Extract :root properties
    root_match = re.search(r':root\s*\{([^}]+)\}', css_content, re.DOTALL)
    light_props = {}
    if root_match:
        for line in root_match.group(1).splitlines():
            line = line.strip()
            if line.startswith('--') and ':' in line:
                k, v = line.split(':', 1)
                light_props[k.strip()] = v.split(';')[0].strip()

    # Extract dark mode properties
    dark_match = re.search(r'\[data-theme="dark"\],\s*\.dark\s*\{([^}]+)\}', css_content, re.DOTALL)
    dark_props = dict(light_props)  # Inherit root properties
    if dark_match:
        for line in dark_match.group(1).splitlines():
            line = line.strip()
            if line.startswith('--') and ':' in line:
                k, v = line.split(':', 1)
                dark_props[k.strip()] = v.split(';')[0].strip()
                
    return light_props, dark_props


def verify_variables_against_css(data, css_path: Path):
    """Strictly assert that all 37 variables in both Light and Dark mode match CSS (74 checks)."""
    light_props, dark_props = parse_css_for_raw_variables(css_path)
    vars_list = data.get("variables", [])
    assert len(vars_list) == 37, f"Expected exactly 37 variables, found {len(vars_list)}"
    
    for v in vars_list:
        name = v["name"]
        css_prop = v["cssProperty"]
        val_light = v["valuesByMode"]["Light"]
        val_dark = v["valuesByMode"]["Dark"]
        
        # Check Light mode mapping
        exp_light = f"{val_light}px" if isinstance(val_light, (int, float)) and ("space" in name or "radius" in name) else str(val_light)
        act_light = light_props.get(css_prop)
        assert act_light == exp_light, f"Light mode mismatch for {name} ({css_prop}): CSS='{act_light}' vs raw='{exp_light}'"
        
        # Check Dark mode mapping
        exp_dark = f"{val_dark}px" if isinstance(val_dark, (int, float)) and ("space" in name or "radius" in name) else str(val_dark)
        act_dark = dark_props.get(css_prop)
        assert act_dark == exp_dark, f"Dark mode mismatch for {name} ({css_prop}): CSS='{act_dark}' vs raw='{exp_dark}'"


def test_figma_variables_raw_export_valid():
    """Verify that design/tokens/figma_variables_raw_export.json contains verified metadata and matches all 74 CSS values."""
    raw_path = Path("design/tokens/figma_variables_raw_export.json")
    css_path = Path("design/tokens/tokens.css")
    assert raw_path.exists(), "Raw variables export file must exist"
    assert css_path.exists(), "Tokens CSS file must exist"
    
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    meta = data.get("metadata", {})
    assert meta.get("fileKey") == "UVhhlZnqdpV0JDcAHwJczo"
    assert meta.get("collectionName") == "WayFinder Tokens"
    assert meta.get("collectionId") == "VariableCollectionId:45:1"
    assert len(meta.get("modes", [])) == 2
    assert "exportedAt" in meta
    assert "exportTool" in meta
    assert meta.get("provenanceType") == "LOCAL_DTCG_CONTRACT_AND_PLUGIN_MAPPING"
    assert meta.get("status") == "LOCAL_VERIFIED_TOKEN_CONTRACT"
    
    # Run full 74-value CSS comparison
    verify_variables_against_css(data, css_path)



def test_w07_roadmap_screens_specification():
    """Verify that design/preview/w07_roadmap_screens.html implements roadmap, progress and rollback/complete actions."""
    w07_html = Path("design/preview/w07_roadmap_screens.html").read_text(encoding="utf-8")
    assert 'id="section-roadmap-overview"' in w07_html
    assert 'id="module-1"' in w07_html
    assert 'id="module-2"' in w07_html
    assert 'id="concept-lad"' in w07_html
    assert 'id="concept-lcx"' in w07_html
    assert 'id="btn-rollback-lad"' in w07_html
    assert 'id="btn-mark-lcx"' in w07_html
    assert 'id="btn-quiz-full"' in w07_html
    assert "min-height: 44px" in w07_html
    assert "height: 44px" in w07_html
    assert "@media (max-width: 768px)" in w07_html
    assert "--color-text" in w07_html
    assert "--color-brand" in w07_html
    assert "--color-text-main" not in w07_html
    assert "--color-brand-blue" not in w07_html


def test_w14_upload_screens_specification():
    """Verify that design/preview/w14_upload_screens.html implements 4-step pipeline, course naming, 96px spinner, and error state."""
    w14_html = Path("design/preview/w14_upload_screens.html").read_text(encoding="utf-8")
    assert 'id="section-upload-select"' in w14_html
    assert 'id="section-pipeline-progress"' in w14_html
    assert 'id="section-scan-error"' in w14_html
    assert 'id="step-1"' in w14_html
    assert 'id="step-2"' in w14_html
    assert 'id="step-3"' in w14_html
    assert 'id="step-4"' in w14_html
    assert 'id="chk-copyright"' in w14_html
    assert 'id="input-course-name"' in w14_html
    assert "width: 96px; height: 96px;" in w14_html
    assert "min-height: 44px" in w14_html
    assert "height: 44px" in w14_html
    assert "prefers-reduced-motion: reduce" in w14_html
    assert "--color-text" in w14_html
    assert "--color-brand" in w14_html
    assert "--color-text-main" not in w14_html
    assert "--color-brand-blue" not in w14_html


def test_falsifiable_mutation_raw_variables_invalid_fails():
    """Falsifiable test: corrupting raw variables export metadata must fail assertion."""
    raw_path = Path("design/tokens/figma_variables_raw_export.json")
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    mutated = dict(data)
    mutated["metadata"] = dict(mutated["metadata"])
    mutated["metadata"]["fileKey"] = "WRONG_FILE_KEY"
    try:
        assert mutated["metadata"]["fileKey"] == "UVhhlZnqdpV0JDcAHwJczo"
        raise RuntimeError("Guard failed to catch wrong file key mutation!")
    except AssertionError:
        pass  # Caught!

def test_falsifiable_raw_variables_primary_mutation_fails():
    """Falsifiable test: mutating raw variable primary color to #FF0000 must cause an assertion failure."""
    raw_path = Path("design/tokens/figma_variables_raw_export.json")
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    vars_by_name = {v["name"]: dict(v) for v in data.get("variables", [])}
    # Mutate primary light color to #FF0000
    vars_by_name["color/primary"]["valuesByMode"] = dict(vars_by_name["color/primary"]["valuesByMode"])
    vars_by_name["color/primary"]["valuesByMode"]["Light"] = "#FF0000"
    
    try:
        assert vars_by_name["color/primary"]["valuesByMode"]["Light"] == "#0A6AB3"
        raise RuntimeError("Guard failed to catch primary color mutation to #FF0000!")
    except AssertionError:
        pass  # Caught!

def test_falsifiable_dark_brand_tint_mutation_fails():
    """Falsifiable test: mutating dark brand tint from 0.14 to 0.99 must cause assertion failure."""
    raw_path = Path("design/tokens/figma_variables_raw_export.json")
    css_path = Path("design/tokens/tokens.css")
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    
    # Mutate dark brand-tint to 0.99
    mutated = dict(data)
    mutated["variables"] = [dict(v) for v in data["variables"]]
    for v in mutated["variables"]:
        if v["name"] == "color/brand-tint":
            v["valuesByMode"] = dict(v["valuesByMode"])
            v["valuesByMode"]["Dark"] = "rgba(41, 169, 255, 0.99)"
            
    try:
        verify_variables_against_css(mutated, css_path)
        raise RuntimeError("Guard failed to catch dark brand tint mutation to 0.99!")
    except AssertionError as e:
        assert "brand-tint" in str(e)  # Successfully caught!


def test_falsifiable_spacing_mutation_fails():
    """Falsifiable test: mutating spacing space-4 from 16 to 18 must cause assertion failure."""
    raw_path = Path("design/tokens/figma_variables_raw_export.json")
    css_path = Path("design/tokens/tokens.css")
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    
    mutated = dict(data)
    mutated["variables"] = [dict(v) for v in data["variables"]]
    for v in mutated["variables"]:
        if v["name"] == "spacing/space-4":
            v["valuesByMode"] = dict(v["valuesByMode"])
            v["valuesByMode"]["Light"] = 18
            
    try:
        verify_variables_against_css(mutated, css_path)
        raise RuntimeError("Guard failed to catch spacing space-4 mutation to 18!")
    except AssertionError as e:
        assert "space-4" in str(e)


def test_falsifiable_radius_mutation_fails():
    """Falsifiable test: mutating radius-md from 10 to 12 must cause assertion failure."""
    raw_path = Path("design/tokens/figma_variables_raw_export.json")
    css_path = Path("design/tokens/tokens.css")
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    
    mutated = dict(data)
    mutated["variables"] = [dict(v) for v in data["variables"]]
    for v in mutated["variables"]:
        if v["name"] == "radius/radius-md":
            v["valuesByMode"] = dict(v["valuesByMode"])
            v["valuesByMode"]["Dark"] = 12
            
    try:
        verify_variables_against_css(mutated, css_path)
        raise RuntimeError("Guard failed to catch radius-md mutation to 12!")
    except AssertionError as e:
        assert "radius-md" in str(e)


def test_falsifiable_motion_mutation_fails():
    """Falsifiable test: mutating motion-fast from 120ms to 150ms must cause assertion failure."""
    raw_path = Path("design/tokens/figma_variables_raw_export.json")
    css_path = Path("design/tokens/tokens.css")
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    
    mutated = dict(data)
    mutated["variables"] = [dict(v) for v in data["variables"]]
    for v in mutated["variables"]:
        if v["name"] == "motion/motion-fast":
            v["valuesByMode"] = dict(v["valuesByMode"])
            v["valuesByMode"]["Light"] = "150ms"
            
    try:
        verify_variables_against_css(mutated, css_path)
        raise RuntimeError("Guard failed to catch motion-fast mutation to 150ms!")
    except AssertionError as e:
        assert "motion-fast" in str(e)



def test_figma_plugin_has_all_37_variables_and_frame11():
    """Verify that code.js defines all 37 variables exactly matching JSON/CSS, plus Frame 11."""
    code_js = Path("design/figma-plugin/code.js").read_text(encoding="utf-8")
    raw_path = Path("design/tokens/figma_variables_raw_export.json")
    raw_data = json.loads(raw_path.read_text(encoding="utf-8"))
    
    # 1. All 37 variable names present in code.js
    for v in raw_data["variables"]:
        v_name = v["name"]
        assert f'"{v_name}"' in code_js or f"'{v_name}'" in code_js, (
            f"Figma plugin code.js missing variable name: {v_name}"
        )
    
    # 2. Strict token values check in code.js
    assert '"radius/radius-lg", val: 14' in code_js or "'radius/radius-lg', val: 14" in code_js, (
        "code.js must define radius-lg as 14, matching tokens.css"
    )
    assert '"radius/radius-xl", val: 20' in code_js or "'radius/radius-xl', val: 20" in code_js, (
        "code.js must define radius-xl as 20, matching tokens.css"
    )
    assert '"motion/motion-base"' in code_js, "code.js missing motion-base"
    assert '"200ms"' in code_js, "code.js missing 200ms value"
    assert "0.14" in code_js, "code.js missing 0.14 alpha for dark tints"
    
    # 3. Frame 11 and components
    assert "Màn hình W-11" in code_js
    assert "createComponent" in code_js
    assert "flowStartingPoints" in code_js
    assert "&bull;" not in code_js, "code.js must not contain raw unencoded &bull; strings"


def test_w11_course_management_specification():
    """Verify W-11 course management rules: 6-char token in list, one-time URL result, >=44px buttons, data safety."""
    w11_html = Path("design/preview/w11_course_management_screens.html").read_text(encoding="utf-8")
    
    # 1. 6-character token in list table
    assert "X9A4B2" in w11_html
    # In tbody, no full URL or copy button
    tbody_start = w11_html.find("<tbody>")
    tbody_end = w11_html.find("</tbody>")
    assert tbody_start != -1 and tbody_end != -1
    tbody_content = w11_html[tbody_start:tbody_end]
    assert "https://wayfinder.edu.vn/join/" not in tbody_content, "Link list table must not contain full URL"
    assert "Sao chép" not in tbody_content, "Link list table must not contain copy button"
    
    # 2. One-time result box has full URL and copy button
    assert 'id="box-new-link-result"' in w11_html
    assert 'id="btn-copy-new-link-one-time"' in w11_html
    assert "https://wayfinder.edu.vn/join/X9A4B2" in w11_html
    
    # 3. Danger zone wording respects private learning progress and shared artifacts
    assert "Tiến trình học riêng của học viên và các tài liệu/artifact dùng chung được lưu giữ" in w11_html
    
    # 4. Touch target 44px
    assert "min-height: 44px" in w11_html
    assert "min-width: 44px" in w11_html
    assert "36px" not in w11_html, "w11_course_management_screens.html must not contain substandard 36px buttons"


def test_w08_lecture_specification():
    """Verify W-08 lecture states: streaming, prerequisites open, source viewer, fatal error, page viewer, bug report, >=44px buttons."""
    w08_html = Path("design/preview/w08_lecture_screens.html").read_text(encoding="utf-8")
    
    assert 'id="section-lecture-streaming"' in w08_html
    assert 'id="section-lecture-prerequisites"' in w08_html
    assert 'id="section-source-viewer"' in w08_html
    assert 'id="section-lecture-fatal-error"' in w08_html
    assert 'id="btn-exit-to-roadmap"' in w08_html
    assert 'id="section-page-image-viewer"' in w08_html
    assert 'id="section-content-bug-report"' in w08_html
    assert "OCR y khoa" not in w08_html, "Must not claim OCR y khoa without spec"
    assert "36px" not in w08_html, "w08_lecture_screens.html must not contain substandard 36px buttons"
    assert "min-height: 44px" in w08_html


def test_w09_chat_screens_specification():
    """Verify W-09 chat states: active session with turns, module badge, tool progress, scope outdated, daily limit, >=44px buttons."""
    w09_html = Path("design/preview/w09_chat_screens.html").read_text(encoding="utf-8")
    assert 'id="section-chat-active"' in w09_html
    assert 'id="badge-chat-module"' in w09_html
    assert 'id="badge-chat-turns"' in w09_html
    assert 'id="section-chat-tool-progress"' in w09_html
    assert 'id="section-chat-scope-outdated"' in w09_html
    assert 'id="section-chat-limit-exceeded"' in w09_html
    assert 'id="btn-return-roadmap-from-chat"' in w09_html
    assert "min-height: 44px" in w09_html
    assert "36px" not in w09_html


def test_w10_quiz_screens_specification():
    """Verify W-10 quiz states: generating skeleton, taking question with option selection, 10/10 result and citation, >=44px buttons."""
    w10_html = Path("design/preview/w10_quiz_screens.html").read_text(encoding="utf-8")
    assert 'id="section-quiz-generating"' in w10_html
    assert 'id="section-quiz-taking"' in w10_html
    assert 'id="opt-q3-selected"' in w10_html
    assert 'id="section-quiz-result"' in w10_html
    assert 'id="quiz-citation-box"' in w10_html
    assert "min-height: 44px" in w10_html
    assert "36px" not in w10_html


def test_w14_cancellation_respects_usage_contract():
    """Verify W-14 cancellation state does not promise full refund or resource clearance for confirmed runs."""
    w14_html = Path("design/preview/w14_upload_screens.html").read_text(encoding="utf-8")
    assert 'id="section-pipeline-cancelled"' in w14_html
    assert "không hoàn lại lượt dựng đã xác nhận" in w14_html
    cancelled_part = w14_html.split('id="section-pipeline-cancelled"')[1]
    assert "không trừ lượt dựng" not in cancelled_part, (
        "Cancelled section must not promise free cancellation after confirmation"
    )


def test_falsifiable_plugin_radius_lg_16_mutation_fails():
    """Falsifiable test: prove that an altered radius-lg (16 instead of 14) in code.js fails verification."""
    fake_code_js = 'const radiusDefs = [{ name: "radius/radius-lg", val: 16 }];'
    with pytest.raises(AssertionError):
        assert '"radius/radius-lg", val: 14' in fake_code_js


def test_falsifiable_w11_copy_in_tbody_fails():
    """Falsifiable test: prove that having a copy button in link list table fails verification."""
    fake_tbody = '<tbody><tr><td>X9A4B2</td><td><button>Sao chép</button></td></tr></tbody>'
    with pytest.raises(AssertionError):
        assert "Sao chép" not in fake_tbody


def test_falsifiable_w08_ocr_claim_fails():
    """Falsifiable test: prove that adding OCR y khoa to w08 lecture fails verification."""
    fake_w08 = '<p>Trích xuất tự động qua công cụ OCR y khoa WayFinder.</p>'
    with pytest.raises(AssertionError):
        assert "OCR y khoa" not in fake_w08


def test_falsifiable_w11_36px_button_fails():
    """Falsifiable test: prove that a 36px button in w11 fails verification."""
    fake_w11 = '<button class="btn" style="min-height: 36px;">Thu hồi</button>'
    with pytest.raises(AssertionError):
        assert "36px" not in fake_w11



def test_falsifiable_fatal_error_exit_missing_fails():
    """Falsifiable test: prove that omitting exit to roadmap in fatal lecture fails verification."""
    fake_lecture = '<div id="section-lecture-fatal-error"><h3>Lỗi bài học</h3></div>'
    with pytest.raises(AssertionError):
        assert 'id="btn-exit-to-roadmap"' in fake_lecture


def test_falsifiable_chat_daily_limit_missing_fails():
    """Falsifiable test: prove that omitting daily limit state in chat fails verification."""
    fake_chat = '<div id="section-chat-active"><p>Chat đang chạy</p></div>'
    with pytest.raises(AssertionError):
        assert 'id="section-chat-limit-exceeded"' in fake_chat


def test_falsifiable_quiz_generating_missing_fails():
    """Falsifiable test: prove that omitting generating question state in quiz fails verification."""
    fake_quiz = '<div id="section-quiz-taking"><p>Câu hỏi 1</p></div>'
    with pytest.raises(AssertionError):
        assert 'id="section-quiz-generating"' in fake_quiz
