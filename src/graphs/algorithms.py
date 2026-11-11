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