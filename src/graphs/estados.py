from collections import deque

from src.graphs.io import (
    CHAVES_VALIDAS,
    PORTAS_VALIDAS,
    achar_bonus,
    achar_inicio,
    obter_custo,
)

ALVO = "ALVO"

DIRECOES = [
    ("N", -1, 0),
    ("L", 0, 1),
    ("S", 1, 0),
    ("O", 0, -1),
]

ESTEIRAS = {
    "^": "N",
    ">": "L",
    "v": "S",
    "<": "O",
}


def dentro_da_grade(grade, l, c):
    return 0 <= l < len(grade) and 0 <= c < len(grade[0])


def pode_entrar(grade, l, c, direcao, chaves="", modo_porta="chave"):
    origem = grade[l][c]
    if origem in ESTEIRAS and ESTEIRAS[origem] != direcao:
        return False

    for nome, dl, dc in DIRECOES:
        if nome == direcao:
            nl, nc = l + dl, c + dc
            break

    if not dentro_da_grade(grade, nl, nc):
        return False

    destino = grade[nl][nc]
    if destino == "#":
        return False

    if destino in PORTAS_VALIDAS:
        if modo_porta == "chao":
            return True
        if modo_porta == "parede":
            return False
        return destino.lower() in chaves

    return True


def vizinho(l, c, direcao):
    for nome, dl, dc in DIRECOES:
        if nome == direcao:
            return l + dl, c + dc


def casas_livres(grade, modo_porta="chave"):
    casas = []
    for l, linha in enumerate(grade):
        for c, valor in enumerate(linha):
            if valor == "#":
                continue
            if valor in PORTAS_VALIDAS and modo_porta == "parede":
                continue
            casas.append((l, c))
    return casas


def construir_g_pos(grade, modo_porta="chao"):
    g = {}
    for l, c in casas_livres(grade, modo_porta):
        g[(l, c)] = []

    for l, c in g:
        if grade[l][c] == "G":
            continue
        for direcao, _, _ in DIRECOES:
            if pode_entrar(grade, l, c, direcao, modo_porta=modo_porta):
                nl, nc = vizinho(l, c, direcao)
                g[(l, c)].append(((nl, nc), obter_custo(grade[nl][nc])))
    return g


def achar_consumiveis(grade, fonte="infinita"):
    consumiveis = dict(achar_bonus(grade))
    if fonte == "consumivel":
        proximo = len(consumiveis)
        for l, linha in enumerate(grade):
            for c, valor in enumerate(linha):
                if valor == "*":
                    consumiveis[(l, c)] = proximo
                    proximo += 1
    return consumiveis


def estado_inicial(grade):
    l, c = achar_inicio(grade)
    return (l, c, "", frozenset())


def proximo_estado(grade, estado, direcao, consumiveis):
    l, c, chaves, bonus = estado
    nl, nc = vizinho(l, c, direcao)
    destino = grade[nl][nc]

    novas_chaves = chaves
    if destino in CHAVES_VALIDAS and destino not in chaves:
        novas_chaves = "".join(sorted(chaves + destino))

    novo_bonus = bonus
    if (nl, nc) in consumiveis:
        indice = consumiveis[(nl, nc)]
        if indice in bonus:
            custo = 1
        else:
            custo = obter_custo(destino)
            novo_bonus = bonus | {indice}
    else:
        custo = obter_custo(destino)

    return (nl, nc, novas_chaves, novo_bonus), custo


def construir_g_est(grade, fonte="infinita"):
    consumiveis = achar_consumiveis(grade, fonte)
    inicio = estado_inicial(grade)

    g = {inicio: []}
    fila = deque([inicio])

    while fila:
        estado = fila.popleft()
        l, c, chaves, _ = estado

        if grade[l][c] == "G":
            g[estado].append((ALVO, 0))
            continue

        for direcao, _, _ in DIRECOES:
            if not pode_entrar(grade, l, c, direcao, chaves):
                continue
            novo, custo = proximo_estado(grade, estado, direcao, consumiveis)
            g[estado].append((novo, custo))
            if novo not in g:
                g[novo] = []
                fila.append(novo)

    g[ALVO] = []
    return g


def rotular(estado):
    if estado == ALVO:
        return ALVO
    if len(estado) == 2:
        l, c = estado
        return f"({l},{c})"
    l, c, chaves, bonus = estado
    texto_chaves = chaves if chaves else "-"
    texto_bonus = "{" + ",".join(str(i) for i in sorted(bonus)) + "}"
    return f"({l},{c})|{texto_chaves}|{texto_bonus}"


def teto_teorico(grade, fonte="infinita"):
    livres = len(casas_livres(grade))
    n_chaves = len({v for linha in grade for v in linha if v in CHAVES_VALIDAS})
    n_bonus = len(achar_consumiveis(grade, fonte))
    return livres * 2 ** n_chaves * 2 ** n_bonus
