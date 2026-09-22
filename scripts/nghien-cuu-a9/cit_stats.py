import csv, os, re, itertools
D = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(D,"2021-22-course-prereqs_-_clean.csv"), encoding="utf-8-sig")))
print("CSV rows:", len(rows), "| cols:", list(rows[0].keys()))
nodes = set(); edges = set()
pcol = [c for c in rows[0] if c.lower().startswith("prerea") or c.lower().startswith("prereq") and "clean" in c.lower()]
pcol = "Prereaquisites (clean)"
for r in rows:
    n = (r["Node_name"] or "").strip()
    if not n: continue
    nodes.add(n)
for r in rows:
    n = (r["Node_name"] or "").strip()
    if not n: continue
    pre = (r[pcol] or "").strip()
    if not pre: continue
    for p in [x.strip() for x in pre.split(",")]:
        if p:
            edges.add((p, n))
allnodes = nodes | {a for a,b in edges} | {b for a,b in edges}
touched = {a for a,b in edges} | {b for a,b in edges}
print("--- CIT (Caltech) raw graph from catalog ---")
print("nodes listed in catalog :", len(nodes))
print("nodes incl. prereq-only :", len(allnodes))
print("edges                   :", len(edges))
print("edges/node (catalog)    : %.3f" % (len(edges)/len(nodes)))
print("edges/node (all nodes)  : %.3f" % (len(edges)/len(allnodes)))
iso_cat = len(nodes - touched)
print("isolated (catalog nodes):", iso_cat, "= %.1f%%" % (100*iso_cat/len(nodes)))
iso_all = len(allnodes - touched)
print("isolated (all nodes)    :", iso_all, "= %.1f%%" % (100*iso_all/len(allnodes)))
try:
    import networkx as nx
    G = nx.DiGraph(); G.add_nodes_from(allnodes); G.add_edges_from(edges)
    sccs = [c for c in nx.strongly_connected_components(G) if len(c) > 1]
    print("nontrivial SCCs         :", len(sccs), "sizes:", sorted(len(c) for c in sccs))
    two = sum(1 for a,b in edges if (b,a) in edges)//2
    print("2-cycles (A<->B) pairs  :", two, "= %.2f%% of edges involved" % (100*2*two/len(edges)))
    print("selfloops               :", nx.number_of_selfloops(G))
    print("is DAG                  :", nx.is_directed_acyclic_graph(G))
    if nx.is_directed_acyclic_graph(G):
        tr = nx.transitive_reduction(G)
        print("edges after transitive reduction:", tr.number_of_edges(),
              "(removed %d = %.1f%%)" % (len(edges)-tr.number_of_edges(), 100*(len(edges)-tr.number_of_edges())/len(edges)))
        print("edges/node after TR     : %.3f" % (tr.number_of_edges()/G.number_of_nodes()))
except ImportError:
    print("networkx not available")
