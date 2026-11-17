"""
test_bfs.py - PACOTE P2 (testes obrigatorios, pytest).
networkx pode ser usado AQUI dentro, como oraculo para conferir os resultados.
"""

from src.graphs.algorithms import bfs


# [IA] Claude – sugestão do caso de teste (grafo e respostas esperadas), conferido à mão pelo grupo
grafo_teste = {
    "A": [("B", 1), ("C", 1)],
    "B": [("D", 1)],
    "C": [("D", 1), ("E", 1)],
    "D": [("F", 1)],
    "E": [],
    "F": [],
}


def test_distancias():
    distancias, pais = bfs(grafo_teste, "A")
    assert distancias == {"A": 0, "B": 1, "C": 1, "D": 2, "E": 2, "F": 3}


def test_pais():
    distancias, pais = bfs(grafo_teste, "A")
    assert pais == {"A": None, "B": "A", "C": "A", "D": "B", "E": "C", "F": "D"}