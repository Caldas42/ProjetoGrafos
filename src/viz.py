"""
viz.py  -  Visualizacoes e UX do projeto.

PACOTE P5.

Este modulo NAO implementa algoritmo nem constroi grafo: ele consome o que
io.py, estados.py, graph.py e algorithms.py produzem, e so desenha.

Gera out/parte1/labirinto_interativo.html, com:
  - selecao de mapa e de algoritmo
  - animacao passo a passo do percurso (posicao, chaves, bonus, custo acumulado)
  - realce dos estados-armadilha e alternancia entre camadas
  - controle de velocidade e avanco passo a passo

Uso:
    python -m src.viz                      # gera para todos os mapas
    python -m src.viz data/mapas/m03.txt   # gera so para um
"""

import glob
import json
import os
import sys

from src.graphs import graph as gr
from src.graphs.estados import (
    ALVO,
    construir_g_est,
    estado_inicial,
    rotular,
    teto_teorico,
)
from src.graphs.io import ler_mapa

# ----------------------------------------------------------------------
# quais algoritmos do grupo estao disponiveis hoje
# ----------------------------------------------------------------------

ALGORITMOS = {}

try:
    from src.graphs.algorithms import bellman_ford
    ALGORITMOS["BELLMAN_FORD"] = bellman_ford
except ImportError:
    pass

try:
    from src.graphs.algorithms import bfs
    ALGORITMOS["BFS"] = bfs
except ImportError:
    pass

try:
    from src.graphs.algorithms import dijkstra
    ALGORITMOS["DIJKSTRA"] = dijkstra
except ImportError:
    pass

try:
    from src.graphs.algorithms import dfs_distancias
    ALGORITMOS["DFS"] = dfs_distancias
except ImportError:
    pass

def _reconstruir(pais, destino):
    """Caminho do inicio ate `destino`, andando de tras pra frente pelo pai."""
    caminho = []
    atual = destino
    vistos = set()
    while atual is not None and atual not in vistos:
        vistos.add(atual)
        caminho.append(atual)
        atual = pais.get(atual)
    caminho.reverse()
    return caminho


def _rodar(funcao, grafo, inicio):
    """
    Chama um algoritmo do grupo e normaliza a saida.
    Aceita retorno (dist, pai) ou (dist, pai, ciclo_negativo).
    Devolve (dist, pai, ciclo) ou None se o algoritmo nao couber nesse formato.
    """
    try:
        resultado = funcao(grafo, inicio)
    except Exception:
        return None
    if not isinstance(resultado, tuple) or len(resultado) < 2:
        return None
    dist, pai = resultado[0], resultado[1]
    if not isinstance(dist, dict) or not isinstance(pai, dict):
        return None
    ciclo = resultado[2] if len(resultado) > 2 else None
    return dist, pai, ciclo


# ----------------------------------------------------------------------
# coleta dos dados de um mapa
# ----------------------------------------------------------------------

