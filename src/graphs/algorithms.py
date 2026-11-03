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
