import json
from pathlib import Path

tokens_path = Path("design/tokens/tokens.json")
tokens = json.loads(tokens_path.read_text(encoding="utf-8"))

var_export = {
    "$schema": "https://design-tokens.github.io/community-group/format/draft-spec.json",
    "metadata": {
        "generator": "scripts/generate_figma_variables_export.py",
        "provenance": "Local DTCG schema definition mapped from design/tokens/tokens.json",
        "collectionName": "WayFinder Tokens",
        "modes": ["Light", "Dark"],
        "targetFileKey": "UVhhlZnqdpV0JDcAHwJczo"
    },
    "collections": [
        {
            "name": "WayFinder Tokens",
            "modes": {
                "mode:light": "Light",
                "mode:dark": "Dark"
            },
            "variables": []
        }
    ]
}

var_list = var_export["collections"][0]["variables"]

# Color variables
light_colors = tokens["color"]["light"]
dark_colors = tokens["color"]["dark"]
all_color_keys = sorted(set(list(light_colors.keys()) + list(dark_colors.keys())))

for k in all_color_keys:
    l_val = light_colors.get(k, {}).get("$value", "")
    d_val = dark_colors.get(k, {}).get("$value", l_val)
    var_list.append({
        "name": f"color/{k}",
        "type": "COLOR",
        "valuesByMode": {
            "mode:light": l_val,
            "mode:dark": d_val
        },
        "scopes": ["ALL_FILLS", "STROKE_COLOR", "TEXT_COLOR"]
    })

# Spacing variables
for k, v in tokens["spacing"].items():
    raw_px = float(v["$value"].replace("px", ""))
    var_list.append({
        "name": f"spacing/{k}",
        "type": "FLOAT",
        "valuesByMode": {
            "mode:light": raw_px,
            "mode:dark": raw_px
        },
        "scopes": ["GAP", "CORNER_RADIUS", "WIDTH_HEIGHT"]
    })

# Radius variables
for k, v in tokens["radius"].items():
    raw_px = float(v["$value"].replace("px", ""))
    var_list.append({
        "name": f"radius/{k}",
        "type": "FLOAT",
        "valuesByMode": {
            "mode:light": raw_px,
            "mode:dark": raw_px
        },
        "scopes": ["CORNER_RADIUS"]
    })

out_path = Path("design/tokens/figma_variables_export.json")
out_path.write_text(json.dumps(var_export, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Successfully generated {out_path} with {len(var_list)} variables")
