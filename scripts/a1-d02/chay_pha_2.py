"""Resume local fresh-process S0/S1/S2 measurements; never read locked books."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

from kiem_nhan_d02 import read_jsonl,validate,load_labels
from cham_d02 import score,aggregate
from xuat_phieu import ROOT,DEVELOPMENT,development_paths,write


def machine_cpu():
    if sys.platform!='win32':return None
    def sample():
        values=[ctypes.c_ulonglong() for _ in range(3)]
        if not ctypes.windll.kernel32.GetSystemTimes(*(ctypes.byref(v) for v in values)):raise ctypes.WinError()
        return [v.value for v in values]
    first=sample();time.sleep(1);last=sample()
    idle,kernel,user=[b-a for a,b in zip(first,last)];total=kernel+user
    return 1-idle/total if total else None


def inputs(folder):
    result={}
    for key in DEVELOPMENT:
        for review in (False,True):
            errors=validate(key,folder,review=review)
            if errors:raise ValueError(key+': '+'; '.join(errors))
        for part in ('dong','cay-muc','trang-mau','duyet'):
            path=folder/part/(key+'.jsonl')
            if path.exists():result[str(path.resolve())]=hashlib.sha256(path.read_bytes()).hexdigest()
    for path in Path(__file__).parent.glob('*.py'):
        result[str(path.resolve())]=hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def summarize(folder,out,runs):
    books=[];completed=0
    for key in DEVELOPMENT:
        lines=read_jsonl(folder/'dong'/(key+'.jsonl'))
        raw_heads,raw_pages=load_labels(key,folder)
        heads,pages=load_labels(key,folder,review=True)
        book=dict(sach=key,pdf_type='native',systems={},agentic={},timings={})
        for system in ('S1','S2','S0'):
            predictions=[]
            for i in range(1,runs+1):
                path=out/key/system/f'run-{i}'/'prediction.json'
                if path.exists():predictions.append(json.loads(path.read_text(encoding='utf-8')));completed+=1
            if not predictions:continue
            book['systems'][system]=score(lines,heads,pages,predictions[0])
            book['agentic'][system]=score(lines,raw_heads,raw_pages,predictions[0])
            timing=[p['runtime'] for p in predictions]
            book['timings'][system]=dict(runs=len(timing),seconds_per_page=statistics.median(p['seconds_per_page'] for p in timing),
                seconds=statistics.median(p['seconds'] for p in timing),peak_rss_mb=max(p['peak_rss_mb'] for p in timing),
                measurements=timing)
            book['systems'][system]['M5']=book['timings'][system]
            if any(p['headings']!=predictions[0]['headings'] or p['chunks']!=predictions[0]['chunks'] for p in predictions[1:]):
                raise ValueError('Repeated output differs: '+key+' '+system)
        books.append(book)
    result=dict(books=books,summary=aggregate(books),completed=completed,total=len(DEVELOPMENT)*3*runs,
        complete=completed==len(DEVELOPMENT)*3*runs,api_usd=0,
        label_status='agentic silver + five owner-authorized parent corrections, not a full human gold review',
        reviewed_l2_pages=0,scanned_development_books=0)
    write(out/'results.json',result)
    rows=['# Vé 15 — phép đo pha 2 đang chạy' if not result['complete'] else '# Vé 15 — phép đo pha 2 hoàn tất',
          '',f"Đã lưu {completed}/{result['total']} lần chạy mới. Chi API: 0 USD.",
          'Nhãn agentic độc lập; có bản sửa cha được chủ dự án cho phép. Chưa có duyệt ngữ nghĩa toàn bộ/vàng L2.',
          'Sáu cuốn phát triển đều PDF gốc; chưa kết luận cho bản quét hoặc tập khoá.',
          '', '| Sách | Hệ | M1 F1 | M2 | M3 | M6 | Giây/trang | Lần đo |',
          '|---|---|---:|---:|---:|---:|---:|---:|']
    number=lambda v:'—' if v is None else f'{v:.4f}'
    for b in books:
        for s,m in b['systems'].items():
            t=b['timings'][s]
            rows.append(f"| {b['sach']} | {s} | {number(m['M1']['f1'])} | {number(m['M2']['accuracy'])} | {number(m['M3']['accuracy'])} | {number(m['M6']['share'])} | {number(t['seconds_per_page'])} | {t['runs']} |")
    (out/'progress.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    return result


def run(folder,out,runs):
    folder=folder.resolve();out=out.resolve();out.mkdir(parents=True,exist_ok=True)
    pinned=inputs(folder);manifest=out/'inputs.json'
    if manifest.exists():
        if json.loads(manifest.read_text(encoding='utf-8'))!=pinned:raise ValueError('Inputs changed; choose a new output directory')
    else:write(manifest,pinned)
    # Exclusive lock is removed even on Ctrl-C. A crash leaves a visible lock for operator verification.
    lock=out/'running.lock'
    with lock.open('x',encoding='utf-8') as handle:handle.write(str(os.getpid()))
    try:
        paths=development_paths();summarize(folder,out,runs)
        for i in range(1,runs+1):
            for system in ('S0','S1','S2'):
                for key in DEVELOPMENT:
                    target=out/key/system/f'run-{i}'
                    if (target/'prediction.json').exists():continue
                    if target.exists():raise ValueError('Incomplete run directory; preserve and inspect: '+str(target))
                    interpreter=ROOT/('tmp/venv-ml/Scripts/python.exe' if system!='S0' else '.venv/Scripts/python.exe')
                    cmd=[str(interpreter),str(Path(__file__).with_name('chay_he.py')),'--pdf',str(paths[key]),
                         '--sach',key,'--system',system,'--out',str(target),'--dong',str(folder/'dong'/(key+'.jsonl'))]
                    print('START',key,system,i,flush=True)
                    cpu_before=machine_cpu()
                    log=out/f'{key}-{system}-{i}.log'
                    with log.open('w',encoding='utf-8') as handle:
                        subprocess.run(cmd,cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT,check=True,
                                       env=dict(os.environ,PYTHONIOENCODING='utf-8',HF_HUB_OFFLINE='1'))
                    prediction=target/'prediction.json'
                    data=json.loads(prediction.read_text(encoding='utf-8'))
                    data['runtime'].update(machine_cpu_before=cpu_before,idle_before=cpu_before is not None and cpu_before<.2)
                    write(prediction,data)
                    result=summarize(folder,out,runs)
                    print('CHECKPOINT',result['completed'],'/',result['total'],flush=True)
    finally:lock.unlink(missing_ok=True)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nhan',type=Path,default=ROOT/'artifacts/a1-d02/development')
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--runs',type=int,choices=[1,3],default=3)
    args=parser.parse_args();run(args.nhan,args.out,args.runs)
