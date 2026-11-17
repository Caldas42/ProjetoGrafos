"""
test_bellman_ford.py - PACOTE P2.
"""

# [IA] Claude – sugestao dos casos de teste (grafos e respostas esperadas), conferidos pelo grupo

from src.graphs.algorithms import bellman_ford


def test_peso_negativo_sem_ciclo_negativo():
    g = {
        "A": [("B", 4), ("C", 5)],
        "B": [("D", 3)],
        "C": [("B", -2), ("D", 6)],
        "D": [],
    }
    d, _, ciclo = bellman_ford(g, "A")
    assert ciclo is None
    assert d == {"A": 0, "B": 3, "C": 5, "D": 6}


def test_usa_a_aresta_negativa_quando_compensa():
    g = {"A": [("B", 4), ("C", 5)], "B": [("D", 3)], "C": [("B", -2)], "D": []}
    d, pais, _ = bellman_ford(g, "A")
    assert pais["B"] == "C"


def test_detecta_ciclo_negativo():
    g = {
        "A": [("B", 1)],
        "B": [("C", 1)],
        "C": [("B", -5)],
    }
    _, _, ciclo = bellman_ford(g, "A")
    assert ciclo is not None


def test_ciclo_devolvido_e_mesmo_um_ciclo_e_soma_negativa():
    g = {"A": [("B", 1)], "B": [("C", 1)], "C": [("B", -5)]}
    _, _, ciclo = bellman_ford(g, "A")
    assert ciclo[0] == ciclo[-1]
    peso = {(u, v): p for u in g for v, p in g[u]}
    soma = sum(peso[(ciclo[i], ciclo[i + 1])] for i in range(len(ciclo) - 1))
    assert soma < 0


def test_vertice_inalcancavel_fica_infinito():
    g = {"A": [("B", 1)], "B": [], "Z": []}
    d, _, _ = bellman_ford(g, "A")
    assert d["Z"] == float("inf")
