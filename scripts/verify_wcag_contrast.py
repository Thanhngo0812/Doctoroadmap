"""WCAG 2.1 Contrast Ratio and Token Consistency Verification for WayFinder (W-22 / W-24).

Dynamically parses design/tokens/tokens.css and design/tokens/tokens.json to verify:
1. Exact 1:1 synchronization between CSS custom properties and JSON tokens.
2. Dynamic contrast ratio calculations of actual tokens used in CSS (Light and Dark mode).
3. Explicit verification of .btn-primary contrast in Dark Mode (primary text on primary bg).
4. Guard against unsafe mutations (e.g., white text on #29A9FF).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    def channel_lum(val: int) -> float:
        c = val / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = [channel_lum(c) for c in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(color1: str, color2: str) -> float:
    lum1 = relative_luminance(hex_to_rgb(color1))
    lum2 = relative_luminance(hex_to_rgb(color2))
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def parse_css_tokens(css_content: str) -> tuple[dict[str, str], dict[str, str]]:
    """Parse light and dark custom properties from CSS content."""
    root_match = re.search(r":root\s*\{([^}]+)\}", css_content, re.DOTALL)
    root_block = root_match.group(1) if root_match else ""

    dark_match = re.search(r'\[data-theme=["\']dark["\']\][^{]*\{([^}]+)\}', css_content, re.DOTALL)
    dark_block = dark_match.group(1) if dark_match else ""

    def extract_vars(block: str) -> dict[str, str]:
        vars_dict = {}
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("--") and ":" in line:
                key, val = line.split(":", 1)
                clean_key = key.strip()
                clean_val = val.split(";", 1)[0].split("/*", 1)[0].strip()
                vars_dict[clean_key] = clean_val
        return vars_dict

    return extract_vars(root_block), extract_vars(dark_block)


def parse_json_tokens(json_path: Path) -> dict:
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def verify_tokens_and_contrast(css_path: Path, json_path: Path) -> tuple[bool, list[str]]:
    logs = []
    if not css_path.exists():
        return False, [f"CSS file not found: {css_path}"]
    if not json_path.exists():
        return False, [f"JSON file not found: {json_path}"]

    css_content = css_path.read_text(encoding="utf-8")
    light_css, dark_css = parse_css_tokens(css_content)
    json_data = parse_json_tokens(json_path)

    json_light = json_data.get("color", {}).get("light", {})
    json_dark = json_data.get("color", {}).get("dark", {})

    all_ok = True

    # 1. Check CSS vs JSON sync for light colors
    for key, val_obj in json_light.items():
        var_name = f"--{key}"
        json_val = val_obj.get("$value", "").upper()
        css_val = light_css.get(var_name, "").upper()
        if not css_val:
            logs.append(f"FAIL: Variable {var_name} missing from :root in CSS")
            all_ok = False
        elif css_val != json_val:
            logs.append(f"FAIL: Value mismatch for {var_name}: CSS={css_val} vs JSON={json_val}")
            all_ok = False

    # 2. Check CSS vs JSON sync for dark colors (for hex tokens)
    for key, val_obj in json_dark.items():
        var_name = f"--{key}"
        json_val = val_obj.get("$value", "").upper()
        if json_val.startswith("#"):
            css_val = dark_css.get(var_name, "").upper()
            if not css_val:
                logs.append(f"FAIL: Variable {var_name} missing from dark mode in CSS")
                all_ok = False
            elif css_val != json_val:
                logs.append(f"FAIL: Value mismatch for dark {var_name}: CSS={css_val} vs JSON={json_val}")
                all_ok = False

    # 3. Dynamic contrast checks on ACTUAL parsed CSS values
    checks = [
        # (Name, fg_key, bg_key, min_ratio, mode, desc)
        ("text_on_bg", "--color-text", "--color-bg", 4.5, "light", "Chữ chính trên nền trắng"),
        ("text_muted_on_bg", "--color-text-muted", "--color-bg", 4.5, "light", "Chữ phụ trên nền trắng"),
        ("text_muted_on_subtle", "--color-text-muted", "--color-bg-subtle", 4.5, "light", "Chữ phụ trên nền phụ"),
        ("primary_on_bg", "--color-primary", "--color-bg", 4.5, "light", "Link chính trên nền trắng"),
        ("primary_btn_light", "--color-primary-text", "--color-primary", 4.5, "light", "Nút chính Sáng (chữ trên nền nút)"),
        ("border_input_on_bg", "--color-border-input", "--color-bg", 3.0, "light", "Viền ô nhập trên nền trắng"),
        ("accent_text_on_tint", "--color-accent-text", "--color-accent-tint", 4.5, "light", "Chữ cảnh báo trên nền hổ phách nhạt"),
        ("text_on_accent", "--color-text", "--color-accent", 4.5, "light", "Chữ tối trên huy hiệu hổ phách"),
        ("success_on_tint", "--color-success", "--color-success-tint", 4.5, "light", "Chữ thành công trên nền xanh lá nhạt"),
        ("danger_on_tint", "--color-danger", "--color-danger-tint", 4.5, "light", "Chữ lỗi trên nền đỏ nhạt"),
        # Dark Mode checks
        ("dark_text_on_surface", "--color-text", "--color-surface", 4.5, "dark", "[Dark] Chữ chính trên surface"),
        ("dark_muted_on_surface", "--color-text-muted", "--color-surface", 4.5, "dark", "[Dark] Chữ phụ trên surface"),
        ("dark_primary_on_surface", "--color-primary", "--color-surface", 4.5, "dark", "[Dark] Primary trên surface"),
        ("primary_btn_dark", "--color-primary-text", "--color-primary", 4.5, "dark", "[Dark] Nút chính Tối (chữ tối trên nền primary)"),
        ("dark_accent_on_surface", "--color-accent", "--color-surface", 4.5, "dark", "[Dark] Accent trên surface"),
        ("dark_success_on_surface", "--color-success", "--color-surface", 4.5, "dark", "[Dark] Success trên surface"),
        ("dark_danger_on_surface", "--color-danger", "--color-surface", 4.5, "dark", "[Dark] Danger trên surface"),
    ]

    for name, fg_k, bg_k, min_r, mode, desc in checks:
        palette = light_css if mode == "light" else dark_css
        fg = palette.get(fg_k)
        bg = palette.get(bg_k)
        if not fg or not bg:
            logs.append(f"FAIL: Missing variable {fg_k} or {bg_k} in {mode} CSS")
            all_ok = False
            continue

        ratio = contrast_ratio(fg, bg)
        passed = ratio >= min_r
        res_str = "PASS" if passed else "FAIL"
        logs.append(f"{name:<24} | FG={fg} BG={bg} | Ratio={ratio:>5.2f}:1 (Req >={min_r:>3.1f}:1) | {res_str}")
        if not passed:
            all_ok = False

    return all_ok, logs


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    css_path = Path("design/tokens/tokens.css")
    json_path = Path("design/tokens/tokens.json")

    ok, logs = verify_tokens_and_contrast(css_path, json_path)
    for log in logs:
        print(log)

    # Falsifiable check on simulated mutation
    print("\n--- FALSIFIABLE MUTATION CHECK ---")
    mutated_ratio = contrast_ratio("#FFFFFF", "#29A9FF")
    print(f"White text on #29A9FF contrast ratio: {mutated_ratio:.2f}:1 (Must fail < 4.5:1)")
    if mutated_ratio < 4.5:
        print("CONFIRMED: Mutation of button text/bg to white-on-#29A9FF is caught by WCAG guard!")
    else:
        print("ERROR: Mutation was not caught!")
        ok = False

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
