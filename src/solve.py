import csv
import glob
import json
import os

# [IA] Claude – geracao dos arquivos de saida (csv/json) a partir das funcoes do grupo

from src.graphs import graph as gr
from src.graphs.algorithms import bellman_ford, bfs, classificar_arcos, dijkstra
from src.graphs.estados import (
    ALVO,
    construir_g_est,
    construir_g_pos,
    estado_inicial,
    rotular,
    teto_teorico,
)
from src.graphs.io import achar_inicio, achar_saida, ler_mapa

INF = float("inf")

DIRECAO = {(-1, 0): "N", (0, 1): "L", (1, 0): "S", (0, -1): "O"}


def movimento(origem, destino):
    if origem == ALVO or destino == ALVO:
        return ""
    return DIRECAO.get((destino[0] - origem[0], destino[1] - origem[1]), "")


def caminho_ate(pais, destino):
    saida, atual, vistos = [], destino, set()
    while atual is not None and atual not in vistos:
        vistos.add(atual)
        saida.append(atual)
        atual = pais.get(atual)
    saida.reverse()
    return saida


def mapas():
    return sorted(glob.glob("data/mapas/*.txt")) + sorted(glob.glob("data/mapas_grupo/*.txt"))


def nome_de(caminho):
    return os.path.splitext(os.path.basename(caminho))[0]


