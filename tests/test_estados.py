"""
test_estados.py - PACOTE P1. Construcao do grafo de estados.
"""

import pytest

# [IA] Claude – sugestao dos casos de teste, conferidos pelo grupo

from src.graphs import graph as gr
from src.graphs.estados import ALVO, construir_g_est, estado_inicial, rotular, teto_teorico


def grade(linhas):
    return [list(l) for l in linhas]


MAPA_MINIMO = ["#####", "#SaG#", "#####"]

ESTADOS_A_MAO = 4
ARCOS_A_MAO = 4


def test_bate_com_o_calculo_a_mao():
    g = construir_g_est(grade(MAPA_MINIMO))

    sem_alvo = gr.subgrafo_induzido(
        g, [e for e in g if e != ALVO]
    )

    assert gr.ordem(sem_alvo) == ESTADOS_A_MAO
    assert gr.tamanho(sem_alvo) == ARCOS_A_MAO

    assert gr.ordem(g) == ESTADOS_A_MAO + 1
    assert gr.tamanho(g) == ARCOS_A_MAO + 1


def test_estado_inicial_sem_chaves_e_sem_bonus():
    e = estado_inicial(grade(MAPA_MINIMO))
    assert rotular(e) == "(1,1)|-|{}"


def test_rotulo_no_formato_exigido():
    assert rotular((3, 5, "ab", frozenset({0, 2}))) == "(3,5)|ab|{0,2}"
    assert rotular((1, 1, "", frozenset())) == "(1,1)|-|{}"


def test_coletar_chave_muda_de_camada():
    g = construir_g_est(grade(MAPA_MINIMO))
    camadas = {e[2] for e in g if e != ALVO}
    assert camadas == {"", "a"}
    trocas = [(a, b) for a, viz in g.items() if a != ALVO
              for b, _ in viz if b != ALVO and b[2] != a[2]]
    assert len(trocas) == 1


def test_mesma_casa_vira_estados_diferentes():
    g = construir_g_est(grade(MAPA_MINIMO))
    na_casa_do_inicio = [e for e in g if e != ALVO and (e[0], e[1]) == (1, 1)]
    assert len(na_casa_do_inicio) == 2


def test_porta_e_parede_sem_a_chave():
    sem = construir_g_est(grade(["#######", "#S.A.G#", "#######"]))
    assert all(e[1] < 3 for e in sem if e != ALVO)


def test_porta_abre_com_a_chave():
    com = construir_g_est(grade(["#######", "#SaA.G#", "#######"]))
    assert any(e[1] == 5 for e in com if e != ALVO)


def test_esteira_apontando_para_parede_gera_estado_sem_saida():
    g = construir_g_est(grade(["#####", "#S^.#", "#..G#", "#####"]))
    presos = [e for e in g if e != ALVO and not g[e] and (e[0], e[1]) == (1, 2)]
    assert presos


def test_estado_em_g_so_aponta_para_o_alvo():
    g = construir_g_est(grade(MAPA_MINIMO))
    for e, viz in g.items():
        if e != ALVO and (e[0], e[1]) == (1, 3):
            assert viz == [(ALVO, 0)]


def test_alvo_existe_como_chave_do_grafo():
    g = construir_g_est(grade(MAPA_MINIMO))
    assert ALVO in g and g[ALVO] == []


def test_fonte_nao_entra_no_estado():
    g = construir_g_est(grade(["######", "#S*.G#", "######"]))
    assert all(e[3] == frozenset() for e in g if e != ALVO)


def test_bonus_entra_no_estado():
    g = construir_g_est(grade(["######", "#S+.G#", "######"]))
    assert any(e[3] for e in g if e != ALVO)


def test_teto_teorico():
    g = grade(MAPA_MINIMO)
    assert teto_teorico(g) == 3 * 2 ** 1 * 2 ** 0
