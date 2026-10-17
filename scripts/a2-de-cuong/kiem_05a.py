"""Read-only 05a audit of saved chunks; never opens T-01 or smoke documents."""
import argparse
import json
from pathlib import Path

from doc2roadmap.domain.chunking import assign_section_roles, repeated_heading_coverage
from doc2roadmap.domain.models import Chunk, Section


def audit(artifacts):
    documents, rows = [], []
    for doc in sorted((Path(artifacts) / 'chunks').iterdir()):
        if not doc.is_dir() or doc.name in {'d01-t01', 'd01-t02'} or doc.name.startswith('smoke'):
            continue
        versions = [p for p in doc.iterdir() if p.is_dir() and p.name.startswith('v') and p.name[1:].isdigit()]
        if not versions:
            continue
        latest = max(versions, key=lambda p: int(p.name[1:]))
        sections = [Section.from_dict(row) for row in json.loads((latest / 'sections.json').read_text(encoding='utf-8'))]
        payload = json.loads((latest / 'chunks.json').read_text(encoding='utf-8'))
        chunks = [Chunk.from_dict(row) for row in (payload['chunks'] if isinstance(payload, dict) else payload)]
        medians = repeated_heading_coverage(sections, chunks)
        stored_roles = {title: sorted({s.role for s in sections if s.title == title}) for title in medians}
        assign_section_roles(sections, chunks)
        documents.append(doc.name)
        for title, coverage in medians.items():
            members = [s for s in sections if s.title == title]
            rows.append({'doc_id': doc.name, 'chunks_version': int(latest.name[1:]), 'title': title,
                         'section_count': len(members), 'median_coverage': coverage,
                         # Back matter precedes repetition in both versions; every other old member was locked.
                         'old_roles': sorted({'cuoi_sach' if s.role == 'cuoi_sach' and s.role_source == 'structure'
                                              else 'de_cuong' for s in members}),
                         'stored_roles': stored_roles[title], 'new_roles': sorted({s.role for s in members}),
                         'new_role_sources': sorted({s.role_source for s in members}),
                         'outline_by_repetition': coverage is not None and coverage >= .5})
    return {'documents': documents, 'document_count': len(documents), 'group_count': len(rows), 'groups': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, default=Path('artifacts'))
    args = parser.parse_args()
    print(json.dumps(audit(args.artifacts), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
