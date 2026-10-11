"""D-02 validator, portable standard-library-only command for annotation agents."""
import argparse
import json
import re
import sys
from pathlib import Path

REGIONS={'mo_dau','noi_dung','bai_tap','de_cuong','hanh_chinh','cuoi_sach'}
ROLES={'tieu_de','than_bai','danh_sach','cong_thuc','bang','ma_lenh','chu_thich_hinh',
       'chu_trong_hinh','dau_trang','chan_trang','so_trang','chu_thich_cuoi_trang','muc_luc','khac'}
EXCLUDED={'dau_trang','chan_trang','so_trang','chu_trong_hinh'}


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def load_labels(sach,folder,*,review=False):
    folder=Path(folder)
    heads=read_jsonl(folder/'cay-muc'/f'{sach}.jsonl')
    sample=folder/'trang-mau'/f'{sach}.jsonl'
    pages=read_jsonl(sample) if sample.exists() else []
    corrections=folder/'duyet'/f'{sach}.jsonl'
    if review and corrections.exists():
        updates=read_jsonl(corrections);head_ids={h['id'] for h in heads};page_ids={p['trang'] for p in pages}
        for value in updates:
            if 'id' in value:
                if value['id'] not in head_ids:raise ValueError('Bản duyệt trỏ tiêu đề không có trong L1')
                heads=[value if h['id']==value['id'] else h for h in heads]
            else:
                if value.get('trang') not in page_ids:raise ValueError('Bản duyệt trỏ trang không có trong L2')
                pages=[value if p['trang']==value['trang'] else p for p in pages]
    return heads,pages