def coletar(caminho_mapa, fonte="infinita"):
    """Monta o dicionario com tudo que a pagina precisa para um mapa."""
    nome = os.path.splitext(os.path.basename(caminho_mapa))[0]
    grade = ler_mapa(caminho_mapa)
    grafo = construir_g_est(grade, fonte=fonte)
    inicio = estado_inicial(grade)

    estados = [e for e in grafo if e != ALVO]

    # camadas: para cada conjunto de chaves, as casas que existem nela
    camadas = {}
    for e in estados:
        camadas.setdefault(e[2] or "-", set()).add((e[0], e[1]))

    # estados-armadilha: no grafo transposto, quem o ALVO nao alcanca.
    # usa o Bellman-Ford do grupo como teste de alcancabilidade.
    armadilhas = []
    if "BELLMAN_FORD" in ALGORITMOS:
        saida = _rodar(ALGORITMOS["BELLMAN_FORD"], gr.transposto(grafo), ALVO)
        if saida is not None:
            dist_re = saida[0]
            inf = float("inf")
            armadilhas = [e for e in estados if dist_re.get(e, inf) == inf]

    # percursos, um por algoritmo disponivel
    percursos = {}
    for apelido, funcao in ALGORITMOS.items():
        # [IA] Claude Code – registrar a recusa do Dijkstra (peso negativo) para a pagina mostrar
        try:
            funcao(grafo, inicio)
        except ValueError as erro:
            percursos[apelido] = {"status": "RECUSA", "passos": [], "custo": None,
                                  "mensagem": str(erro)}
            continue
        except Exception:
            pass
        saida = _rodar(funcao, grafo, inicio)
        if saida is None:
            continue
        dist, pai, ciclo = saida
        if ciclo:
            percursos[apelido] = {
                "status": "CICLO_NEGATIVO",
                "passos": [],
                "custo": None,
                "ciclo": [rotular(e) for e in ciclo],
            }
            continue
        if dist.get(ALVO, float("inf")) == float("inf"):
            percursos[apelido] = {"status": "SEM_SOLUCAO", "passos": [], "custo": None}
            continue
        caminho = _reconstruir(pai, ALVO)
        passos = []
        for estado in caminho:
            if estado == ALVO:
                continue
            l, c, chaves, bonus = estado
            passos.append({
                "l": l, "c": c,
                "chaves": chaves,
                "bonus": sorted(int(b) for b in bonus),
                "custo": dist[estado] if dist[estado] != float("inf") else None,
                "rotulo": rotular(estado),
            })
        percursos[apelido] = {
            "status": "OK",
            "passos": passos,
            "custo": dist[ALVO],
            "n_passos": len(passos) - 1,
        }

    sem_alvo = gr.subgrafo_induzido(grafo, [n for n in grafo if n != ALVO])

    return {
        "nome": nome,
        "fonte": fonte,
        "grade": grade,
        "linhas": len(grade),
        "colunas": len(grade[0]) if grade else 0,
        "metricas": {
            "ordem": gr.ordem(sem_alvo),
            "tamanho": gr.tamanho(sem_alvo),
            "densidade": round(gr.densidade(sem_alvo), 6),
            "teto": teto_teorico(grade, fonte=fonte),
        },
        "camadas": {k: sorted(map(list, v)) for k, v in sorted(camadas.items())},
        "armadilhas": sorted([e[0], e[1], e[2] or "-"] for e in armadilhas),
        "percursos": percursos,
    }


# ----------------------------------------------------------------------
# a pagina
# ----------------------------------------------------------------------

# [IA] Claude Code – pagina interativa em React (so visualizacao/UX).
# O modelo da pagina fica em src/web/labirinto.html. As bibliotecas (React,
# ReactDOM e htm) ficam em src/web/vendor/ e sao embutidas no HTML gerado,
# para a pagina abrir sem internet (ex.: na apresentacao).
PASTA_WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
BIBLIOTECAS = ["react.production.min.js", "react-dom.production.min.js", "htm.umd.js"]


def _ler(caminho):
    with open(caminho, encoding="utf-8") as arquivo:
        return arquivo.read()


def _montar_pagina(dados):
    """Junta modelo + bibliotecas + dados num unico HTML."""
    modelo = _ler(os.path.join(PASTA_WEB, "labirinto.html"))
    scripts = "\n".join(
        "<script>\n" + _ler(os.path.join(PASTA_WEB, "vendor", nome)).replace("</script", "<\\/script") + "\n</script>"
        for nome in BIBLIOTECAS
    )
    # "</" escapado para o JSON nao fechar a tag <script> por engano
    json_dados = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    return modelo.replace("__VENDOR__", scripts).replace("__DADOS__", json_dados)


def gerar_html(mapas=None, saida="out/parte1/labirinto_interativo.html"):
    """Gera a pagina interativa com todos os mapas informados."""
    if mapas is None:
        mapas = sorted(glob.glob("data/mapas/*.txt")) + sorted(glob.glob("data/mapas_grupo/*.txt"))

    dados = {}
    for caminho in mapas:
        try:
            info = coletar(caminho)

            if info["nome"] == "m06_fonte":
                info["versao_consumivel"] = coletar(caminho, fonte="consumivel")

            dados[info["nome"]] = info
        except Exception as erro:
            print(f"  ! {os.path.basename(caminho)}: {type(erro).__name__}: {erro}")

    os.makedirs(os.path.dirname(saida), exist_ok=True)
    html = _montar_pagina(dados)
    with open(saida, "w", encoding="utf-8") as arquivo:
        arquivo.write(html)

    return saida, dados




