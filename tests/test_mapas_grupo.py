"""
test_mapas_grupo.py - PACOTE P3. Confere se os 2 mapas do grupo cumprem
os requisitos da Secao 10 do enunciado.
"""

import glob
import os

import pytest

# [IA] Claude Code - validador dos requisitos da Secao 10 e o mapa g02_porao;
# os valores esperados foram conferidos pelo grupo rodando o proprio codigo

from src.graphs import graph as gr
from src.graphs.algorithms import bellman_ford, bfs, dijkstra
from src.graphs.estados import ALVO, construir_g_est, estado_inicial
from src.graphs.io import ler_mapa

PASTA = "data/mapas_grupo"
MAPA_ATALHO = os.path.join(PASTA, "g01_tres_chaves.txt")
MAPA_PORAO = os.path.join(PASTA, "g02_porao.txt")
INF = float("inf")


def simbolos(grade):
    return {c for linha in grade for c in linha}


def melhor_caminho(grade, grafo):
    inicio = estado_inicial(grade)
    try:
        dist, pais = dijkstra(grafo, inicio)
    except ValueError:
        dist, pais, _ = bellman_ford(grafo, inicio)
    if dist.get(ALVO, INF) == INF:
        return None
    caminho, atual, vistos = [], ALVO, set()
    while atual is not None and atual not in vistos:
        vistos.add(atual)
        caminho.append(atual)
        atual = pais.get(atual)
    caminho.reverse()
    return [e for e in caminho if e != ALVO]


def armadilhas(grafo):
    alcanca = bfs(gr.transposto(grafo), ALVO)[0]
    return [e for e in grafo if e != ALVO and e not in alcanca]


def test_existem_dois_mapas():
    assert len(glob.glob(os.path.join(PASTA, "*.txt"))) >= 2


@pytest.mark.parametrize("caminho", [MAPA_ATALHO, MAPA_PORAO])
def test_mapa_e_valido_e_tem_solucao(caminho):
    grade = ler_mapa(caminho)
    grafo = construir_g_est(grade)
    assert melhor_caminho(grade, grafo) is not None


def test_atalho_tem_tres_chaves_esteiras_e_bonus():
    presentes = simbolos(ler_mapa(MAPA_ATALHO))
    assert len(presentes & set("abcd")) >= 3
    assert presentes & set("><^v")
    assert "+" in presentes


def test_atalho_o_caminho_otimo_usa_bonus_e_esteira():
    grade = ler_mapa(MAPA_ATALHO)
    caminho = melhor_caminho(grade, construir_g_est(grade))
    casas = [grade[e[0]][e[1]] for e in caminho]
    assert "+" in casas
    assert any(c in "><^v" for c in casas)


def test_atalho_o_caminho_otimo_atravessa_uma_porta():
    grade = ler_mapa(MAPA_ATALHO)
    caminho = melhor_caminho(grade, construir_g_est(grade))
    casas = [grade[e[0]][e[1]] for e in caminho]
    assert any(c in "ABCD" for c in casas)


def test_porao_tem_ao_menos_vinte_porcento_de_armadilhas():
    grade = ler_mapa(MAPA_PORAO)
    grafo = construir_g_est(grade)
    estados = [e for e in grafo if e != ALVO]
    presos = armadilhas(grafo)
    assert len(presos) / len(estados) >= 0.20
