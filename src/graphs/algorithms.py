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

def dfs(grafo, v0):
    NAO_VISITADO = "NAO_VISITADO"
    VISITADO = "VISITADO"
    ENCERRADO = "ENCERRADO"

    estado = {v: NAO_VISITADO for v in grafo} #inicializa os vértices
    p = {v: None for v in grafo}   # pai
    t = {}                         # tempo de cada vértice
    tempo = -1

    def visita_vertice(vi):
        nonlocal tempo
        tempo += 1
        estado[vi] = VISITADO
        t[vi] = tempo

        for vj, peso in grafo[vi]:          #visita os filhos
            if estado[vj] == NAO_VISITADO:
                p[vj] = vi
                visita_vertice(vj)

        estado[vi] = ENCERRADO
        tempo += 1

    visita_vertice(v0)
    return estado, p, t


#estado, p, t = dfs(grafo, "A")
#print("estado:", estado)
#print("pai:   ", p)
#print("t:     ", t)


INF = float("inf")

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

    d = {v: float("inf") for v in grafo}
    anterior = {v: None for v in grafo}
    visitado = {v: False for v in grafo}

    d[origem] = 0
    fila = [(0, origem)]  

    while fila:
        dist_u, u = heapq.heappop(fila)

        if visitado[u]:
            continue  
        visitado[u] = True

        for v, peso in grafo[u]:
            if d[v] > d[u] + peso:
                d[v] = d[u] + peso
                anterior[v] = u
                heapq.heappush(fila, (d[v], v))

    return d, anterior