import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap

CORES_CASA = {
    "#": "#343846", ".": "#ffffff", "S": "#67c18a", "G": "#f0a05a",
    ",": "#c08c4a", "~": "#6fa8d6", "+": "#e5739b", "*": "#58c3bc",
}
COR_CHAVE, COR_PORTA, COR_ESTEIRA = "#f2d750", "#b49ad8", "#9aa6b8"

RAMPA_CAMADA = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]

RAMPA_SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def _tons(n):
    if n <= 1:
        return [RAMPA_CAMADA[2]]
    ultimo = len(RAMPA_CAMADA) - 1
    return [RAMPA_CAMADA[round(i * ultimo / (n - 1))] for i in range(n)]

TINTA, TINTA2 = "#16181f", "#6b7183"


def _cor_da_casa(ch):
    if ch in CORES_CASA:
        return CORES_CASA[ch]
    if ch in "abcd":
        return COR_CHAVE
    if ch in "ABCD":
        return COR_PORTA
    if ch in "><^v":
        return COR_ESTEIRA
    return "#ffffff"


def _desenhar_grade(ax, grade, rotulos=True):
    n_l, n_c = len(grade), len(grade[0])
    for l in range(n_l):
        for c in range(n_c):
            ch = grade[l][c]
            ax.add_patch(Rectangle((c - .5, l - .5), 1, 1,
                                   facecolor=_cor_da_casa(ch),
                                   edgecolor="#d3d7e0", linewidth=.4))
            if rotulos and ch not in "#.":
                ax.text(c, l, ch, ha="center", va="center",
                        fontsize=max(4, min(9, 150 / n_c)), color=TINTA, weight="bold")
    ax.set_xlim(-.5, n_c - .5)
    ax.set_ylim(n_l - .5, -.5)
    ax.set_aspect("equal")
    ax.set_xlabel("coluna", fontsize=9, color=TINTA2)
    ax.set_ylabel("linha", fontsize=9, color=TINTA2)
    ax.tick_params(labelsize=7, colors=TINTA2, length=2)
    for lado in ax.spines.values():
        lado.set_color("#d3d7e0")


def _legenda_casas(ax, grade):
    presentes, itens = {ch for linha in grade for ch in linha}, []
    rotulo = [("#", "parede"), (".", "chão · 1"), (",", "lama · 3"), ("~", "água · 5"),
              ("+", "bônus · −4"), ("*", "fonte · −2"), ("S", "início"), ("G", "saída")]
    for ch, nome in rotulo:
        if ch in presentes:
            itens.append(Patch(facecolor=_cor_da_casa(ch), edgecolor="#d3d7e0", label=nome))
    if presentes & set("abcd"):
        itens.append(Patch(facecolor=COR_CHAVE, edgecolor="#d3d7e0", label="chave"))
    if presentes & set("ABCD"):
        itens.append(Patch(facecolor=COR_PORTA, edgecolor="#d3d7e0", label="porta"))
    if presentes & set("><^v"):
        itens.append(Patch(facecolor=COR_ESTEIRA, edgecolor="#d3d7e0", label="esteira"))
    return itens


def _percurso(grade, algoritmo="DIJKSTRA"):
    grafo = construir_g_est(grade)
    inicio = estado_inicial(grade)
    for nome in (algoritmo, "BELLMAN_FORD", "BFS"):
        if nome not in ALGORITMOS:
            continue
        saida = _rodar(ALGORITMOS[nome], grafo, inicio)
        if saida is None:
            continue
        dist, pai, ciclo = saida
        if ciclo or dist.get(ALVO, float("inf")) == float("inf"):
            continue
        caminho = [e for e in _reconstruir(pai, ALVO) if e != ALVO]
        return caminho, dist, nome
    return None, None, None


