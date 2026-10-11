"""Native-only research router for the custodian; does not invoke a parser."""
import argparse
import json
from pathlib import Path

from pha3 import native_route,ROOT,write


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();records=[]
    for book in json.loads(args.manifest.read_text(encoding='utf-8'))['books']:
        result=native_route(ROOT/book['pdf'])
        expected_system='S1' if book['type']=='native' else 'reject'
        records.append(dict(sach=book['id'],expected=book['type'],**result,
            correct=result['pdf_type']==book['type'] and result['system']==expected_system))
        print(book['id'],result['pdf_type'],result['system'],flush=True)
    write(args.out,dict(books=records,total=len(records),correct=sum(r['correct'] for r in records),
        false_native_rejections=sum(r['expected']=='native' and r['system']!='S1' for r in records)))


if __name__=='__main__':main()
