import random

from jogo.grafos import (G1, G2, caminho, conectado, dijkstra, sem, sortear_arestas, sortear_nos,
                         tsp_forca_bruta, tsp_heuristico)

# Grafo 1: ciclo ótimo 1-2-3-5-4-1 = 2+4+3+3+3 = 15
rota, custo, testadas = tsp_forca_bruta(G1, 1)
assert custo == 15, custo
assert rota in ([1, 2, 3, 5, 4, 1], [1, 4, 5, 3, 2, 1]), rota

# Dijkstra no grafo 1 a partir do nó 1
dist, ant, _ = dijkstra(G1, 1)
assert dist == {1: 0, 2: 2, 3: 6, 4: 3, 5: 6}, dist

# Grafo 2 a partir do abrigo (nó 1)
dist, ant, passos = dijkstra(G2, 1)
assert dist[2] == 20 and dist[8] == 29 and dist[13] == 37 and dist[3] == 45
assert dist[16] == 56 and caminho(ant, 16) == [1, 13, 16]
assert len(passos) == 18

# TSP heurístico: visita todos os 18 e volta ao 1
ordem, custo2, expandida = tsp_heuristico(G2, 1)
assert sorted(ordem[:-1]) == list(range(1, 19)) and ordem[0] == ordem[-1] == 1
assert all(b in G2[a] for a, b in zip(expandida, expandida[1:]))
# Zumbis bloqueando: sem o nó 13, o caminho até o 16 desvia (1-12-16 = 72)
g = sem(G2, nos={13})
assert 13 not in g and all(13 not in viz for viz in g.values())
dist, ant, _ = dijkstra(g, 1)
assert dist[16] == 72 and caminho(ant, 16) == [1, 12, 16]
# Zumbis na estrada 3-5 do grafo 1: o ciclo ótimo muda
rota, custo, _ = tsp_forca_bruta(sem(G1, arestas=[(3, 5)]), 1)
assert custo == 22 and rota in ([1, 2, 3, 4, 5, 1], [1, 5, 4, 3, 2, 1]), (rota, custo)
# Sorteio dos zumbis: nunca desconecta o grafo nem impede o ciclo
rng = random.Random(1)
for _ in range(50):
    bloq = sortear_nos(G2, 1, 4, rng)
    assert 1 not in bloq and len(bloq) == 4 and conectado(sem(G2, nos=bloq), 1)
    arestas = sortear_arestas(G1, 1, 1, rng, ciclo=True)
    assert tsp_forca_bruta(sem(G1, arestas=arestas), 1)[0]
    assert conectado(sem(G2, arestas=sortear_arestas(G2, 1, 3, rng)), 1)
assert not conectado(sem(G1, nos={2, 4, 5}), 1)
print("OK — todos os testes passaram. TSP grafo 2 (heurístico):", custo2)