def figura_percurso(caminho_mapa, saida=None):
    nome = os.path.splitext(os.path.basename(caminho_mapa))[0]
    saida = saida or f"out/parte1/percurso_{nome.split('_')[0]}.png"
    grade = ler_mapa(caminho_mapa)
    caminho, dist, alg = _percurso(grade)

    if caminho is None:
        print(f"  ! {nome}: nenhum algoritmo devolveu caminho")
        return None

    ordem_camadas = []

    for e in caminho:
        if e[2] not in ordem_camadas:
            ordem_camadas.append(e[2])

    paleta = [
        "#2563EB",
        "#EA580C",
        "#9333EA",
        "#059669",
        "#DB2777"
    ]

    cor_de = {
        ch: paleta[i % len(paleta)]
        for i, ch in enumerate(ordem_camadas)
    }

    n_l, n_c = len(grade), len(grade[0])
    mapa_grande = n_c > 30

    if mapa_grande:
        fig, ax = plt.subplots(figsize=(24, 13))
    else:
        fig, ax = plt.subplots(
            figsize=(max(8, n_c * .45), max(6, n_l * .45 + 2.2))
        )

    _desenhar_grade(ax, grade, rotulos=not mapa_grande)

    segmentos = list(zip(caminho, caminho[1:]))
    sobreposicoes = {}

    for i, (a, b) in enumerate(segmentos):
        trecho = tuple(sorted((a[:2], b[:2])))
        sobreposicoes.setdefault(trecho, []).append(i)

    for i, (a, b) in enumerate(segmentos):
        x0, y0 = a[1], a[0]
        x1, y1 = b[1], b[0]

        cor = cor_de[b[2]]

        trecho = tuple(sorted((a[:2], b[:2])))
        ocorrencias = sobreposicoes[trecho]

        if len(ocorrencias) > 1:
            indice = ocorrencias.index(i)
            deslocamento = (
                indice - (len(ocorrencias) - 1) / 2
            ) * .24

            if y0 == y1:
                y0 += deslocamento
                y1 += deslocamento
            else:
                x0 += deslocamento
                x1 += deslocamento

        ax.plot(
            [x0, x1], [y0, y1],
            color="#ffffff",
            linewidth=4.5,
            solid_capstyle="round",
            zorder=3
        )

        ax.plot(
            [x0, x1], [y0, y1],
            color=cor,
            linewidth=2.8,
            solid_capstyle="round",
            zorder=4
        )

        ax.plot(
            x0, y0, "o",
            markersize=3.2,
            color=cor,
            markeredgecolor="#ffffff",
            markeredgewidth=.7,
            zorder=5
        )

        intervalo_setas = 5 if mapa_grande else 3

        if i % intervalo_setas == 0 or len(ocorrencias) > 1:
            ax.annotate(
                "",
                xy=(
                    x0 + (x1 - x0) * .75,
                    y0 + (y1 - y0) * .75
                ),
                xytext=(
                    x0 + (x1 - x0) * .25,
                    y0 + (y1 - y0) * .25
                ),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=cor,
                    linewidth=1.5,
                    mutation_scale=12,
                    shrinkA=0,
                    shrinkB=0
                ),
                zorder=6
            )

    ultimo = caminho[-1]

    ax.plot(
        ultimo[1], ultimo[0], "o",
        markersize=5,
        color=cor_de[ultimo[2]],
        markeredgecolor="#ffffff",
        markeredgewidth=1,
        zorder=7
    )

    for a, b in segmentos:
        if b[2] != a[2]:
            nova = (set(b[2]) - set(a[2])).pop()

            ax.annotate(
                f"pegou {nova}",
                (b[1], b[0]),
                textcoords="offset points",
                xytext=(0, 14),
                ha="center",
                fontsize=12 if mapa_grande else 9,
                color=TINTA,
                weight="bold",
                bbox=dict(
                    boxstyle="round,pad=0.25",
                    fc="#ffffff",
                    ec=cor_de[b[2]],
                    lw=1.5
                ),
                zorder=10
            )

    itens = [
        Line2D(
            [], [],
            color=cor_de[ch],
            lw=4,
            label=f"com {ch}" if ch else "sem chaves"
        )
        for ch in ordem_camadas
    ]

    itens += _legenda_casas(ax, grade)

    ax.legend(
        handles=itens,
        loc="upper center",
        bbox_to_anchor=(.5, -.075 if mapa_grande else -.12),
        ncol=min(6 if mapa_grande else 5, len(itens)),
        fontsize=19 if mapa_grande else 10,
        frameon=False,
        handlelength=2.5,
        columnspacing=1.5,
        labelspacing=.8
    )

    ax.set_title(
        f"Caminho de menor custo — {nome}\n"
        f"{alg} · {len(caminho)-1} passos · custo {dist[ALVO]} · "
        f"{len(ordem_camadas)} camada(s)",
        fontsize=22 if mapa_grande else 14,
        color=TINTA,
        weight="bold",
        pad=15
    )

    ax.set_xlabel(
        "coluna",
        fontsize=14 if mapa_grande else 11,
        color=TINTA2
    )

    ax.set_ylabel(
        "linha",
        fontsize=14 if mapa_grande else 11,
        color=TINTA2
    )

    ax.tick_params(
        labelsize=12 if mapa_grande else 9
    )

    fig.tight_layout()

    fig.savefig(
        saida,
        dpi=200,
        bbox_inches="tight",
        facecolor="#fcfcfb"
    )

    plt.close(fig)

    return saida


