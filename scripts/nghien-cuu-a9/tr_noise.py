import csv, os, random, statistics
import networkx as nx
D=os.path.dirname(os.path.abspath(__file__))
rows=list(csv.DictReader(open(os.path.join(D,"2021-22-course-prereqs_-_clean.csv"),encoding="utf-8-sig")))
nodes=set(); edges=set()
for r in rows:
    n=(r["Node_name"] or "").strip()
    if not n: continue
    nodes.add(n)
    for p in [x.strip() for x in (r["Preaquisites (clean)"] if "Preaquisites (clean)" in r else r["Prereaquisites (clean)"] or "").split(",")]:
        if p: edges.add((p,n))
G=nx.DiGraph(); G.add_nodes_from(nodes); G.add_edges_from(edges)
base=nx.transitive_reduction(G)
base_e=set(base.edges())
print("=== Caltech CPN: do thi goc %d node / %d canh; rut gon bac cau -> %d canh ==="%(G.number_of_nodes(),G.number_of_edges(),len(base_e)))
print()
print("THI NGHIEM: them DUNG MOT canh sai (ngau nhien, giu tinh phi chu trinh), do xem")
print("rut gon bac cau lam MAT bao nhieu canh dung so voi khi khong co canh sai.\n")
random.seed(11)
losses=[]; trials=0; nl=list(nodes)
while trials<400:
    a,b=random.sample(nl,2)
    if G.has_edge(a,b) or G.has_edge(b,a): continue
    H=G.copy(); H.add_edge(a,b)
    if not nx.is_directed_acyclic_graph(H): continue
    trials+=1
    tr=set(nx.transitive_reduction(H).edges())
    lost=len(base_e-tr)                      # canh dung bien mat khoi ket qua
    losses.append(lost)
c=sum(1 for x in losses if x>0)
print("  So lan thu                       : %d"%len(losses))
print("  So lan canh sai lam MAT canh dung: %d (%.1f%%)"%(c,100*c/len(losses)))
print("  Mat trung binh (tat ca lan)      : %.2f canh dung"%statistics.mean(losses))
print("  Mat trung binh (khi co mat)      : %.2f canh dung"%(statistics.mean([x for x in losses if x>0]) if c else 0))
print("  Mat toi da quan sat duoc         : %d canh dung tu MOT canh sai"%max(losses))
from collections import Counter
print("  Phan bo so canh dung bi mat      : %s"%dict(sorted(Counter(losses).items())))
print()
print("KIEM CHUNG NGUOC: neu chi DANH DAU (redundant_via) thay vi XOA, khong canh dung nao mat,")
print("vi do thi goc van con nguyen; nguoi duyet go canh sai xong thi canh truc tiep van o do.")
print()
# how many edges does TR remove on a real graph
print("Ti le canh bi rut gon bac cau loai bo tren Caltech: %d/%d = %.1f%%"%(G.number_of_edges()-len(base_e),G.number_of_edges(),100*(G.number_of_edges()-len(base_e))/G.number_of_edges()))
