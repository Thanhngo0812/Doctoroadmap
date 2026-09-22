import csv, os, re
import networkx as nx
D = os.path.dirname(os.path.abspath(__file__))

# ---------- CUT (Cyprus University of Technology) ----------
txt = open(os.path.join(D,"CUT_Courses.txt"), encoding="utf-8", errors="replace").read()
# lines look like: "Pre Req. ABF_211 (ABF_104)"  -> course ABF_211 requires ABF_104
edges=set(); nodes=set()
pat = re.compile(r"Pre Req\.\s*([A-Za-z0-9_\-]+)\s*\(([^)]*)\)")
for m in pat.finditer(txt):
    course, pres = m.group(1).strip(), m.group(2)
    nodes.add(course)
    for p in re.split(r"[,\s]+", pres):
        p=p.strip()
        if p:
            nodes.add(p); edges.add((p,course))
G=nx.DiGraph(); G.add_nodes_from(nodes); G.add_edges_from(edges)
touched={a for a,b in edges}|{b for a,b in edges}
print("=== CUT (from CUT_Courses.txt; file lists ONLY courses that have prereqs) ===")
print("nodes appearing:", G.number_of_nodes(), "edges:", G.number_of_edges())
print("edges/node: %.3f" % (G.number_of_edges()/G.number_of_nodes()))
print("isolated:", len(nodes-touched))
print("is DAG:", nx.is_directed_acyclic_graph(G))
two=sum(1 for a,b in edges if (b,a) in edges)//2
print("2-cycle pairs:", two)
sccs=[c for c in nx.strongly_connected_components(G) if len(c)>1]
print("nontrivial SCCs:", len(sccs), sorted(len(c) for c in sccs)[:20])
if nx.is_directed_acyclic_graph(G):
    tr=nx.transitive_reduction(G); print("after TR edges:", tr.number_of_edges())
print("NOTE: paper Table I reports CUT n=416, m=319 after TR -> isolated fraction needs full catalog (this file has only prereq lines)")

# ---------- JHU ----------
rows=list(csv.DictReader(open(os.path.join(D,"JHU_Courses.csv"), encoding="utf-8-sig", errors="replace")))
print()
print("=== JHU ===")
print("catalog rows (courses):", len(rows), "cols:", list(rows[0].keys()))
has = sum(1 for r in rows if (r.get("Pre Req") or "").strip())
print("courses WITH a non-empty prerequisite text:", has, "= %.1f%%" % (100*has/len(rows)))
print("courses WITHOUT any prerequisite text     :", len(rows)-has, "= %.1f%%" % (100*(len(rows)-has)/len(rows)))
# extract course codes like AS.440.011 from prereq text
code=re.compile(r"\b[A-Z]{2}\.\d{3}\.\d{3}\b")
catalog={ (r["Course"] or "").strip() for r in rows if (r.get("Course") or "").strip()}
e=set()
for r in rows:
    c=(r.get("Course") or "").strip()
    if not c: continue
    for p in code.findall(r.get("Pre Req") or ""):
        if p!=c: e.add((p,c))
Gj=nx.DiGraph(); Gj.add_nodes_from(catalog); Gj.add_edges_from(e)
t={a for a,b in e}|{b for a,b in e}
print("my naive-parse: nodes(catalog)=%d edges=%d edges/node=%.3f" % (len(catalog), len(e), len(e)/len(catalog)))
print("isolated (catalog nodes untouched by any parsed edge):", len(catalog-t), "= %.1f%%" % (100*len(catalog-t)/len(catalog)))
print("is DAG:", nx.is_directed_acyclic_graph(Gj))
two=sum(1 for a,b in e if (b,a) in e)//2
print("2-cycle pairs:", two, "-> %.2f%% of edges sit in a 2-cycle" % (100*2*two/max(1,len(e))))
sccs=[c for c in nx.strongly_connected_components(Gj) if len(c)>1]
print("nontrivial SCCs:", len(sccs), "sizes:", sorted((len(c) for c in sccs), reverse=True)[:15])
print("paper Table I: JHU n=10291 m=3499 after TR -> %.3f edges/node" % (3499/10291))
print("  => lower bound on isolated nodes if m=3499: >= %d = %.1f%%" % (10291-2*3499, 100*(10291-2*3499)/10291))
