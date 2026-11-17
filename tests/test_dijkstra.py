"""
test_dijkstra.py - PACOTE P2.
"""

import pytest

# [IA] Claude – sugestao dos casos de teste (grafos e respostas esperadas), conferidos pelo grupo

from src.graphs.algorithms import dijkstra


grafo_simples = {
    "A": [("B", 3), ("C", 1)],
    "B": [("D", 2)],
    "C": [("B", 1)],
    "D": [],
}


def test_distancias_minimas():
    d, _ = dijkstra(grafo_simples, "A")
    assert d == {"A": 0, "B": 2, "C": 1, "D": 4}


def test_escolhe_o_caminho_mais_barato_e_nao_o_mais_curto():
    d, pais = dijkstra(grafo_simples, "A")
    assert pais["B"] == "C"
    assert d["B"] == 2


def test_vertice_inalcancavel_fica_infinito():
    g = {"A": [("B", 1)], "B": [], "Z": []}
    d, _ = dijkstra(g, "A")
    assert d["Z"] == float("inf")


def test_empate_de_distancia_nao_quebra_com_nos_de_tipos_diferentes():
    g = {
        (0, 0): [("ALVO", 1), ((1, 1), 1)],
        (1, 1): [("ALVO", 1)],
        "ALVO": [],
    }
    d, _ = dijkstra(g, (0, 0))
    assert d["ALVO"] == 1


def test_recusa_peso_negativo():
    g = {"A": [("B", -1)], "B": []}
    with pytest.raises(ValueError):
        dijkstra(g, "A")


def test_mensagem_da_recusa_e_clara():
    g = {"A": [("B", -4)], "B": []}
    with pytest.raises(ValueError, match="negativ"):
        dijkstra(g, "A")
