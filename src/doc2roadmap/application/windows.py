from collections import defaultdict

from doc2roadmap.domain.models import Chunk


def assemble_windows(chunks: list[Chunk]) -> dict[str, list[Chunk]]:
    windows: dict[str, list[Chunk]] = defaultdict(list)
    for chunk in sorted(chunks, key=lambda item: item.order_index):
        windows[chunk.parent_section_id].append(chunk)
    return dict(windows)

