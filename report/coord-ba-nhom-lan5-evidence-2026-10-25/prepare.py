import hashlib,json,subprocess
from pathlib import Path

ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
HERE=Path(__file__).parent
def output(*args):return subprocess.check_output(args,cwd=ROOT,text=True,encoding='utf-8').strip()
assert output('git','branch','--show-current')=='main'
assert output('git','rev-parse','main')=='46d829a55a62d852897f07102e89cf9a1fd5185e'
protected=['report/ket-qua-v3-05b-09b-11b-vertex-2026-09-28.md','scripts/thu-vertex/chi_thu_credit.py',
 'scripts/thu-vertex/goi_thu_vertex.py','scripts/thu-vertex/so_embedding.py',
 'task/sau-a10/19-dac-ta-bo-cau-hoi-thu.md','task/v3-lo-trinh-doc-duoc/19-goi-mo-hinh-qua-vertex.md']
snap={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in protected}
(HERE/'protected-shared-files.json').write_text(json.dumps(snap,indent=2)+'\n')
heads={name:output('git','rev-parse',branch) for name,branch in [('web','work/w09-assistant'),('core','work/w15-real-build'),('design','work/w24-figma-evidence')]}
(HERE/'worker-heads.json').write_text(json.dumps(heads,indent=2)+'\n')
path=ROOT/'report/handoff-dieu-phoi-2026-10-18.md'
text=path.read_text(encoding='utf-8')
marker='## 8. Câu hỏi treo\n\n'
assert text.count(marker)==1
note=('**Cửa nghiệm thu ba nhóm lần5 — đang giữ, Codex 2026-10-25 11:35 giờ Việt Nam:** '
      f'nhận W-09 `{heads["web"][:7]}`, W-15 `{heads["core"][:7]}`, thiết kế `{heads["design"][:7]}` trên main local46d829a. '
      'Đề nghị Claude giữ ghép SA/main và cổng PostgreSQL toàn repo tới khi Codex ghi mở lại sau commit hồ sơ lần5; '
      'làn SA vẫn có thể cài/soát riêng. Chỉ kiểm0USD; giá embedding demo theo chỉ thị được trích trong báo cáo lõi '
      'không là duyệt chạy trả tiền. Giữ quyết định chủ dự án chỉ commit local/chưa push main, không Cloud Figma, '
      'không dọn/link dữ liệu hoặc worktree.\n\n')
path.write_text(text.replace(marker,marker+note,1),encoding='utf-8',newline='\n')
assert not output('git','diff','--cached','--name-only')
subprocess.run(['git','add','--','report/handoff-dieu-phoi-2026-10-18.md'],cwd=ROOT,check=True)
subprocess.run(['git','commit','-m','docs(coord): reserve round five acceptance window; local only','--','report/handoff-dieu-phoi-2026-10-18.md'],cwd=ROOT,check=True)
print(json.dumps({'workers':heads,'main_window':output('git','rev-parse','main'),'push':False}))
