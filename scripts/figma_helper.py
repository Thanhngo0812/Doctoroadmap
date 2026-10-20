"""Figma API helper for Doctoroadmap.
Enables fetching metadata, node details, design tokens, and exporting images from Figma.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Fix Windows console encoding for Unicode/Vietnamese
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def get_token() -> str:
    token = os.environ.get("FIGMA_ACCESS_TOKEN")
    if token:
        return token.strip()

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("FIGMA_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip()

    raise RuntimeError("FIGMA_ACCESS_TOKEN not found in environment or .env file.")


def parse_figma_url(url_or_key: str) -> tuple[str, str | None]:
    """Parse file key and optional node id from Figma URL or file key string."""
    url_or_key = url_or_key.strip()
    if "/" not in url_or_key and not url_or_key.startswith("http"):
        return url_or_key, None

    parsed = urllib.parse.urlparse(url_or_key)
    path_parts = [p for p in parsed.path.split("/") if p]
    
    file_key = ""
    for i, part in enumerate(path_parts):
        if part in ("file", "design", "board") and i + 1 < len(path_parts):
            file_key = path_parts[i + 1]
            break

    if not file_key and path_parts:
        file_key = path_parts[0]

    node_id = None
    query_params = urllib.parse.parse_qs(parsed.query)
    if "node-id" in query_params:
        node_id = query_params["node-id"][0].replace("-", ":")

    return file_key, node_id


def _api_get(endpoint: str, token: str) -> dict:
    import time
    url = f"https://api.figma.com/v1/{endpoint.lstrip('/')}"
    req = urllib.request.Request(
        url,
        headers={
            "X-Figma-Token": token,
            "User-Agent": "Doctoroadmap-Figma-Client/1.0",
        },
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raw_retry = e.headers.get("Retry-After", "5")
                try:
                    retry_after = int(raw_retry)
                except ValueError:
                    retry_after = 5
                if retry_after > 10:
                    raise RuntimeError(f"Figma API Rate Limit exceeded (Retry-After: {retry_after}s). Cannot export via REST image endpoint.")
                if attempt < 2:
                    time.sleep(retry_after)
                    continue
            raise


def get_file(file_key: str, depth: int | None = 2) -> dict:
    token = get_token()
    query = f"?depth={depth}" if depth is not None else ""
    return _api_get(f"files/{file_key}{query}", token)


def get_node(file_key: str, node_id: str) -> dict:
    token = get_token()
    clean_node_id = urllib.parse.quote(node_id.replace("-", ":"))
    return _api_get(f"files/{file_key}/nodes?ids={clean_node_id}", token)


def export_image(file_key: str, node_id: str, fmt: str = "png", scale: float = 2.0) -> str:
    token = get_token()
    clean_node_id = urllib.parse.quote(node_id.replace("-", ":"))
    res = _api_get(f"images/{file_key}?ids={clean_node_id}&format={fmt}&scale={scale}", token)
    images = res.get("images", {})
    raw_node_id = node_id.replace("-", ":")
    image_url = images.get(raw_node_id) or next(iter(images.values()), None)
    if not image_url:
        raise RuntimeError(f"Could not export image for node {node_id}")
    return image_url


def download_file(url: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(output_path, "wb") as f:
        f.write(resp.read())
    return output_path


def format_node_summary(node: dict, indent: int = 0) -> list[str]:
    lines = []
    prefix = "  " * indent
    name = node.get("name", "Unnamed")
    ntype = node.get("type", "UNKNOWN")
    box = node.get("absoluteBoundingBox") or {}
    w = round(box.get("width", 0))
    h = round(box.get("height", 0))
    size_str = f" ({w}x{h})" if w and h else ""
    
    details = []
    if "layoutMode" in node:
        details.append(f"AutoLayout:{node['layoutMode']}")
    if "itemSpacing" in node:
        details.append(f"gap:{node['itemSpacing']}")
    if "paddingLeft" in node:
        details.append(f"pad:({node.get('paddingTop',0)},{node.get('paddingRight',0)},{node.get('paddingBottom',0)},{node.get('paddingLeft',0)})")

    detail_str = f" [{', '.join(details)}]" if details else ""
    lines.append(f"{prefix}- [{ntype}] {name} (id: {node.get('id')}){size_str}{detail_str}")

    if ntype == "TEXT":
        chars = node.get("characters", "").replace("\n", " ").strip()
        if chars:
            display_chars = chars if len(chars) <= 60 else chars[:57] + "..."
            lines.append(f"{prefix}    Text: \"{display_chars}\"")
        style = node.get("style", {})
        if style:
            font = style.get("fontFamily", "")
            size = style.get("fontSize", "")
            weight = style.get("fontWeight", "")
            lines.append(f"{prefix}    Font: {font} {size}px (weight: {weight})")

    for child in node.get("children", []):
        lines.extend(format_node_summary(child, indent + 1))

    return lines


def main():
    parser = argparse.ArgumentParser(description="Doctoroadmap Figma CLI")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    info_p = subparsers.add_parser("info", help="Get summary of a Figma file")
    info_p.add_argument("target", help="Figma URL or File Key")
    info_p.add_argument("--depth", type=int, default=2, help="Tree depth")

    node_p = subparsers.add_parser("node", help="Inspect a specific node/frame")
    node_p.add_argument("target", help="Figma URL or File Key")
    node_p.add_argument("--node-id", help="Node ID (e.g. 1:2 or 1-2). If in URL, optional.")

    export_p = subparsers.add_parser("export", help="Export a node as image/svg")
    export_p.add_argument("target", help="Figma URL or File Key")
    export_p.add_argument("--node-id", help="Node ID to export")
    export_p.add_argument("--out", required=True, help="Output file path (e.g. assets/preview.png)")
    export_p.add_argument("--format", choices=["png", "svg", "jpg", "pdf"], default="png")
    export_p.add_argument("--scale", type=float, default=2.0)

    args = parser.parse_args()

    file_key, url_node_id = parse_figma_url(args.target)
    node_id = getattr(args, "node_id", None) or url_node_id

    if args.cmd == "info":
        data = get_file(file_key, depth=args.depth)
        name = data.get("name", "Untitled")
        print(f"File Name: {name}")
        print(f"File Key:  {file_key}")
        print(f"Version:   {data.get('version')}")
        print("\nPages and Frames:")
        for page in data.get("document", {}).get("children", []):
            print(f"- Page: {page.get('name')} (id: {page.get('id')})")
            for frame in page.get("children", []):
                box = frame.get("absoluteBoundingBox") or {}
                dims = f" ({round(box.get('width', 0))}x{round(box.get('height', 0))})" if box else ""
                print(f"    Frame: {frame.get('name')} [id: {frame.get('id')}]{dims}")

    elif args.cmd == "node":
        if not node_id:
            print("Error: --node-id is required if not in the URL", file=sys.stderr)
            sys.exit(1)
        data = get_node(file_key, node_id)
        nodes = data.get("nodes", {})
        raw_id = node_id.replace("-", ":")
        target_node = nodes.get(raw_id, {}).get("document")
        if not target_node:
            print(f"Node {node_id} not found in response.", file=sys.stderr)
            sys.exit(1)
        print("\n".join(format_node_summary(target_node)))

    elif args.cmd == "export":
        if not node_id:
            print("Error: --node-id is required if not in the URL", file=sys.stderr)
            sys.exit(1)
        img_url = export_image(file_key, node_id, fmt=args.format, scale=args.scale)
        out_path = Path(args.out)
        saved = download_file(img_url, out_path)
        print(f"Successfully exported {node_id} -> {saved}")


if __name__ == "__main__":
    main()