def escrever_csv(destino, cabecalho, linhas):
    with open(destino, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(cabecalho)
        escritor.writerows(linhas)
    return destino


def escrever_json(destino, dados):
    with open(destino, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    return destino


def arestas_csv(nome, grade, grafo, pasta):
    linhas = []
    for origem, vizinhos in grafo.items():
        for destino, peso in vizinhos:
            casa = "" if destino == ALVO else grade[destino[0]][destino[1]]
            linhas.append([rotular(origem), rotular(destino),
                           movimento(origem, destino), casa, peso])
    return escrever_csv(os.path.join(pasta, f"arestas_{nome}.csv"),
                        ["origem", "destino", "movimento", "casa_destino", "peso"],
                        linhas)


def graus_csv(nome, grafo, pasta):
    entrada = gr.graus_entrada(grafo)
    linhas = [[rotular(e), entrada.get(e, 0), gr.grau_saida(grafo, e)]
              for e in sorted(grafo, key=rotular)]
    return escrever_csv(os.path.join(pasta, f"graus_{nome}.csv"),
                        ["estado", "grau_entrada", "grau_saida"], linhas)


def metricas_do_mapa(grade, grafo):
    pos = construir_g_pos(grade)
    ordem = gr.ordem(grafo) - 1
    teto = teto_teorico(grade)
    return {
        "g_pos": {"ordem": gr.ordem(pos), "tamanho": gr.tamanho(pos),
                  "densidade": round(gr.densidade(pos), 6)},
        "g_est": {"ordem": ordem, "tamanho": gr.tamanho(grafo),
                  "densidade": round(gr.densidade(grafo), 6)},
        "teto_teorico": teto,
        "taxa_de_ocupacao": round(ordem / teto, 6) if teto else 0,
    }


def camadas_do_mapa(grafo):
    por_camada = {}
    for e in grafo:
        if e != ALVO:
            por_camada.setdefault(e[2] or "-", []).append(e)

    medidas = {}
    for chaves, estados in sorted(por_camada.items()):
        sub = gr.subgrafo_induzido(grafo, estados)
        medidas[chaves] = {"ordem": gr.ordem(sub), "tamanho": gr.tamanho(sub),
                           "densidade": round(gr.densidade(sub), 6)}

    entre = []
    for origem, vizinhos in grafo.items():
        if origem == ALVO:
            continue
        for destino, _ in vizinhos:
            if destino != ALVO and destino[2] != origem[2]:
                entre.append({"origem": rotular(origem), "destino": rotular(destino),
                              "casa": [destino[0], destino[1]]})
    return {"camadas": medidas, "arcos_entre_camadas": len(entre), "arcos": entre}


def graus_extremos(grafo):
    entrada = gr.graus_entrada(grafo)
    estados = [e for e in grafo if e != ALVO]
    if not estados:
        return {}
    maior_saida = min(estados, key=lambda e: (-gr.grau_saida(grafo, e), rotular(e)))
    maior_entrada = min(estados, key=lambda e: (-entrada.get(e, 0), rotular(e)))
    becos = [rotular(e) for e in estados if gr.grau_saida(grafo, e) == 0]
    casas = {}
    for e in estados:
        casas[(e[0], e[1])] = casas.get((e[0], e[1]), 0) + 1
    maximo = max(casas.values())
    return {
        "maior_grau_saida": {"estado": rotular(maior_saida),
                             "grau": gr.grau_saida(grafo, maior_saida)},
        "maior_grau_entrada": {"estado": rotular(maior_entrada),
                               "grau": entrada.get(maior_entrada, 0)},
        "becos": becos,
        "multiplicidade_maxima": maximo,
        "casas_com_multiplicidade_maxima": sum(1 for v in casas.values() if v == maximo),
    }


def armadilhas(grafo):
    alcanca = bfs(gr.transposto(grafo), ALVO)[0]
    return [e for e in grafo if e != ALVO and e not in alcanca]


def rodar_algoritmos(grade, grafo):
    inicio = estado_inicial(grade)
    linhas = []

    passos, pais_bfs = bfs(grafo, inicio)
    if passos.get(ALVO, INF) == INF:
        linhas.append(["BFS", "", "", "SEM_SOLUCAO", ""])
    else:
        caminho = [e for e in caminho_ate(pais_bfs, ALVO) if e != ALVO]
        linhas.append(["BFS", passos[ALVO] - 1, "", "OK",
                       " -> ".join(rotular(e) for e in caminho)])

    try:
        custo, pais = dijkstra(grafo, inicio)
    except ValueError as erro:
        linhas.append(["DIJKSTRA", "", "", "RECUSA", str(erro)])
    else:
        if custo.get(ALVO, INF) == INF:
            linhas.append(["DIJKSTRA", "", "", "SEM_SOLUCAO", ""])
        else:
            caminho = [e for e in caminho_ate(pais, ALVO) if e != ALVO]
            linhas.append(["DIJKSTRA", len(caminho) - 1, custo[ALVO], "OK",
                           " -> ".join(rotular(e) for e in caminho)])

    custo, pais, ciclo = bellman_ford(grafo, inicio)
    if ciclo:
        linhas.append(["BELLMAN_FORD", "", "", "CICLO_NEGATIVO",
                       " -> ".join(rotular(e) for e in ciclo)])
    elif custo.get(ALVO, INF) == INF:
        linhas.append(["BELLMAN_FORD", "", "", "SEM_SOLUCAO", ""])
    else:
        caminho = [e for e in caminho_ate(pais, ALVO) if e != ALVO]
        linhas.append(["BELLMAN_FORD", len(caminho) - 1, custo[ALVO], "OK",
                       " -> ".join(rotular(e) for e in caminho)])
    return linhas


def comparacao_modelagem(grade):
    inicio_pos = achar_inicio(grade)
    saidas = achar_saida(grade)
    resultado = []

    for modo, rotulo in (("chao", "G_pos, porta como chao"),
                         ("parede", "G_pos, porta como parede")):
        pos = construir_g_pos(grade, modo_porta=modo)
        if inicio_pos not in pos:
            resultado.append([rotulo, "", "nao", "inicio fora do grafo"])
            continue
        passos, pais = bfs(pos, inicio_pos)
        alcancadas = [s for s in saidas if passos.get(s, INF) != INF]
        if not alcancadas:
            resultado.append([rotulo, "", "nao",
                              "nenhuma saida alcancavel: a modelagem FALHA"])
            continue
        melhor = min(alcancadas, key=lambda s: passos[s])
        caminho = caminho_ate(pais, melhor)
        atravessa = [c for c in caminho if grade[c[0]][c[1]] in "ABCD"]
        if modo == "chao" and atravessa:
            obs = ("caminho INVALIDO: atravessa porta trancada em "
                   + ", ".join(f"({l},{c})" for l, c in atravessa))
            valido = "nao"
        else:
            obs = ""
            valido = "sim"
        resultado.append([rotulo, passos[melhor], valido, obs])

    grafo = construir_g_est(grade)
    passos, _ = bfs(grafo, estado_inicial(grade))
    if passos.get(ALVO, INF) == INF:
        resultado.append(["G_est", "", "nao", "sem solucao"])
    else:
        resultado.append(["G_est", passos[ALVO] - 1, "sim", "modelagem correta"])
    return resultado


# [IA] Claude Code – saidas de BF: m05 no G_pos x G_est e m06 com fonte consumivel
def _custo_ciclo(grafo, ciclo):
    peso = {(u, v): p for u in grafo for v, p in grafo[u]}
    return sum(peso[(ciclo[i], ciclo[i + 1])] for i in range(len(ciclo) - 1))


def _resumo_bf_est(grade, grafo):
    custo, pais, ciclo = bellman_ford(grafo, estado_inicial(grade))
    if ciclo:
        return {"status": "CICLO_NEGATIVO", "custo_do_ciclo": _custo_ciclo(grafo, ciclo),
                "ciclo": [rotular(e) for e in ciclo], "estados": gr.ordem(grafo) - 1}
    if custo.get(ALVO, INF) == INF:
        return {"status": "SEM_SOLUCAO", "estados": gr.ordem(grafo) - 1}
    caminho = [e for e in caminho_ate(pais, ALVO) if e != ALVO]
    return {"status": "OK", "custo": custo[ALVO], "passos": len(caminho) - 1,
            "estados": gr.ordem(grafo) - 1, "caminho": [rotular(e) for e in caminho]}


def prova_m05(nome, grade, grafo):
    pos = construir_g_pos(grade)
    _, _, ciclo = bellman_ford(pos, achar_inicio(grade))
    g_pos = {"status": "CICLO_NEGATIVO" if ciclo else "SEM_CICLO",
             "regra": "'+' vale -4 fixo, toda vez que se entra na casa",
             "ordem": gr.ordem(pos)}
    if ciclo:
        g_pos["custo_do_ciclo"] = _custo_ciclo(pos, ciclo)
        g_pos["ciclo"] = [rotular(e) for e in ciclo]
    g_est = _resumo_bf_est(grade, grafo)
    g_est["regra"] = "cada '+' vale -4 so na primeira visita (bonus guardado no estado)"
    return {"mapa": nome, "algoritmo": "BELLMAN_FORD", "g_pos": g_pos, "g_est": g_est}


def fonte_m06(nome, grade, grafo):
    infinita = _resumo_bf_est(grade, grafo)
    infinita["regra"] = "'*' vale -2 sempre (fonte infinita)"
    consumivel = _resumo_bf_est(grade, construir_g_est(grade, fonte="consumivel"))
    consumivel["regra"] = "'*' vale -2 so na primeira vez (--fonte-consumivel)"
    return {"mapa": nome, "algoritmo": "BELLMAN_FORD",
            "fonte_infinita": infinita, "fonte_consumivel": consumivel}


def gerar(pasta="out/parte1"):
    os.makedirs(pasta, exist_ok=True)
    metricas, camadas, solucoes, dfs_linhas, comparacao = {}, {}, [], [], []
    gerados = []

    for caminho in mapas():
        nome = nome_de(caminho)
        grade = ler_mapa(caminho)
        grafo = construir_g_est(grade)

        gerados.append(arestas_csv(nome, grade, grafo, pasta))
        gerados.append(graus_csv(nome, grafo, pasta))

        metricas[nome] = metricas_do_mapa(grade, grafo)
        metricas[nome].update(graus_extremos(grafo))
        camadas[nome] = camadas_do_mapa(grafo)

        for linha in rodar_algoritmos(grade, grafo):
            solucoes.append([nome] + linha)

        tipos = {"arvore": 0, "retorno": 0, "avanco": 0, "cruzamento": 0}
        for _, _, tipo in classificar_arcos(grafo, estado_inicial(grade)):
            tipos[tipo] += 1
        dfs_linhas.append([nome, tipos["arvore"], tipos["retorno"],
                           tipos["avanco"], tipos["cruzamento"]])

        if nome.startswith(("m02", "m03", "m04")):
            for linha in comparacao_modelagem(grade):
                comparacao.append([nome] + linha)

        presos = armadilhas(grafo)
        if nome.startswith(("m04", "m07")):
            gerados.append(escrever_csv(
                os.path.join(pasta, f"armadilhas_{nome.split('_')[0]}.csv"),
                ["estado", "linha", "coluna", "chaves"],
                [[rotular(e), e[0], e[1], e[2] or "-"] for e in sorted(presos, key=rotular)]))
        metricas[nome]["estados_armadilha"] = len(presos)

        if nome.startswith("m03"):
            custo, pais = dijkstra(grafo, estado_inicial(grade))
            caminho = [e for e in caminho_ate(pais, ALVO) if e != ALVO]
            gerados.append(escrever_json(os.path.join(pasta, "percurso_m03.json"), {
                "mapa": nome, "algoritmo": "DIJKSTRA",
                "passos": len(caminho) - 1, "custo": custo[ALVO],
                "percurso": [{"rotulo": rotular(e), "linha": e[0], "coluna": e[1],
                              "chaves": e[2] or "-", "bonus": sorted(e[3]),
                              "casa": grade[e[0]][e[1]], "custo_acumulado": custo[e]}
                             for e in caminho],
            }))

        if nome.startswith("m06"):
            _, _, ciclo = bellman_ford(grafo, estado_inicial(grade))
            peso = {(u, v): p for u in grafo for v, p in grafo[u]}
            soma = sum(peso[(ciclo[i], ciclo[i + 1])] for i in range(len(ciclo) - 1)) if ciclo else 0
            gerados.append(escrever_json(os.path.join(pasta, "ciclo_negativo_m06.json"), {
                "mapa": nome,
                "tem_ciclo_negativo": bool(ciclo),
                "custo_do_ciclo": soma,
                "ciclo": [rotular(e) for e in ciclo] if ciclo else [],
            }))
            gerados.append(escrever_json(os.path.join(pasta, "m06_fonte_consumivel.json"),
                                         fonte_m06(nome, grade, grafo)))

        if nome.startswith("m05"):
            gerados.append(escrever_json(os.path.join(pasta, "m05_gpos_vs_gest.json"),
                                         prova_m05(nome, grade, grafo)))

    gerados.append(escrever_json(os.path.join(pasta, "metricas_global.json"), metricas))
    gerados.append(escrever_json(os.path.join(pasta, "camadas.json"), camadas))
    gerados.append(escrever_csv(os.path.join(pasta, "solucoes.csv"),
                                ["mapa", "algoritmo", "passos", "custo", "status", "caminho"],
                                solucoes))
    gerados.append(escrever_csv(os.path.join(pasta, "dfs_classificacao.csv"),
                                ["mapa", "arvore", "retorno", "avanco", "cruzamento"],
                                dfs_linhas))
    gerados.append(escrever_csv(os.path.join(pasta, "comparacao_modelagem.csv"),
                                ["mapa", "abordagem", "passos", "caminho_valido", "observacao"],
                                comparacao))
    return gerados


if __name__ == "__main__":
    for arquivo in gerar():
        print(f"{arquivo}  ({os.path.getsize(arquivo)} bytes)")
