def construir_grafo(arestas):
    grafo = {}

    for origem, destino, peso, timestamp in arestas:
        if origem not in grafo:
            grafo[origem] = []

        if destino not in grafo:
            grafo[destino] = []

        grafo[origem].append((destino, peso))

    return grafo

# [IA] ChatGPT - reutilizacao da amostragem existente para o front
def selecionar_vertices(grafo):
    from random import Random

    fonte = 7188

    origem_negativa, destino_negativo = next(
        (u, v)
        for u, vizinhos in grafo.items()
        for v, peso in vizinhos
        if peso < 0
    )

    obrigatorios = list(dict.fromkeys([
        fonte, origem_negativa, destino_negativo
    ]))

    restantes = sorted(set(grafo) - set(obrigatorios))
    Random(42).shuffle(restantes)

    return obrigatorios + restantes


def construir_recorte(grafo, percentual, vertices=None):
    if percentual not in (10, 50, 100):
        raise ValueError("Percentual deve ser 10, 50 ou 100.")

    if percentual == 100:
        return grafo

    if vertices is None:
        vertices = selecionar_vertices(grafo)

    quantidade = int(len(grafo) * percentual / 100)
    selecionados = set(vertices[:quantidade])

    return {
        u: [
            (v, peso)
            for v, peso in grafo[u]
            if v in selecionados
        ]
        for u in grafo
        if u in selecionados
    }