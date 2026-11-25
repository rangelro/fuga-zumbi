"""Grafos da atividade + Dijkstra e Caixeiro Viajante."""
import heapq
import itertools
import math


# ---------------------------------------------------------------- dados

def montar(arestas):
    g = {}
    for a, b, w in arestas:
        g.setdefault(a, {})[b] = w
        g.setdefault(b, {})[a] = w
    return g


# Grafo 1: 5 cidades (suprimentos)
G1 = montar([(1, 2, 2), (1, 4, 3), (1, 5, 6), (2, 3, 4), (2, 4, 3),
             (3, 4, 7), (3, 5, 3), (4, 5, 3)])
POS1 = {1: (75, 212), 2: (181, 137), 3: (275, 212), 4: (122, 307), 5: (225, 307)}

# Grafo 2: 18 bairros da cidade infestada; o nó 1 é o abrigo.
# Pesos lidos da imagem: confira antes da apresentação.
G2 = montar([
    (1, 2, 20), (1, 8, 29), (1, 12, 29), (1, 13, 37), (2, 3, 25), (2, 8, 28),
    (2, 12, 39), (3, 4, 25), (3, 8, 30), (3, 13, 54), (4, 6, 32), (4, 7, 42),
    (4, 9, 23), (4, 10, 33), (4, 5, 39), (6, 7, 17), (6, 5, 12), (6, 10, 35),
    (6, 11, 30), (7, 5, 26), (7, 11, 38), (5, 10, 19), (8, 12, 25), (8, 13, 22),
    (9, 10, 26), (9, 13, 34), (9, 14, 56), (9, 16, 43), (10, 11, 24), (10, 14, 30),
    (10, 15, 19), (11, 15, 26), (11, 18, 36), (12, 13, 27), (12, 16, 43),
    (13, 14, 24), (13, 16, 19), (14, 16, 19), (14, 15, 20), (14, 17, 17),
    (15, 17, 18), (15, 18, 21), (16, 17, 26), (17, 18, 15),
])
POS2 = {1: (393, 220), 2: (413, 157), 3: (493, 140), 4: (580, 130), 5: (684, 180),
        6: (688, 128), 7: (733, 102), 8: (476, 233), 9: (551, 203), 10: (629, 219),
        11: (720, 218), 12: (430, 295), 13: (524, 296), 14: (599, 301),
        15: (654, 268), 16: (557, 344), 17: (645, 335), 18: (698, 326)}


# ---------------------------------------------------------------- algoritmos

def dijkstra(g, origem):
    """Retorna (dist, anterior, passos). passos = [(nó fechado, cópia de dist)]."""
    dist = {v: math.inf for v in g}
    ant = {v: None for v in g}
    dist[origem] = 0
    fila = [(0, origem)]
    fechados = set()
    passos = []
    while fila:
        d, u = heapq.heappop(fila)
        if u in fechados:
            continue
        fechados.add(u)
        for v, w in g[u].items():
            if d + w < dist[v]:
                dist[v] = d + w
                ant[v] = u
                heapq.heappush(fila, (dist[v], v))
        passos.append((u, dict(dist)))
    return dist, ant, passos


def caminho(ant, destino):
    c = []
    while destino is not None:
        c.append(destino)
        destino = ant[destino]
    return c[::-1]


def custo_rota(g, rota):
    return sum(g[a][b] for a, b in zip(rota, rota[1:]))


def tsp_forca_bruta(g, inicio):
    """Testa todas as permutações. Retorna (rota, custo, rotas testadas)."""
    outros = [v for v in g if v != inicio]
    melhor, melhor_custo, testadas = None, math.inf, 0
    for p in itertools.permutations(outros):
        rota = [inicio, *p, inicio]
        if all(b in g[a] for a, b in zip(rota, rota[1:])):
            testadas += 1
            c = custo_rota(g, rota)
            if c < melhor_custo:
                melhor, melhor_custo = rota, c
    return melhor, melhor_custo, testadas


def tsp_heuristico(g, inicio):
    """Grafo incompleto: a matriz de distâncias vem do Dijkstra (todos os pares).
    Depois: vizinho mais próximo + 2-opt.
    ponytail: heurística, pode não ser ótima; Held-Karp (DP O(n²·2ⁿ)) dá o ótimo exato.
    Retorna (ordem de visita, custo, rota expandida em arestas reais)."""
    todos = {u: dijkstra(g, u) for u in g}
    d = {u: todos[u][0] for u in g}

    ordem, livres = [inicio], set(g) - {inicio}
    while livres:
        prox = min(livres, key=lambda v: d[ordem[-1]][v])
        ordem.append(prox)
        livres.remove(prox)
    ordem.append(inicio)

    melhorou = True
    while melhorou:
        melhorou = False
        for i in range(1, len(ordem) - 2):
            for j in range(i + 1, len(ordem) - 1):
                a, b, c, e = ordem[i - 1], ordem[i], ordem[j], ordem[j + 1]
                if d[a][c] + d[b][e] < d[a][b] + d[c][e]:
                    ordem[i:j + 1] = reversed(ordem[i:j + 1])
                    melhorou = True

    custo = sum(d[a][b] for a, b in zip(ordem, ordem[1:]))
    expandida = [inicio]
    for a, b in zip(ordem, ordem[1:]):
        expandida += caminho(todos[a][1], b)[1:]
    return ordem, custo, expandida


def sem(g, nos=(), arestas=()):
    """Cópia do grafo sem os nós e as arestas bloqueados (onde os zumbis estão)."""
    bloq = {frozenset(a) for a in arestas}
    return {u: {v: w for v, w in vs.items() if v not in nos and frozenset((u, v)) not in bloq}
            for u, vs in g.items() if u not in nos}


def conectado(g, origem):
    """True se todos os nós do grafo são alcançáveis a partir da origem."""
    return all(d < math.inf for d in dijkstra(g, origem)[0].values())


def sortear_nos(g, origem, n, rng, proibidos=()):
    """Sorteia n nós para os zumbis sem desconectar o grafo (a partir da origem)."""
    candidatos = [v for v in g if v != origem and v not in proibidos]
    for _ in range(1000):
        bloq = set(rng.sample(candidatos, n))
        if conectado(sem(g, nos=bloq), origem):
            return bloq
    raise ValueError("não achei nós que deixem o grafo conectado")


def sortear_arestas(g, origem, n, rng, ciclo=False):
    """Sorteia n estradas para os zumbis mantendo o grafo conectado (e com ciclo hamiltoniano, se pedido)."""
    arestas = [(a, b) for a in g for b in g[a] if a < b]
    for _ in range(1000):
        bloq = rng.sample(arestas, n)
        h = sem(g, arestas=bloq)
        if conectado(h, origem) and (not ciclo or tsp_forca_bruta(h, origem)[0]):
            return bloq
    raise ValueError("não achei estradas que mantenham uma rota possível")
