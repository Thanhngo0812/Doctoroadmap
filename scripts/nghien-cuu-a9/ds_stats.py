import urllib.request, os, csv, io
import networkx as nx
D=os.path.dirname(os.path.abspath(__file__)); os.makedirs(os.path.join(D,"ds"),exist_ok=True)
def get(url):
    p=os.path.join(D,"ds",url.split("/")[-1].replace("%20","_"))
    if not os.path.exists(p):
        req=urllib.request.Request(url, headers={"User-Agent":"research"})
        open(p,"wb").write(urllib.request.urlopen(req,timeout=90).read())
    return open(p,encoding="utf-8",errors="replace").read()

def report(name, nodes, edges):
    G=nx.DiGraph(); G.add_nodes_from(nodes); G.add_edges_from(edges)
    n=G.number_of_nodes(); m=G.number_of_edges()
    touched={a for a,b in edges}|{b for a,b in edges}
    iso=n-len(touched)
    two=sum(1 for a,b in edges if (b,a) in edges)//2
    sccs=[c for c in nx.strongly_connected_components(G) if len(c)>1]
    dag=nx.is_directed_acyclic_graph(G)
    tr=""
    if dag:
        t=nx.transitive_reduction(G)
        tr="| TR: %d canh (-%.1f%%), %.2f canh/node"%(t.number_of_edges(),100*(m-t.number_of_edges())/m, t.number_of_edges()/n)
    print("%-26s n=%-6d m=%-6d canh/node=%-6.2f coLap=%-4d(%5.1f%%) 2chieu=%-4d(%.2f%% canh) SCC>1=%-3d DAG=%-5s %s"
          %(name,n,m,m/n,iso,100*iso/n,two,100*2*two/max(1,m),len(sccs),dag,tr))
    if sccs:
        print("%-26s   kich thuoc SCC: %s"%("",sorted((len(c) for c in sccs),reverse=True)[:12]))

print("=== AL-CPL (Liang et al., EAAI 2018) — .preqs = cap tien quyet duong ===")
B="https://raw.githubusercontent.com/harrylclc/AL-CPL-dataset/master/data/"
for d in ["data_mining","geometry","physics","precalculus"]:
    pre=[l.split(",") for l in get(B+d+".preqs").strip().split("\n") if l.strip()]
    allp=[l.split(",") for l in get(B+d+".pairs").strip().split("\n") if l.strip()]
    nodes={x.strip() for r in allp for x in r[:2]}
    edges={(r[0].strip(),r[1].strip()) for r in pre}
    report("AL-CPL "+d, nodes, edges)

print()
print("=== LectureBank 2.0 (Li et al.) — hop train+test positive edges ===")
LB="https://raw.githubusercontent.com/Yale-LILY/LectureBank/master/LB-Paper/LectureBank2/data/split/"
edges=set()
for part in ["train_edges_positive_0.txt","test_edges_positive_0.txt"]:
    for l in get(LB+part).strip().split("\n"):
        l=l.strip().replace(",", " ")
        if not l: continue
        p=l.split()
        if len(p)>=2: edges.add((p[0],p[1]))
topics=get("https://raw.githubusercontent.com/Yale-LILY/LectureBank/master/LB-Paper/LectureBank2/data/322topics_final.tsv")
nodes={str(i) for i in range(len(topics.strip().split("\n")))}
print("   (so chu de trong 322topics_final.tsv: %d)"%len(topics.strip().split("\n")))
report("LectureBank2.0 NLP", nodes|{a for a,b in edges}|{b for a,b in edges}, edges)

print()
print("=== LectureBankCD (cross-domain: NLP / CV / BIO) ===")
CD="https://raw.githubusercontent.com/Yale-LILY/LectureBank/master/LB-Paper/LectureBankCD/BenchmarkData/"
for dom in ["NLP","CV","BIO"]:
    e=set(); nodes=set()
    for f in ["train.0.csv","val.0.csv","test.0.csv"]:
        try: txt=get(CD+dom+"/"+f)
        except Exception as ex: print("  skip",dom,f,ex); continue
        for l in txt.strip().split("\n"):
            p=[x.strip() for x in l.replace("\t",",").split(",")]
            if len(p)>=3:
                nodes.add(p[0]); nodes.add(p[1])
                if p[2] in ("1","1.0"): e.add((p[0],p[1]))
    if e: report("LectureBankCD "+dom, nodes, e)
