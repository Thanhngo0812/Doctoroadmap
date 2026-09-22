import os, random, statistics
from collections import Counter
import networkx as nx
D=os.path.dirname(os.path.abspath(__file__))
def rd(p): return open(os.path.join(D,"ds",p),encoding="utf-8",errors="replace").read()

def run(name, G, trials_target=300, seed=5):
    base=set(nx.transitive_reduction(G).edges())
    nl=list(G.nodes()); random.seed(seed)
    losses=[]; t=0; guard=0
    while t<trials_target and guard<200000:
        guard+=1
        a,b=random.sample(nl,2)
        if G.has_edge(a,b): continue
        H=G.copy(); H.add_edge(a,b)
        if not nx.is_directed_acyclic_graph(H): continue
        t+=1
        tr=set(nx.transitive_reduction(H).edges())
        losses.append(len(base-tr))
    c=sum(1 for x in losses if x>0)
    print("%-24s n=%-5d m=%-5d (%.2f canh/node) | TR giu %d canh (-%.0f%%)"%(
        name,G.number_of_nodes(),G.number_of_edges(),G.number_of_edges()/G.number_of_nodes(),
        len(base),100*(G.number_of_edges()-len(base))/G.number_of_edges()))
    print("    1 canh sai -> mat canh dung: %d/%d lan = %.1f%% | TB khi mat %.2f | toi da %d | phan bo %s"%(
        c,len(losses),100*c/len(losses),
        (statistics.mean([x for x in losses if x>0]) if c else 0), max(losses),
        dict(sorted(Counter(losses).items()))))
    print()

print("=== Thiet hai cua MOT canh sai len rut gon bac cau, theo mat do do thi ===\n")
B="https://raw.githubusercontent.com/harrylclc/AL-CPL-dataset/master/data/"
for d in ["geometry","physics","precalculus","data_mining"]:
    pre=[l.split(",") for l in rd(d+".preqs").strip().split("\n") if l.strip()]
    allp=[l.split(",") for l in rd(d+".pairs").strip().split("\n") if l.strip()]
    G=nx.DiGraph(); G.add_nodes_from({x.strip() for r in allp for x in r[:2]})
    G.add_edges_from({(r[0].strip(),r[1].strip()) for r in pre})
    run("AL-CPL "+d, G)

# LectureBank: make it a DAG first by removing edges in nontrivial SCCs, then test
edges=set()
for part in ["train_edges_positive_0.txt","test_edges_positive_0.txt"]:
    for l in rd(part).strip().split("\n"):
        p=l.strip().replace(","," ").split()
        if len(p)>=2: edges.add((p[0],p[1]))
G=nx.DiGraph(); G.add_nodes_from(str(i) for i in range(322)); G.add_edges_from(edges)
H=G.copy()
while not nx.is_directed_acyclic_graph(H):
    cyc=nx.find_cycle(H); H.remove_edge(*cyc[0][:2])
run("LectureBank2.0 (da DAG-hoa)", H)
