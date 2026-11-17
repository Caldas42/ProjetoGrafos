"""
test_io.py - PACOTE P1. Validacao dos mapas.
"""

import pytest

# [IA] Claude – sugestao dos casos de teste (mapas invalidos), conferidos pelo grupo

from src.graphs.io import ler_mapa, obter_custo, validar_mapa, achar_inicio, \
    achar_saida, achar_chaves, achar_portas, achar_bonus


def grade(linhas):
    return [list(l) for l in linhas]


def test_custos_da_tabela():
    assert obter_custo(".") == 1
    assert obter_custo("S") == 1
    assert obter_custo("G") == 1
    assert obter_custo(",") == 3
    assert obter_custo("~") == 5
    assert obter_custo("+") == -4
    assert obter_custo("*") == -2


def test_custo_de_chave_porta_e_esteira_e_um():
    for simbolo in "abcdABCD><^v":
        assert obter_custo(simbolo) == 1


def test_mapa_valido_passa():
    validar_mapa(grade(["#####", "#S.G#", "#####"]))


def test_mapa_nao_retangular():
    with pytest.raises(ValueError, match="retangular"):
        validar_mapa(grade(["#####", "#S.G#", "####"]))


def test_dois_inicios():
    with pytest.raises(ValueError, match="S"):
        validar_mapa(grade(["#####", "#SSG#", "#####"]))


def test_nenhum_inicio():
    with pytest.raises(ValueError, match="S"):
        validar_mapa(grade(["#####", "#..G#", "#####"]))


def test_nenhuma_saida():
    with pytest.raises(ValueError, match="G"):
        validar_mapa(grade(["#####", "#S..#", "#####"]))


def test_simbolo_desconhecido():
    with pytest.raises(ValueError, match="inv"):
        validar_mapa(grade(["#####", "#SzG#", "#####"]))


def test_mapa_vazio():
    with pytest.raises(ValueError):
        validar_mapa([])


def test_ler_mapa_devolve_grade_de_caracteres(tmp_path):
    arquivo = tmp_path / "m.txt"
    arquivo.write_text("#####\n#S.G#\n#####\n", encoding="utf-8")
    g = ler_mapa(str(arquivo))
    assert len(g) == 3
    assert g[1][1] == "S"
    assert g[1][3] == "G"
    assert all(len(linha) == 5 for linha in g)


def test_ler_mapa_ignora_comentarios(tmp_path):
    arquivo = tmp_path / "c.txt"
    arquivo.write_text("; comentario\n#####\n#S.G#\n; outro\n#####\n", encoding="utf-8")
    g = ler_mapa(str(arquivo))
    assert len(g) == 3
    assert g[0] == list("#####")


def test_ler_mapa_recusa_arquivo_invalido(tmp_path):
    arquivo = tmp_path / "ruim.txt"
    arquivo.write_text("#####\n#S.G#\n####\n", encoding="utf-8")
    with pytest.raises(ValueError):
        ler_mapa(str(arquivo))


def test_catalogos():
    g = grade(["######", "#SaA.#", "#.+bG#", "######"])
    assert achar_inicio(g) == (1, 1)
    assert achar_saida(g) == [(2, 4)]
    assert achar_chaves(g) == {"a": (1, 2), "b": (2, 3)}
    assert achar_portas(g) == {"A": [(1, 3)]}
    assert achar_bonus(g) == {(2, 2): 0}


def test_bonus_numerados_em_ordem_de_leitura():
    g = grade(["#######", "#S.+.+#", "#+...G#", "#######"])
    assert achar_bonus(g) == {(1, 3): 0, (1, 5): 1, (2, 1): 2}


def test_fonte_nao_entra_no_catalogo_de_bonus():
    g = grade(["######", "#S.*.#", "#...G#", "######"])
    assert achar_bonus(g) == {}