def figura_camadas(caminho_mapa="data/mapas/m02_uma_chave.txt",
                   saida="out/parte1/camadas_m02.png"):
    nome = os.path.splitext(os.path.basename(caminho_mapa))[0]
    grade = ler_mapa(caminho_mapa)
    grafo = construir_g_est(grade)
    n_l, n_c = len(grade), len(grade[0])

    camadas = sorted(
        {e[2] for e in grafo if e != ALVO},
        key=lambda s: (len(s), s)
    )

    faixa = {ch: i for i, ch in enumerate(camadas)}

    paleta = [
        "#2563EB",
        "#EA580C",
        "#9333EA",
        "#059669",
        "#DB2777"
    ]

    tons = {
        ch: paleta[i % len(paleta)]
        for i, ch in enumerate(camadas)
    }

    cor_arco = "#64748B"
    cor_transicao = "#059669"
    alt = n_l + 1.5
    escala_x = 1.8

    def pos(e):
        return (
            e[1] * escala_x,
            (len(camadas) - 1 - faixa[e[2]]) * alt + e[0]
        )

    fig, ax = plt.subplots(
        figsize=(18, 8)
    )

    for ch in camadas:
        estados = [
            e for e in grafo
            if e != ALVO and e[2] == ch
        ]

        coordenadas = [pos(e) for e in estados]

        xmin = min(x for x, y in coordenadas)
        xmax = max(x for x, y in coordenadas)
        ymin = min(y for x, y in coordenadas)
        ymax = max(y for x, y in coordenadas)

        ax.add_patch(
            Rectangle(
                (xmin - .8, ymin - .7),
                xmax - xmin + 1.6,
                ymax - ymin + 1.4,
                facecolor=tons[ch],
                edgecolor=tons[ch],
                alpha=.07,
                linewidth=1.5,
                zorder=0
            )
        )

        ax.text(
            xmin - 1.2,
            (ymin + ymax) / 2,
            f"Com {ch}" if ch else "Sem chaves",
            ha="right",
            va="center",
            fontsize=13,
            weight="bold",
            color=tons[ch]
        )

    dentro = fora = 0

    for origem, vizinhos in grafo.items():
        if origem == ALVO:
            continue

        x0, y0 = pos(origem)

        for destino, _ in vizinhos:
            if destino == ALVO:
                continue

            x1, y1 = pos(destino)

            if destino[2] == origem[2]:

                reciproco = any(
                    v == origem
                    for v, _ in grafo[destino]
                )

                ax.annotate(
                    "",
                    xy=(x1, y1),
                    xytext=(x0, y0),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        color=cor_arco,
                        linewidth=1.3,
                        mutation_scale=12,
                        shrinkA=6,
                        shrinkB=6,
                        connectionstyle=(
                            "arc3,rad=0.16"
                            if reciproco else "arc3,rad=0"
                        )
                    ),
                    zorder=2
                )

                dentro += 1

            else:
                ax.annotate(
                    "",
                    xy=(x1, y1),
                    xytext=(x0, y0),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        color=cor_transicao,
                        linewidth=3,
                        mutation_scale=22,
                        shrinkA=7,
                        shrinkB=7
                    ),
                    zorder=5
                )

                novas = "".join(
                    sorted(set(destino[2]) - set(origem[2]))
                )

                ax.annotate(
                    f"Coleta da chave {novas}",
                    ((x0 + x1) / 2, (y0 + y1) / 2),
                    textcoords="offset points",
                    xytext=(-18, 0),
                    ha="right",
                    va="center",
                    fontsize=12,
                    weight="bold",
                    color=cor_transicao,
                    bbox=dict(
                        boxstyle="round,pad=0.4",
                        fc="#ffffff",
                        ec=cor_transicao,
                        lw=1.5
                    ),
                    zorder=7
                )

                fora += 1

    for e in grafo:
        if e == ALVO:
            continue

        x, y = pos(e)

        ax.plot(
            x, y, "o",
            markersize=10,
            color=tons[e[2]],
            markeredgecolor="#ffffff",
            markeredgewidth=1.4,
            zorder=4
        )

        ax.annotate(
            rotular(e),
            (x, y),
            textcoords="offset points",
            xytext=(0, 11),
            ha="center",
            va="bottom",
            fontsize=8.5,
            color=TINTA,
            zorder=6
        )

    ax.autoscale_view()
    ax.margins(x=.12, y=.10)
    ax.invert_yaxis()
    ax.axis("off")

    itens = [
        Line2D(
            [], [],
            marker="o",
            color="none",
            markerfacecolor=tons[ch],
            markeredgecolor="#ffffff",
            markersize=10,
            label=f"Com {ch}" if ch else "Sem chaves"
        )
        for ch in camadas
    ]

    itens += [
        Line2D(
            [], [],
            color=cor_arco,
            lw=1.8,
            label=f"Arco interno ({dentro})"
        ),
        Line2D(
            [], [],
            color=cor_transicao,
            lw=3,
            label=f"Mudança de camada ({fora})"
        )
    ]

    ax.legend(
        handles=itens,
        loc="upper center",
        bbox_to_anchor=(.5, -.025),
        ncol=4,
        fontsize=12,
        frameon=False,
        handlelength=2.5,
        columnspacing=2
    )

    ax.set_title(
        f"Grafo de estados em camadas — {nome}\n"
        f"{len(grafo)-1} estados · "
        f"{len(camadas)} camadas · "
        f"{fora} arco(s) de transição",
        fontsize=19,
        weight="bold",
        color=TINTA,
        pad=20
    )

    fig.tight_layout()

    fig.savefig(
        saida,
        dpi=200,
        bbox_inches="tight",
        facecolor="#fcfcfb"
    )

    plt.close(fig)

    return saida


