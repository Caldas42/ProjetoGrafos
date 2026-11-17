"""
test_dfs.py - PACOTE P2. DFS em grafo dirigido.
"""

import pytest

# [IA] Claude – sugestao dos casos de teste (grafos e respostas esperadas), conferidos pelo grupo

from src.graphs import algorithms


grafo_com_ciclo = {
    "A": [("B", 1)],
    "B": [("C", 1)],
    "C": [("A", 1)],
}

grafo_sem_ciclo = {
    "A": [("B", 1), ("C", 1)],
    "B": [("D", 1)],
    "C": [("D", 1)],
    "D": [],
}


def test_visita_todos_os_alcancaveis():
    estado, _, _ = algorithms.dfs(grafo_sem_ciclo, "A")
    assert all(v == "ENCERRADO" for v in estado.values())


def test_arvore_de_pais_coerente():
    _, pais, _ = algorithms.dfs(grafo_sem_ciclo, "A")
    assert pais["A"] is None
    assert pais["B"] == "A"
    assert pais["C"] == "A"
    assert pais["D"] in ("B", "C")


def test_tempos_sao_distintos():
    _, _, t = algorithms.dfs(grafo_sem_ciclo, "A")
    assert len(set(t.values())) == len(t)


def test_respeita_a_ordem_da_lista_de_adjacencia():
    _, _, t = algorithms.dfs(grafo_sem_ciclo, "A")
    assert t["B"] < t["C"]


@pytest.mark.skipif(
    not hasattr(algorithms, "classificar_arcos"),
    reason="classificar_arcos() ainda nao existe em algorithms.py",
)
def test_classificacao_de_arcos():
    arcos = algorithms.classificar_arcos(grafo_sem_ciclo, "A")
    tipos = {(u, v): tipo for u, v, tipo in arcos}
    assert tipos[("A", "B")] == "arvore"
    assert tipos[("A", "C")] == "arvore"
    assert "cruzamento" in tipos.values() or "avanco" in tipos.values()


@pytest.mark.skipif(
    not hasattr(algorithms, "classificar_arcos"),
    reason="classificar_arcos() ainda nao existe em algorithms.py",
)
def test_arco_de_retorno_indica_ciclo():
    arcos = algorithms.classificar_arcos(grafo_com_ciclo, "A")
    assert any(tipo == "retorno" for _, _, tipo in arcos)
