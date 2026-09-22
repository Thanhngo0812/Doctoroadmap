import os, itertools, math
import networkx as nx
D=os.path.dirname(os.path.abspath(__file__))
def get(p):
    return open(os.path.join(D,"ds",p),encoding="utf-8",errors="replace").read()
edges=set()
for part in ["train_edges_positive_0.txt","test_edges_positive_0.txt"]:
    for l in get(part).strip().split("\n"):
        l=l.strip().replace(","," ")
        p=l.split()
        if len(p)>=2: edges.add((p[0],p[1]))
topics=[l.split("\t") for l in get("322topics_final.tsv").strip().split("\n")]
name={}
for r in topics:
    if len(r)>=2: name[r[0].strip()]=r[1].strip()
G=nx.DiGraph(); G.add_nodes_from(str(i) for i in range(322)); G.add_edges_from(edges)
print("LectureBank 2.0: n=%d m=%d"%(G.number_of_nodes(),G.number_of_edges()))
sccs=sorted([c for c in nx.strongly_connected_components(G) if len(c)>1], key=len, reverse=True)
print("So SCC khong tam thuong: %d"%len(sccs))
print()
print("%-6s %-6s %-8s %-22s %s"%("|V|","|E|","2^|E|","vet can kha thi?","ghi chu"))
tot_e=0
for c in sccs:
    S=G.subgraph(c)
    m=S.number_of_edges(); tot_e+=m
    feasible = "CO" if m<=25 else "KHONG"
    note=""
    if m<=22:
        try:
            ncyc=sum(1 for _ in nx.simple_cycles(S)); note="%d chu trinh don"%ncyc
        except Exception: note=""
    else:
        note="qua lon de dem chu trinh"
    print("%-6d %-6d %-8s %-22s %s"%(len(c),m,("2^%d"%m) if m<64 else "huge",feasible,note))
print()
print("Tong canh nam trong SCC khong tam thuong: %d / %d = %.1f%%"%(tot_e,G.number_of_edges(),100*tot_e/G.number_of_edges()))
big=sccs[0]; S=G.subgraph(big)
print()
print("=== SCC LON NHAT: %d node, %d canh ==="%(S.number_of_nodes(),S.number_of_edges()))
print("So tap con canh phai duyet neu vet can: 2^%d = %.3e"%(S.number_of_edges(),2.0**S.number_of_edges()))
print("O toc do 1 trieu phep kiem tra DAG moi giay, can %.3e nam"%(2.0**S.number_of_edges()/1e6/3600/24/365))
try:
    ncyc=0
    for i,_ in enumerate(nx.simple_cycles(S)):
        ncyc+=1
        if ncyc>2_000_000: ncyc=-1; break
    print("So chu trinh don trong SCC lon nhat:", ncyc if ncyc>0 else ">2.000.000 (dung dem)")
except Exception as e: print("dem chu trinh loi:",e)
print()
print("Ten mot so node trong SCC lon nhat:")
print("  ", ", ".join(sorted(name.get(x,x) for x in list(big))[:14]))
# 2-cycles detail
two=[(a,b) for a,b in edges if (b,a) in edges and a<b]
print()
print("So cap 2 chieu (A<->B): %d  -> %d canh = %.2f%% cua %d canh"%(len(two),2*len(two),100*2*len(two)/G.number_of_edges(),G.number_of_edges()))
print("Vi du cap 2 chieu:")
for a,b in two[:8]: print("   %s  <->  %s"%(name.get(a,a),name.get(b,b)))
# what if we only cut 2-cycles - is the rest a DAG?
H=G.copy(); H.remove_edges_from([(a,b) for a,b in edges if (b,a) in edges])
print()
print("Neu GO HET canh nam trong 2-chu-trinh: con DAG khong? ->", nx.is_directed_acyclic_graph(H))
rest=[c for c in nx.strongly_connected_components(H) if len(c)>1]
print("   SCC con lai:",len(rest),"kich thuoc:",sorted((len(c) for c in rest),reverse=True)[:10])
# what if we KEEP 2-cycles (project design) - what remains cyclic?
print()
print("THIET KE DU AN: giu 2-chu-trinh, vet can cac SCC con lai.")
K=G.copy()
# collapse: treat 2-cycles as kept; find SCCs ignoring nothing -> same as before
print("   -> SCC phai vet can van la:",[len(c) for c in sccs[:6]],"... canh:",[G.subgraph(c).number_of_edges() for c in sccs[:6]])
