def construir_grafo(arestas):
    grafo = {}

    for origem, destino, peso, timestamp in arestas:
        if origem not in grafo:
            grafo[origem] = []

        if destino not in grafo:
            grafo[destino] = []

        grafo[origem].append((destino, peso))

    return grafo