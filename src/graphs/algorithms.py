"""
algorithms.py  -  BFS, DFS, Dijkstra e Bellman-Ford. Implementacao propria.

PACOTE P2. NAO PODE SER ESCRITO POR IA (ver DECLARACAO_IA).
Usado nas DUAS partes do projeto (labirintos e dataset maior).

Responsabilidades deste arquivo:
  - BFS   : menor numero de passos + niveis + arvore BFS
  - DFS   : classificacao dos arcos (arvore, retorno, avanco, cruzamento)
            e deteccao de ciclos, respeitando a ordem N, L, S, O
  - DIJKSTRA : menor custo; deve RECUSAR grafo com arco de peso negativo
  - BELLMAN-FORD : menor custo com pesos negativos; detecta e RETORNA o ciclo negativo
  - permitido usar heapq no Dijkstra. Proibido networkx/igraph fora de tests/.
"""

import heapq
from collections import deque

NAO_VISITADO = "NAO_VISITADO"
VISITADO = "VISITADO"
ENCERRADO = "ENCERRADO"


def dfs_completa(grafo, v0):
    estado = {v: NAO_VISITADO for v in grafo}
    pais = {v: None for v in grafo}
    descoberta = {}
    termino = {}
    arcos = []
    tempo = 0

    estado[v0] = VISITADO
    descoberta[v0] = tempo
    tempo += 1
    pilha = [(v0, 0)]

    while pilha:
        u, i = pilha[-1]
        vizinhos = grafo.get(u, [])

        if i < len(vizinhos):
            pilha[-1] = (u, i + 1)
            v, _ = vizinhos[i]
            situacao = estado.get(v, NAO_VISITADO)

            if situacao == NAO_VISITADO:
                arcos.append((u, v, "arvore"))
                pais[v] = u
                estado[v] = VISITADO
                descoberta[v] = tempo
                tempo += 1
                pilha.append((v, 0))
            elif situacao == VISITADO:
                arcos.append((u, v, "retorno"))
            elif descoberta[u] < descoberta[v]:
                arcos.append((u, v, "avanco"))
            else:
                arcos.append((u, v, "cruzamento"))
        else:
            pilha.pop()
            estado[u] = ENCERRADO
            termino[u] = tempo
            tempo += 1

    return estado, pais, descoberta, termino, arcos


def dfs(grafo, v0):
    estado, pais, descoberta, _, _ = dfs_completa(grafo, v0)
    return estado, pais, descoberta


def classificar_arcos(grafo, v0):
    return dfs_completa(grafo, v0)[4]


def tem_ciclo(grafo, v0):
    for _, _, tipo in classificar_arcos(grafo, v0):
        if tipo == "retorno":
            return True
    return False


INF = float("inf")

# [IA] Claude Code – pseudocodigo de referencia e conferencia dos resultados (codigo escrito pelo integrante)
def bellman_ford(grafo, v0):
    d = {}
    p = {}
    for v in grafo:
        d[v] = INF
        p[v] = None
    d[v0] = 0

    n = len(grafo)
    for _ in range(n - 1):
        mudou = False
        for vi in grafo:
            for vj, peso in grafo[vi]:
                if d[vi] != INF and d[vi] + peso < d[vj]:
                    d[vj] = d[vi] + peso
                    p[vj] = vi
                    mudou = True
        if not mudou:
            break

    x = None
    for vi in grafo:
        for vj, peso in grafo[vi]:
            if d[vi] != INF and d[vi] + peso < d[vj]:
                p[vj] = vi
                x = vj
                break
        if x is not None:
            break

    if x is None:
        return d, p, None

    for _ in range(n):
        x = p[x]
    ciclo = [x]
    y = p[x]
    while y != x:
        ciclo.append(y)
        y = p[y]
    ciclo.append(x)
    ciclo.reverse()
    return d, p, ciclo


# grafo = {"A": [("B", 4), ("C", 5)], "B": [("D", 3)], "C": [("B", -2), ("D", 6)], "D": [("E", 2)], "E": []}
# print(bellman_ford(grafo, "A"))

# grafo = {"A": [("B", 4), ("C", 5)], "B": [("D", 3)], "C": [("B", -2), ("D", 6)], "D": [("E", 2)], "E": []}
# d, p, ciclo = bellman_ford(grafo, "A")
# print("distancias:", d)
# print("pai:       ", p)
# print("ciclo:     ", ciclo)

# grafo_ciclo = {"A": [("B", 4), ("C", 5)], "B": [("D", 3)], "C": [("B", -2), ("D", 6)], "D": [("E", 2)], "E": [("C", -10)]}
# print("ciclo negativo:", bellman_ford(grafo_ciclo, "A")[2])

def dijkstra(grafo, origem):
    for u in grafo:
        for v, peso in grafo[u]:
            if peso < 0:
                raise ValueError(
                    f"Dijkstra recusado: o arco {u!r} -> {v!r} tem peso negativo ({peso}). "
                    f"Use o Bellman-Ford para grafos com pesos negativos."
                )

    d = {v: float("inf") for v in grafo}
    anterior = {v: None for v in grafo}
    visitado = {v: False for v in grafo}

    d[origem] = 0
    contador = 0
    fila = [(0, contador, origem)]

    while fila:
        dist_u, _, u = heapq.heappop(fila)

        if visitado[u]:
            continue
        visitado[u] = True

        for v, peso in grafo.get(u, []):
            if d.get(v, float("inf")) > dist_u + peso:
                d[v] = dist_u + peso
                anterior[v] = u
                contador += 1
                heapq.heappush(fila, (d[v], contador, v))
            visitado.setdefault(v, False)

    return d, anterior

def bfs(grafo, inicio):
    distancias = {}
    pais = {}

    distancias[inicio] = 0
    pais[inicio] = None

    fila = deque([inicio])

    while fila:
        atual = fila.popleft()

        for vizinho, peso in grafo[atual]:
            if vizinho not in distancias:
                distancias[vizinho] = distancias[atual] + 1
                pais[vizinho] = atual
                fila.append(vizinho)

    return distancias, pais