def figura_arvore_bfs(caminho_mapa="data/mapas/m02_uma_chave.txt",
                      saida="out/parte1/arvore_bfs_m02.png"):
    if "BFS" not in ALGORITMOS:
        print("  ! arvore BFS: a funcao bfs() ainda nao existe em algorithms.py")
        return None

    nome = os.path.splitext(os.path.basename(caminho_mapa))[0]
    grade = ler_mapa(caminho_mapa)
    grafo = construir_g_est(grade)
    inicio = estado_inicial(grade)

    saida_bfs = _rodar(ALGORITMOS["BFS"], grafo, inicio)

    if saida_bfs is None:
        return None

    niveis, pais = saida_bfs[0], saida_bfs[1]

    por_nivel = {}

    for no, n in niveis.items():
        if no != ALVO:
            por_nivel.setdefault(n, []).append(no)

    for n in por_nivel:
        por_nivel[n].sort()

    pos = {}

    for n, nos in por_nivel.items():
        for i, no in enumerate(nos):
            pos[no] = (n, i - (len(nos) - 1) / 2)

    fundo = max(por_nivel)

    fig, ax = plt.subplots(figsize=(26, 5.5))

    paleta = [
        "#2563EB",
        "#EA580C",
        "#9333EA",
        "#059669",
        "#DB2777"
    ]

    ordem_ch = sorted(
        {no[2] for no in pos},
        key=lambda t: (len(t), t)
    )

    tons = {
        ch: paleta[i % len(paleta)]
        for i, ch in enumerate(ordem_ch)
    }

    cor_arco = "#64748B"
    cor_transicao = "#059669"

    for n in range(fundo + 1):
        ax.axvline(
            n,
            color="#E2E8F0",
            lw=.8,
            zorder=0
        )

    for no, (x, y) in pos.items():
        pai = pais.get(no)

        if pai not in pos:
            continue

        px, py = pos[pai]

        transicao = no[2] != pai[2]

        ax.annotate(
            "",
            xy=(x, y),
            xytext=(px, py),
            arrowprops=dict(
                arrowstyle="-|>",
                color=cor_transicao if transicao else cor_arco,
                linewidth=2.5 if transicao else 1.4,
                mutation_scale=15 if transicao else 10,
                shrinkA=6,
                shrinkB=6
            ),
            zorder=2
        )

        if transicao:
            novas = "".join(
                sorted(set(no[2]) - set(pai[2]))
            )

            ax.annotate(
                f"Coleta da chave {novas}",
                ((px + x) / 2, (py + y) / 2),
                textcoords="offset points",
                xytext=(0, 65),
                ha="center",
                fontsize=12,
                weight="bold",
                color=cor_transicao,
                bbox=dict(
                    boxstyle="round,pad=0.35",
                    fc="#FFFFFF",
                    ec=cor_transicao,
                    lw=1.5
                ),
                arrowprops=dict(
                    arrowstyle="->",
                    color=cor_transicao,
                    lw=1.3
                ),
                zorder=7
            )

    for no, (x, y) in pos.items():
        cor = tons[no[2]]

        eh_inicio = no == inicio
        eh_saida = grade[no[0]][no[1]] == "G"

        ax.plot(
            x, y, "o",
            markersize=10 if eh_inicio or eh_saida else 7.5,
            color=cor,
            markeredgecolor="#FFFFFF",
            markeredgewidth=1.2,
            zorder=4
        )

        deslocamento = 13 if int(x) % 2 == 0 else -13

        ax.annotate(
            rotular(no),
            (x, y),
            textcoords="offset points",
            xytext=(0, deslocamento),
            ha="center",
            va="bottom" if deslocamento > 0 else "top",
            fontsize=9,
            color=TINTA,
            zorder=5
        )

        if eh_inicio or eh_saida:
            cor_destaque = "#059669" if eh_inicio else "#DC2626"

            ax.plot(
                x, y, "o",
                markersize=15,
                markerfacecolor="none",
                markeredgecolor=cor_destaque,
                markeredgewidth=2,
                zorder=6
            )

            ax.annotate(
                "INÍCIO" if eh_inicio else "SAÍDA",
                (x, y),
                textcoords="offset points",
                xytext=(0, 40),
                ha="center",
                fontsize=11,
                weight="bold",
                color=cor_destaque,
                zorder=7
            )

    largura = max(len(v) for v in por_nivel.values())

    ax.set_ylim(
        -largura / 2 - .45,
        largura / 2 + .65
    )

    ax.set_xlim(-.8, fundo + .8)

    ax.set_xticks(range(fundo + 1))
    ax.set_yticks([])

    ax.tick_params(
        axis="x",
        labelsize=10,
        colors=TINTA2,
        length=3
    )

    ax.set_xlabel(
        "Nível da BFS (número de passos desde o início)",
        fontsize=13,
        color=TINTA2,
        labelpad=12
    )

    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)

    ax.spines["bottom"].set_color("#D3D7E0")

    itens = [
        Line2D(
            [], [],
            marker="o",
            color="none",
            markerfacecolor=tons[ch],
            markeredgecolor="#FFFFFF",
            markersize=10,
            label=f"Com {ch}" if ch else "Sem chaves"
        )
        for ch in ordem_ch
    ]

    itens += [
        Line2D(
            [], [],
            color=cor_arco,
            lw=1.8,
            label="Arco da árvore BFS"
        ),
        Line2D(
            [], [],
            color=cor_transicao,
            lw=2.5,
            label="Mudança de camada"
        ),
        Line2D(
            [], [],
            marker="o",
            color="none",
            markerfacecolor="none",
            markeredgecolor="#059669",
            markeredgewidth=2,
            markersize=10,
            label="Início"
        ),
        Line2D(
            [], [],
            marker="o",
            color="none",
            markerfacecolor="none",
            markeredgecolor="#DC2626",
            markeredgewidth=2,
            markersize=10,
            label="Saída"
        )
    ]

    ax.legend(
        handles=itens,
        loc="upper center",
        bbox_to_anchor=(.5, -.18),
        ncol=6,
        fontsize=12,
        frameon=False,
        handlelength=2.2,
        columnspacing=2
    )

    ax.set_title(
        f"Árvore BFS do grafo de estados — {nome}\n"
        f"{len(pos)} estados alcançáveis · "
        f"profundidade máxima: {fundo} passos",
        fontsize=20,
        weight="bold",
        color=TINTA,
        pad=18
    )

    fig.tight_layout()

    fig.savefig(
        saida,
        dpi=200,
        bbox_inches="tight",
        facecolor="#FCFCFB"
    )

    plt.close(fig)

    return saida


