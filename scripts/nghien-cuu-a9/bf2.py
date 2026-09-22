import itertools, time, random, sys
import networkx as nx
def bf(G, budget=10.0):
    E=list(G.edges()); m=len(E); t0=time.time(); tested=0
    for k in range(m+1):
        for comb in itertools.combinations(range(m),k):
            tested+=1
            H=G.copy(); H.remove_edges_from([E[i] for i in comb])
            if nx.is_directed_acyclic_graph(H): return k,tested,time.time()-t0,True
            if time.time()-t0>budget: return None,tested,time.time()-t0,False
    return None,tested,time.time()-t0,False
print("SCC: n | m | #chu trinh don | |MFAS| | so tap con da thu | giay | xong?", flush=True)
random.seed(3)
for n in [5,6,7,8,9,10,11,12]:
    G=None
    for _ in range(300):
        C=nx.gnp_random_graph(n,0.4,seed=random.randint(0,10**6),directed=True)
        s=[c for c in nx.strongly_connected_components(C) if len(c)>1]
        if s and len(max(s,key=len))==n: G=C.subgraph(max(s,key=len)).copy(); break
    if G is None: continue
    nc=sum(1 for _ in nx.simple_cycles(G))
    k,t,el,done=bf(G,budget=10.0)
    print(f"  {n:>2} | {G.number_of_edges():>2} | {nc:>6} | {str(k):>4} | {t:>12,} | {el:>6.2f} | {done}", flush=True)
