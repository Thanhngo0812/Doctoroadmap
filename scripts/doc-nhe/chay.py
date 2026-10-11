"""Run the v4-14 CPU experiment; pause for alignment review on a new dataset."""
import argparse
import subprocess
import sys
from pathlib import Path

import hoc_tieu_de as m


def reviewed(out):
    sample = m.read(out / 'alignment-review-80.json')
    path = out / 'alignment-review-80-reviewed.json'
    if not path.exists():
        raise ValueError('Review the 80 alignment samples and record the review before training; see README.md')
    review = m.read(path)
    if (len(sample) != 80 or review.get('sample_sha256') != m.digest(out / 'alignment-review-80.json')
            or sorted(r['sample'] for r in review.get('reviews', [])) != list(range(1, 81))):
        raise ValueError('Alignment review is incomplete or belongs to a different sample')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=m.ROOT / 'tmp/doc-nhe-v414')
    args = parser.parse_args()
    m.prepare(args.out)
    reviewed(args.out)
    m.train(args.out)
    for name, arguments in [('danh_gia.py', []), ('bao_cao.py', ['errors']), ('bao_cao.py', ['summary'])]:
        subprocess.run([sys.executable, str(Path(__file__).with_name(name)), *arguments, '--out', str(args.out)],
                       cwd=m.ROOT, check=True)


if __name__ == '__main__':
    main()
