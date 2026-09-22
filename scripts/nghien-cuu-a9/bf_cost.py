import itertools, math, time, random
import networkx as nx

def brute_force_mfas(G, time_budget=20.0):
    """Exhaustive search: smallest edge subset whose removal makes G acyclic."""
    E = list(G.edges()); m = len(E); t0 = time.time(); tested = 0
    for k in range(m+1):
        for comb in itertools.combinations(range(m), k):
            tested += 1
            H = G.copy(); H.remove_edges_from([E[i] for i in comb])
            if nx.is_directed_acyclic_graph(H):
                return k, tested, time.time()-t0, True
            if time.time()-t0 > time_budget:
                return None, tested, time.time()-t0, False
    return None, tested, time.time()-t0, False

print("=== Chi phi vet can theo kich thuoc SCC (do thi ngau nhien, chi lay SCC khong tam thuong) ===")
print(f"{'n':>4} {'m':>5} {'#simple cycles':>15} {'|MFAS|':>7} {'subsets tested':>15} {'time(s)':>9} {'done':>5}")
random.seed(7)
for n in [5,6,7,8,9,10,12,14,16,20]:
    p = 0.35
    for attempt in range(60):
        G = nx.gnp_random_graph(n, p, seed=random.randint(0,10**6), directed=True)
        sccs = [c for c in nx.strongly_connected_components(G) if len(c)>1]
        if not sccs: continue
        S = G.subgraph(max(sccs, key=len)).copy()
        if S.number_of_nodes() < n-1: continue
        break
    else:
        continue
    try:
        ncyc = sum(1 for _ in nx.simple_cycles(S))
    except Exception:
        ncyc = -1
    k, tested, el, done = brute_force_mfas(S, time_budget=20.0)
    print(f"{S.number_of_nodes():>4} {S.number_of_edges():>5} {ncyc:>15} {str(k):>7} {tested:>15} {el:>9.2f} {str(done):>5}")

print()
print("=== So tap con phai duyet trong truong hop xau (2^m) ===")
for m in [10,15,20,25,30,35,40,50]:
    print(f"  m={m:>3} canh -> 2^m = {2**m:>20,}  (o 1 trieu phep thu/giay: {2**m/1e6/3600:>12.3f} gio)")