def validate(sach, folder, *, l2_required=True,review=False):
    folder=Path(folder); errors=[]
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*',sach):
        return ['sach: mã sách không hợp lệ']
    try:
        lines=read_jsonl(folder/'dong'/f'{sach}.jsonl')
        heads,pages=load_labels(sach,folder,review=review)
        selected=json.loads((folder/'chon-trang-mau'/f'{sach}.json').read_text(encoding='utf-8-sig'))['trang']
    except (OSError,ValueError,KeyError,TypeError) as error:
        return [f'Không đọc được phiếu/nhãn: {error}']
    if not isinstance(selected,list) or any(type(p) is not int or p<1 for p in selected) or len(set(selected))!=len(selected):
        return ['chon-trang-mau: danh sách trang không hợp lệ']
    source={}; positions={}; by_page={}
    for i,line in enumerate(lines):
        if not isinstance(line,dict): errors.append(f'dong {i+1}: cần object');continue
        key=line.get('id'); page=line.get('trang')
        if not isinstance(key,str) or not re.fullmatch(r'p\d{4,}-l\d{3,}',key):
            errors.append(f'dong {i+1}: id sai');continue
        if type(page) is not int or page<1 or int(key.split('-')[0][1:])!=page:
            errors.append(f'{key}: trang không khớp id');continue
        if key in source:errors.append(f'{key}: mã dòng trùng')
        if not isinstance(line.get('text'),str) or not line['text'].strip():errors.append(f'{key}: text rỗng/sai')
        source[key]=line;positions[key]=i;by_page.setdefault(page,set()).add(key)
    used=set();stacks={'content':{},'front':{}};branches={};previous_number=-1;previous_position=-1
    for i,head in enumerate(heads):
        if not isinstance(head,dict):errors.append(f'cay-muc {i+1}: cần object');continue
        key=head.get('id'); level=head.get('cap'); ids=head.get('dong')
        required={'sach','id','dong','text','cap','cha','vung','ghi_chu'}
        if not required<=head.keys():errors.append(f'{key}: thiếu trường bắt buộc')
        if head.get('sach')!=sach:errors.append(f'{key}: sach sai')
        if not isinstance(key,str) or not re.fullmatch(r'h\d+',key):errors.append(f'{key}: id tiêu đề sai')
        else:
            number=int(key[1:])
            if number<=previous_number:errors.append(f'{key}: id trùng/không tăng')
            previous_number=number
        if not isinstance(ids,list) or not ids or any(not isinstance(x,str) for x in ids):
            errors.append(f'{key}: dong phải là danh sách không rỗng');ids=[]
        if len(ids)!=len(set(ids)) or used.intersection(ids):errors.append(f'{key}: mã dòng thuộc nhiều tiêu đề')
        used.update(ids)
        if any(x not in source for x in ids):errors.append(f'{key}: mã dòng không tồn tại')
        elif ids:
            order=[positions[x] for x in ids]
            if order!=sorted(order) or order[0]<=previous_position:errors.append(f'{key}: sai thứ tự đọc')
            previous_position=order[-1]
        if not isinstance(head.get('text'),str) or not head['text'].strip():errors.append(f'{key}: text rỗng/sai')
        if not isinstance(head.get('ghi_chu'),str):errors.append(f'{key}: ghi_chu phải là chữ')
        if type(level) is not int or not 1<=level<=6:errors.append(f'{key}: cap ngoài 1–6');continue
        branch=('front' if head.get('vung') in ('mo_dau','hanh_chinh') else 'content') if level==1 else branches.get(head.get('cha'),'content')
        stack=stacks[branch]
        expected=None if level==1 else stack.get(level-1)
        if (level>1 and expected is None) or head.get('cha')!=expected:
            errors.append(f'{key}: cha phải là tiêu đề đang mở cấp {level-1} trong nhánh logic')
        if level==1 and (not isinstance(head.get('vung'),str) or head['vung'] not in REGIONS):errors.append(f'{key}: vung cấp 1 sai')
        elif level>1 and head.get('vung') is not None:errors.append(f'{key}: vung cấp con phải null')
        stack={depth:value for depth,value in stack.items() if depth<level};stack[level]=key
        stacks[branch]=stack
        if isinstance(key,str):branches[key]=branch
    seen=set()
    for i,page in enumerate(pages):
        if not isinstance(page,dict):errors.append(f'trang-mau {i+1}: cần object');continue
        number=page.get('trang'); roles=page.get('dong'); order=page.get('thu_tu')
        if type(number) is not int:errors.append('trang-mau: trang phải số nguyên');continue
        if number not in selected or number in seen:errors.append(f'trang {number}: ngoài mẫu/trùng')
        seen.add(number)
        if page.get('sach')!=sach:errors.append(f'trang {number}: sach sai')
        if not isinstance(roles,dict):errors.append(f'trang {number}: dong phải object');continue
        if set(roles)!=by_page.get(number,set()):errors.append(f'trang {number}: thiếu/thừa mã dòng')
        if any(not isinstance(r,str) or r not in ROLES for r in roles.values()):errors.append(f'trang {number}: vai trò sai')
        expected={x for x,r in roles.items() if not isinstance(r,str) or r not in EXCLUDED}
        if (not isinstance(order,list) or any(not isinstance(x,str) for x in order)
                or len(order)!=len(set(order)) or set(order)!=expected):errors.append(f'trang {number}: thu_tu không là hoán vị đúng')
        if {x for x,r in roles.items() if r=='tieu_de'} != used.intersection(by_page.get(number,set())):
            errors.append(f'trang {number}: tieu_de không khớp cây mục')
        if any(type(page.get(flag)) is not bool for flag in ('co_bang','co_hinh')):errors.append(f'trang {number}: cờ phải true/false')
        if not isinstance(page.get('ghi_chu'),str):errors.append(f'trang {number}: ghi_chu phải là chữ')
    if (l2_required or pages) and seen!=set(selected):errors.append('trang-mau: thiếu trang được chọn')
    return errors


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sach',required=True)
    parser.add_argument('--thu-muc',type=Path,required=True)
    parser.add_argument('--chi-cay',action='store_true',help='L1 only; L2 is optional for development scoring')
    parser.add_argument('--ban-duyet',action='store_true',help='Áp dụng bản sửa riêng trong duyet/, không ghi đè nhãn agentic')
    args=parser.parse_args()
    errors=validate(args.sach,args.thu_muc,l2_required=not args.chi_cay,review=args.ban_duyet)
    print('\n'.join(errors) if errors else 'ĐẠT')
    raise SystemExit(1 if errors else 0)
