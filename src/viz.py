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
    tons = _tons(len(ordem_camadas))
    cor_de = {ch: tons[i] for i, ch in enumerate(ordem_camadas)}

    n_l, n_c = len(grade), len(grade[0])
    fig, ax = plt.subplots(figsize=(max(6, n_c * .34), max(4, n_l * .34 + 2.2)))
    _desenhar_grade(ax, grade, rotulos=n_c <= 30)

    for a, b in zip(caminho, caminho[1:]):
        ax.plot([a[1], b[1]], [a[0], b[0]], color=cor_de[b[2]],
                linewidth=3.2, solid_capstyle="round", zorder=3,
                path_effects=None)
    for e in caminho:
        ax.plot(e[1], e[0], "o", markersize=4.6, color=cor_de[e[2]],
                markeredgecolor="#ffffff", markeredgewidth=1.0, zorder=4)

    for a, b in zip(caminho, caminho[1:]):
        if b[2] != a[2]:
            nova = (set(b[2]) - set(a[2])).pop()
            ax.annotate(f"pegou {nova}", (b[1], b[0]),
                        textcoords="offset points", xytext=(0, 13),
                        ha="center", fontsize=7.5, color=TINTA, weight="bold",
                        bbox=dict(boxstyle="round,pad=0.22", fc="#ffffff",
                                  ec=cor_de[b[2]], lw=1.0), zorder=6)

    itens = [Line2D([], [], color=cor_de[ch], lw=3.2,
                    label=f"com {ch}" if ch else "sem chaves")
             for ch in ordem_camadas]
    itens += _legenda_casas(ax, grade)
    ax.legend(handles=itens, loc="upper center", bbox_to_anchor=(.5, -.14),
              ncol=min(5, len(itens)), fontsize=7.5, frameon=False)

    ax.set_title(f"Caminho de menor custo — {nome}\n"
                 f"{alg} · {len(caminho)-1} passos · custo {dist[ALVO]} · "
                 f"{len(ordem_camadas)} camada(s)",
                 fontsize=11, color=TINTA, weight="bold", pad=10)
    fig.tight_layout()
    fig.savefig(saida, dpi=160, bbox_inches="tight", facecolor="#fcfcfb")
    plt.close(fig)
    return saida


