import json
import os
import matplotlib.pyplot as plt
import numpy as np

PASTA = "out/parte2"

CORES = {
    "BFS": "#2563EB",
    "DFS": "#EA580C",
    "DIJKSTRA": "#9333EA",
    "BELLMAN_FORD": "#059669"
}

NOMES = {
    "BFS": "BFS",
    "DFS": "DFS",
    "DIJKSTRA": "Dijkstra (recusa)",
    "BELLMAN_FORD": "Bellman-Ford"
}

plt.rcParams.update({
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titleweight": "bold",
    "figure.facecolor": "white"
})


def salvar(fig, nome):
    caminho = os.path.join(PASTA, nome)
    fig.tight_layout()
    fig.savefig(caminho, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Gerado: {caminho}")


def extrair_tarefas(dados):
    resultados = dados["resultados"]
    tarefas = []

    for algoritmo in ["BFS", "DFS"]:
        for item in resultados[algoritmo]:
            tarefas.append((
                f"{algoritmo} — {item['fonte']}",
                algoritmo,
                item
            ))

    tarefas.append((
        "Dijkstra — recusa",
        "DIJKSTRA",
        resultados["DIJKSTRA"]
    ))

    tarefas.append((
        "Bellman-Ford — recorte",
        "BELLMAN_FORD",
        resultados["BELLMAN_FORD"]["sem_ciclo_negativo"]
    ))

    tarefas.append((
        "Bellman-Ford — grafo completo",
        "BELLMAN_FORD",
        resultados["BELLMAN_FORD"]["grafo_completo"]
    ))

    return tarefas


def figura_tempo(dados):
    tarefas = extrair_tarefas(dados)

    rotulos = [t[0] for t in tarefas]
    cores = [CORES[t[1]] for t in tarefas]
    valores = [t[2]["tempo_medio_s"] for t in tarefas]

    fig, ax = plt.subplots(figsize=(13, 7))

    barras = ax.barh(rotulos, valores, color=cores)

    ax.set_xscale("log")
    ax.invert_yaxis()
    ax.set_xlim(min(valores) / 2, max(valores) * 12)

    for barra, valor in zip(barras, valores):
        ax.text(
            valor * 1.12,
            barra.get_y() + barra.get_height() / 2,
            f"{valor:.3g} s",
            va="center"
        )

    ax.set_title("Tempo médio de execução por algoritmo e tarefa")
    ax.set_xlabel("Tempo médio em segundos — escala logarítmica")
    ax.grid(axis="x", alpha=0.2)
    ax.set_axisbelow(True)

    salvar(fig, "alg_01_comparacao_tempo.png")


def figura_memoria(dados):
    tarefas = extrair_tarefas(dados)

    rotulos = [t[0] for t in tarefas]
    cores = [CORES[t[1]] for t in tarefas]
    valores = [
        t[2]["memoria_pico_bytes"] / 1024
        for t in tarefas
    ]

    fig, ax = plt.subplots(figsize=(13, 7))

    barras = ax.barh(rotulos, valores, color=cores)

    ax.set_xscale("log")
    ax.invert_yaxis()
    ax.set_xlim(min(valores) / 2, max(valores) * 5)

    for barra, valor in zip(barras, valores):
        ax.text(
            valor * 1.12,
            barra.get_y() + barra.get_height() / 2,
            f"{valor:.2f} KiB",
            va="center"
        )

    ax.set_title("Pico de memória por algoritmo e tarefa")
    ax.set_xlabel("Memória alocada em KiB — escala logarítmica")
    ax.grid(axis="x", alpha=0.2)
    ax.set_axisbelow(True)

    salvar(fig, "alg_02_comparacao_memoria.png")


def figura_escalabilidade(dados):
    resultados = dados["escalabilidade"]
    tamanhos = [r["vertices"] for r in resultados]

    fig, ax = plt.subplots(figsize=(12, 7))

    for algoritmo in CORES:
        tempos = [
            r["algoritmos"][algoritmo]["tempo_medio_s"]
            for r in resultados
        ]

        ax.plot(
            tamanhos,
            tempos,
            color=CORES[algoritmo],
            marker="o",
            markersize=8,
            linewidth=2.5,
            linestyle="--" if algoritmo == "DIJKSTRA" else "-",
            label=NOMES[algoritmo]
        )

    ax.set_yscale("log")

    ax.set_xticks(tamanhos)
    ax.set_xticklabels([
        f"{r['percentual']}%\n"
        f"{r['vertices']} vértices\n"
        f"{r['arestas']} arcos"
        for r in resultados
    ])

    ax.set_title("Escalabilidade dos algoritmos")
    ax.set_xlabel("Tamanho do grafo")
    ax.set_ylabel("Tempo médio em segundos — escala logarítmica")
    ax.grid(alpha=0.2)
    ax.legend()

    salvar(fig, "alg_03_escalabilidade.png")


def figura_camadas_bfs(dados):
    resultados = dados["resultados"]["BFS"]

    niveis = sorted({
        int(nivel)
        for item in resultados
        for nivel in item["camadas"]
    })

    posicoes = np.arange(len(niveis))
    largura = 0.25

    cores = ["#2563EB", "#EA580C", "#059669"]

    fig, ax = plt.subplots(figsize=(12, 7))

    for i, item in enumerate(resultados):
        quantidades = [
            len(item["camadas"].get(str(nivel), []))
            for nivel in niveis
        ]

        barras = ax.bar(
            posicoes + (i - 1) * largura,
            quantidades,
            largura,
            color=cores[i],
            label=f"Fonte {item['fonte']}"
        )

        ax.bar_label(
            barras,
            padding=3,
            fontsize=8
        )

    ax.set_xticks(posicoes)
    ax.set_xticklabels(niveis)

    ax.set_title("Distribuição dos vértices por camada da BFS")
    ax.set_xlabel("Nível — distância em número de arcos")
    ax.set_ylabel("Quantidade de vértices")
    ax.set_ylim(0, 2300)
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    ax.legend()

    salvar(fig, "alg_04_camadas_bfs.png")


def figura_arcos_dfs(dados):
    resultados = dados["resultados"]["DFS"]
    fontes = [str(r["fonte"]) for r in resultados]

    tipos = {
        "arvore": ("Árvore", "#2563EB"),
        "retorno": ("Retorno", "#DC2626"),
        "avanco": ("Avanço", "#059669"),
        "cruzamento": ("Cruzamento", "#9333EA")
    }

    acumulado = np.zeros(len(fontes))

    fig, ax = plt.subplots(figsize=(10, 7))

    for tipo, (rotulo, cor) in tipos.items():
        valores = [
            r["classificacao_arcos"][tipo]
            for r in resultados
        ]

        barras = ax.bar(
            fontes,
            valores,
            bottom=acumulado,
            color=cor,
            label=rotulo,
            width=0.55
        )

        for barra, valor, base in zip(
            barras, valores, acumulado
        ):
            if valor >= 1000:
                ax.text(
                    barra.get_x() + barra.get_width() / 2,
                    base + valor / 2,
                    str(valor),
                    color="white",
                    ha="center",
                    va="center",
                    fontweight="bold"
                )
            else:
                ax.text(
                    barra.get_x() + barra.get_width() / 2,
                    base + valor + 180,
                    str(valor),
                    color=cor,
                    ha="center",
                    va="bottom"
                )

        acumulado += valores

    ax.set_title("Classificação dos arcos pela DFS")
    ax.set_xlabel("Vértice de origem")
    ax.set_ylabel("Quantidade de arcos")
    ax.set_ylim(0, max(acumulado) * 1.12)
    ax.legend(loc="upper center", ncol=4)
    ax.grid(axis="y", alpha=0.15)
    ax.set_axisbelow(True)

    salvar(fig, "alg_05_classificacao_dfs.png")


def reconstruir_caminho(pais, destino):
    caminho = []
    visitados = set()
    atual = destino

    while atual is not None:
        if atual in visitados:
            raise ValueError("Ciclo na cadeia de predecessores")

        visitados.add(atual)
        caminho.append(atual)
        atual = pais.get(str(atual))

    return caminho[::-1]


def desenhar_caminho(ax, caminho, cor, titulo, pesos=None):
    posicoes = np.linspace(0, 1, len(caminho))

    for i in range(len(caminho) - 1):
        ax.annotate(
            "",
            xy=(posicoes[i + 1], 0),
            xytext=(posicoes[i], 0),
            arrowprops={
                "arrowstyle": "->",
                "color": cor,
                "lw": 2,
                "shrinkA": 22,
                "shrinkB": 22
            }
        )

        if pesos is not None:
            ax.text(
                (posicoes[i] + posicoes[i + 1]) / 2,
                0.12,
                str(pesos[i]),
                ha="center",
                color=cor,
                fontweight="bold"
            )

    ax.scatter(
        posicoes,
        [0] * len(caminho),
        s=1600,
        color=cor,
        edgecolors="white",
        linewidths=2,
        zorder=3
    )

    for x, vertice in zip(posicoes, caminho):
        ax.text(
            x, 0, str(vertice),
            ha="center",
            va="center",
            color="white",
            fontweight="bold",
            zorder=4
        )

    ax.set_title(titulo, loc="left", fontsize=12)
    ax.set_xlim(-0.15, 1.15)
    ax.set_ylim(-0.3, 0.3)
    ax.axis("off")


def figura_caminhos(dados):
    resultados = dados["resultados"]

    bfs = resultados["BFS"][0]
    dfs = resultados["DFS"][0]

    destino = 2

    caminho_bfs = reconstruir_caminho(
        bfs["pais"], destino
    )

    caminho_dfs = reconstruir_caminho(
        dfs["pais"], destino
    )

    bf = resultados["BELLMAN_FORD"]

    origem, destino_bf, peso = (
        bf["sem_ciclo_negativo"]["aresta_original"]
    )

    ciclo = bf["grafo_completo"]["ciclo"]
    pesos = bf["grafo_completo"]["pesos_ciclo"]
    custo = bf["grafo_completo"]["custo_ciclo"]

    fig, axs = plt.subplots(5, 1, figsize=(14, 11))

    desenhar_caminho(
        axs[0],
        caminho_bfs,
        CORES["BFS"],
        f"BFS — {len(caminho_bfs) - 1} arcos"
    )

    desenhar_caminho(
        axs[1],
        caminho_dfs,
        CORES["DFS"],
        f"DFS — {len(caminho_dfs) - 1} arcos na árvore"
    )

    desenhar_caminho(
        axs[2],
        [origem, destino_bf],
        CORES["BELLMAN_FORD"],
        f"Bellman-Ford — sem ciclo negativo | Custo: {peso}",
        [peso]
    )

    desenhar_caminho(
        axs[3],
        ciclo,
        "#DC2626",
        f"Bellman-Ford — ciclo negativo | Custo: {custo}",
        pesos
    )

    axs[4].axis("off")

    axs[4].text(
        0.5, 0.6,
        "Dijkstra — execução recusada",
        ha="center",
        fontsize=14,
        fontweight="bold",
        color=CORES["DIJKSTRA"]
    )

    axs[4].text(
        0.5, 0.25,
        "O grafo contém pesos negativos. "
        "Nenhum caminho foi calculado.",
        ha="center",
        fontsize=11
    )

    fig.suptitle(
        "Comparação dos caminhos e comportamentos dos algoritmos",
        fontsize=16,
        fontweight="bold"
    )

    salvar(fig, "alg_06_comparacao_caminhos.png")


def main():
    with open(
        os.path.join(PASTA, "parte2_report.json"),
        encoding="utf-8"
    ) as arquivo:
        dados = json.load(arquivo)

    figura_tempo(dados)
    figura_memoria(dados)
    figura_escalabilidade(dados)
    figura_camadas_bfs(dados)
    figura_arcos_dfs(dados)
    figura_caminhos(dados)


if __name__ == "__main__":
    main()