def figura_heatmap(caminho_mapa="data/mapas/m08_grande.txt",
                   saida="out/parte1/heatmap_m08.png"):
    nome = os.path.splitext(os.path.basename(caminho_mapa))[0]
    grade = ler_mapa(caminho_mapa)
    grafo = construir_g_est(grade)
    n_l, n_c = len(grade), len(grade[0])

    mult = [[0] * n_c for _ in range(n_l)]
    for e in grafo:
        if e != ALVO:
            mult[e[0]][e[1]] += 1
    maximo = max(max(linha) for linha in mult)
    casas_no_max = sum(1 for l in range(n_l) for c in range(n_c) if mult[l][c] == maximo)

    cmap = LinearSegmentedColormap.from_list("seq_azul", RAMPA_SEQ)
    fig, ax = plt.subplots(figsize=(max(8, n_c * .22), max(5, n_l * .22 + 1.8)))

    dados = [[float("nan") if grade[l][c] == "#" else mult[l][c] for c in range(n_c)]
             for l in range(n_l)]
    cmap.set_bad(CORES_CASA["#"])
    im = ax.imshow(dados, cmap=cmap, vmin=0, vmax=maximo, interpolation="nearest")

    ax.set_xlabel("coluna", fontsize=9, color=TINTA2)
    ax.set_ylabel("linha", fontsize=9, color=TINTA2)
    ax.tick_params(labelsize=7, colors=TINTA2, length=2)
    for lado in ax.spines.values():
        lado.set_color("#d3d7e0")

    barra = fig.colorbar(im, ax=ax, fraction=.026, pad=.015)
    barra.set_label("estados por casa (multiplicidade)", fontsize=9, color=TINTA2)
    barra.ax.tick_params(labelsize=7, colors=TINTA2, length=2)
    barra.outline.set_edgecolor("#d3d7e0")

    ax.set_title(f"Multiplicidade das casas — {nome}\n"
                 f"{len(grafo)-1} estados em {sum(1 for l in range(n_l) for c in range(n_c) if grade[l][c] != '#')} casas livres · "
                 f"máximo {maximo} (em {casas_no_max} casa(s)) · cinza escuro = parede",
                 fontsize=11, weight="bold", color=TINTA, pad=10)
    fig.savefig(saida, dpi=160, bbox_inches="tight", facecolor="#fcfcfb")
    plt.close(fig)
    return saida, maximo, casas_no_max


def gerar_figuras():
    os.makedirs("out/parte1", exist_ok=True)
    feitas = []
    for mapa in ("data/mapas/m03_tres_chaves.txt", "data/mapas/m08_grande.txt"):
        f = figura_percurso(mapa)
        if f:
            feitas.append(f)
    for fn in (figura_camadas, figura_arvore_bfs):
        f = fn()
        if f:
            feitas.append(f)
    r = figura_heatmap()
    if r:
        feitas.append(r[0])
        print(f"  multiplicidade maxima no m08: {r[1]} (em {r[2]} casa(s))")
    return feitas


def main():
    alvo = sys.argv[1] if len(sys.argv) > 1 else "tudo"

    if alvo in ("tudo", "html"):
        destino, dados = gerar_html()
        print(f"{destino}  ({os.path.getsize(destino)/1024:.0f} KB, {len(dados)} mapas)")

    if alvo in ("tudo", "figuras"):
        for f in gerar_figuras():
            print(f"{f}  ({os.path.getsize(f)/1024:.0f} KB)")

    print(f"algoritmos disponiveis: {', '.join(sorted(ALGORITMOS)) or '(nenhum)'}")


if __name__ == "__main__":
    main()