def figura_camadas(caminho_mapa="data/mapas/m02_uma_chave.txt",
                   saida="out/parte1/camadas_m02.png"):
    nome = os.path.splitext(os.path.basename(caminho_mapa))[0]
    grade = ler_mapa(caminho_mapa)
    grafo = construir_g_est(grade)
    n_l, n_c = len(grade), len(grade[0])

    camadas = sorted({e[2] for e in grafo if e != ALVO}, key=lambda s: (len(s), s))
    faixa = {ch: i for i, ch in enumerate(camadas)}
    tons = _tons(len(camadas))
    alt = n_l + 2.2

    def pos(e):
        return (e[1], (len(camadas) - 1 - faixa[e[2]]) * alt + e[0])

    fig, ax = plt.subplots(figsize=(max(7, n_c * .5), 2.4 + len(camadas) * alt * .42))

    for ch in camadas:
        y0 = (len(camadas) - 1 - faixa[ch]) * alt - .6
        ax.add_patch(Rectangle((-1.1, y0), n_c + 1.4, n_l + .2,
                               facecolor="#f3f5f8", edgecolor="#d3d7e0", lw=.8, zorder=0))
        ax.text(-1.5, y0 + n_l / 2, f"camada\n{ch or '-'}", ha="right", va="center",
                fontsize=9, weight="bold", color=tons[faixa[ch]])

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
                ax.annotate("", (x1, y1), (x0, y0), zorder=1,
                            arrowprops=dict(arrowstyle="->", color="#c3c7d2",
                                            lw=1.0, shrinkA=3, shrinkB=3))
                dentro += 1
            else:
                ax.annotate("", (x1, y1), (x0, y0), zorder=5,
                            arrowprops=dict(arrowstyle="-|>", color="#eb6834",
                                            lw=2.4, shrinkA=3, shrinkB=3))
                fora += 1

    for e in grafo:
        if e == ALVO:
            continue
        x, y = pos(e)
        ax.plot(x, y, "o", markersize=7, color=tons[faixa[e[2]]],
                markeredgecolor="#ffffff", markeredgewidth=1.0, zorder=4)

        ax.text(x + 0.18, y - 0.12, rotular(e),
                fontsize=5.5, color=TINTA, zorder=6)

    ax.set_xlim(-3.4, n_c + .6)
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(handles=[
        Line2D([], [], color="#c3c7d2", lw=1.4, label=f"arco dentro da camada ({dentro})"),
        Line2D([], [], color="#eb6834", lw=2.4, label=f"arco que TROCA de camada ({fora})"),
        Line2D([], [], marker="o", color="none", markerfacecolor=tons[0],
               markeredgecolor="#fff", markersize=8, label="estado"),
    ], loc="upper center", bbox_to_anchor=(.5, -.02), ncol=3, fontsize=8.5, frameon=False)
    ax.set_title(f"Grafo de estados em camadas — {nome}\n"
                 f"{len(grafo)-1} estados · cada camada é um conjunto de chaves · "
                 f"{fora} arco(s) trocam de camada",
                 fontsize=11, weight="bold", color=TINTA, pad=12)
    fig.tight_layout()
    fig.savefig(saida, dpi=160, bbox_inches="tight", facecolor="#fcfcfb")
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
    fig, ax = plt.subplots(figsize=(max(8, fundo * .42), 4.6))

    for no, (x, y) in pos.items():
        pai = pais.get(no)
        if pai in pos:
            px, py = pos[pai]
            ax.plot([px, x], [py, y], color="#c3c7d2", lw=1.0, zorder=1)

    ordem_ch = sorted({no[2] for no in pos}, key=lambda t: (len(t), t))
    tons = dict(zip(ordem_ch, _tons(len(ordem_ch))))
    for no, (x, y) in pos.items():
        cor = tons[no[2]]
        ax.plot(x, y, "o", markersize=5.6, color=cor,
                markeredgecolor="#ffffff", markeredgewidth=.9, zorder=3)

        ax.text(x + 0.08, y + 0.08, rotular(no),
                fontsize=5.2, color=TINTA, zorder=4)

    for n in range(0, fundo + 1, max(1, fundo // 12)):
        ax.axvline(n, color="#e7eaf0", lw=.7, zorder=0)

    largura = max(len(v) for v in por_nivel.values())
    ax.set_ylim(-largura / 2 - .8, largura / 2 + .8)
    ax.set_xlim(-.8, fundo + .8)

    chaves = ordem_ch
    ax.legend(handles=[Line2D([], [], marker="o", color="none",
                              markerfacecolor=tons[ch],
                              markeredgecolor="#fff", markersize=8,
                              label=f"com {ch}" if ch else "sem chaves")
                       for ch in chaves],
              loc="upper center", bbox_to_anchor=(.5, -.08),
              ncol=len(chaves), fontsize=8.5, frameon=False)

    ax.set_xlabel("nível da BFS  (número de passos desde o início)",
                  fontsize=9.5, color=TINTA2)
    ax.set_yticks([])
    ax.tick_params(labelsize=7, colors=TINTA2, length=2)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color("#d3d7e0")
    ax.set_title(f"Árvore BFS do grafo de estados — {nome}\n"
                 f"{len(pos)} estados alcançáveis · profundidade {fundo} níveis",
                 fontsize=11, weight="bold", color=TINTA, pad=10)
    fig.tight_layout()
    fig.savefig(saida, dpi=160, bbox_inches="tight", facecolor="#fcfcfb")
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
