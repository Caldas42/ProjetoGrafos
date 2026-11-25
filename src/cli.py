import argparse
import os
import sys
from src.graphs.algorithms import classificar_arcos

from src.graphs import graph as gr
from src.graphs.estados import (
    ALVO,
    construir_g_est,
    construir_g_pos,
    estado_inicial,
    rotular,
    teto_teorico,
)
from src.graphs.io import ler_mapa

ALGORITMOS = {}
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
    from src.graphs.algorithms import bellman_ford
    ALGORITMOS["BELLMAN_FORD"] = bellman_ford
except ImportError:
    pass
try:
    from src.graphs.algorithms import dfs
    ALGORITMOS["DFS"] = dfs
except ImportError:
    pass

INF = float("inf")


def _caminho(pais, destino):
    saida, atual, vistos = [], destino, set()
    while atual is not None and atual not in vistos:
        vistos.add(atual)
        saida.append(atual)
        atual = pais.get(atual)
    saida.reverse()
    return saida


def _cabecalho(titulo):
    print()
    print(titulo)
    print("-" * len(titulo))


def comando_metricas(grade, fonte):
    grafo = construir_g_est(grade, fonte=fonte)
    pos = construir_g_pos(grade)
    teto = teto_teorico(grade, fonte=fonte)
    # [IA] Claude Code – correção de bug (metricas do G_est sem o no ALVO e sem os arcos que chegam nele)
    sem_alvo = gr.subgrafo_induzido(grafo, [n for n in grafo if n != ALVO])
    ordem = gr.ordem(sem_alvo)
    _cabecalho("Metricas")
    print(f"  G_pos : ordem {gr.ordem(pos)}, tamanho {gr.tamanho(pos)}, "
          f"densidade {gr.densidade(pos):.6f}")
    print(f"  G_est : ordem {ordem}, tamanho {gr.tamanho(sem_alvo)}, "
          f"densidade {gr.densidade(sem_alvo):.6f}")
    print(f"  teto teorico {teto}  ocupacao {100 * ordem / teto:.1f}%")
    return grafo


def comando_algoritmo(grafo, grade, nome, fonte, mostrar_caminho):
    if nome not in ALGORITMOS:
        print(f"  {nome}: nao implementado em algorithms.py", file=sys.stderr)
        return 1
    inicio = estado_inicial(grade)
    _cabecalho(nome)

    if nome == "DFS":
        resultado = ALGORITMOS[nome](grafo, inicio)
        visitados = sum(1 for v in resultado[0].values() if v == "ENCERRADO")

        tipos = {"arvore": 0, "retorno": 0, "avanco": 0, "cruzamento": 0}

        for _, _, tipo in classificar_arcos(grafo, inicio):
            tipos[tipo] += 1

        print(f"  visitou {visitados} de {gr.ordem(grafo)} vertices")
        print(f"  arcos de arvore: {tipos['arvore']}")
        print(f"  arcos de retorno: {tipos['retorno']}")
        print(f"  arcos de avanco: {tipos['avanco']}")
        print(f"  arcos de cruzamento: {tipos['cruzamento']}")
        print(f"  possui ciclo: {'SIM' if tipos['retorno'] > 0 else 'NAO'}")

        return 0

    try:
        resultado = ALGORITMOS[nome](grafo, inicio)
    except ValueError as erro:
        print(f"  status  RECUSA")
        print(f"  motivo  {erro}")
        return 0

    dist, pais = resultado[0], resultado[1]
    ciclo = resultado[2] if len(resultado) > 2 else None

    if ciclo:
        peso = {(u, v): p for u in grafo for v, p in grafo[u]}
        soma = sum(peso[(ciclo[i], ciclo[i + 1])]
                   for i in range(len(ciclo) - 1))

        print("  status  CICLO_NEGATIVO")
        print("  ciclo  ", " -> ".join(rotular(e) for e in ciclo))
        print(f"  custo do ciclo: {soma}")
        return 0

    if dist.get(ALVO, INF) == INF:
        print("  status  SEM_SOLUCAO")
        print(f"  estados alcancaveis: {gr.ordem(grafo) - 1}")
        return 0

    caminho = [e for e in _caminho(pais, ALVO) if e != ALVO]
    print("  status  OK")
    if nome == "BFS":
        # [IA] Claude Code – correção de bug (passos do BFS sem contar o arco virtual G -> ALVO)
        print(f"  passos  {len(caminho) - 1}")
    else:
        print(f"  custo   {dist[ALVO]}")
        print(f"  passos  {len(caminho) - 1}")
    if mostrar_caminho:
        print("  caminho")
        for i, e in enumerate(caminho):
            print(f"    {i:4}  {rotular(e):22} custo {dist[e]}")
    return 0


# [IA] Claude Code – rodar um algoritmo no G_pos (prova do m05)
def comando_algoritmo_gpos(grade, nome):
    """Roda o algoritmo no grafo de posicoes, a partir de S. Nao ha ALVO aqui."""
    from src.graphs.io import achar_inicio, achar_saida
    if nome not in ALGORITMOS or nome == "DFS":
        print(f"  {nome}: use BFS, DIJKSTRA ou BELLMAN_FORD com --gpos", file=sys.stderr)
        return 1
    pos = construir_g_pos(grade)
    inicio = achar_inicio(grade)
    _cabecalho(f"{nome} no G_pos")
    try:
        resultado = ALGORITMOS[nome](pos, inicio)
    except ValueError as erro:
        print("  status  RECUSA")
        print(f"  motivo  {erro}")
        return 0
    dist, ciclo = resultado[0], (resultado[2] if len(resultado) > 2 else None)
    if ciclo:
        peso = {(u, v): w for u in pos for v, w in pos[u]}
        soma = sum(peso[(ciclo[i], ciclo[i + 1])] for i in range(len(ciclo) - 1))
        print("  status  CICLO_NEGATIVO")
        print("  ciclo  ", " -> ".join(rotular(e) for e in ciclo), f"(custo {soma})")
        return 0
    saidas = [s for s in achar_saida(grade) if dist.get(s, INF) != INF]
    if not saidas:
        print("  status  SEM_SOLUCAO")
        return 0
    melhor = min(saidas, key=lambda s: dist[s])
    print("  status  OK")
    print(f"  {'passos' if nome == 'BFS' else 'custo '}  {dist[melhor]}")
    return 0


def comando_armadilhas(grafo):
    _cabecalho("Estados-armadilha")
    if "BELLMAN_FORD" not in ALGORITMOS and "BFS" not in ALGORITMOS:
        print("  preciso de bfs() ou bellman_ford() para a busca no transposto",
              file=sys.stderr)
        return 1
    funcao = ALGORITMOS.get("BFS") or ALGORITMOS["BELLMAN_FORD"]
    alcanca = funcao(gr.transposto(grafo), ALVO)[0]
    estados = [e for e in grafo if e != ALVO]
    presos = [e for e in estados if alcanca.get(e, INF) == INF]
    print(f"  alcancaveis do inicio : {len(estados)}")
    print(f"  chegam no ALVO        : {len(estados) - len(presos)}")
    print(f"  ARMADILHAS            : {len(presos)} "
          f"({100 * len(presos) / max(1, len(estados)):.0f}%)")
    for e in sorted(presos)[:40]:
        print(f"    {rotular(e)}")
    if len(presos) > 40:
        print(f"    ... e mais {len(presos) - 40}")
    return 0


def comando_graus(grafo):
    _cabecalho("Graus")
    becos = [n for n in grafo if n != ALVO and gr.grau_saida(grafo, n) == 0]

    grafo = gr.subgrafo_induzido(grafo, [n for n in grafo if n != ALVO])

    entrada = gr.graus_entrada(grafo)
    saida = {n: gr.grau_saida(grafo, n) for n in grafo}

    maior_s = min(grafo, key=lambda n: (-saida[n], rotular(n)))
    maior_e = min(grafo, key=lambda n: (-entrada[n], rotular(n)))

    print(f"  maior grau de saida   {rotular(maior_s)}  ({saida[maior_s]})")
    print(f"  maior grau de entrada {rotular(maior_e)}  ({entrada[maior_e]})")
    print(f"  estados sem saida     {len(becos)}")
    return 0

def comando_dataset(args):
    from src.graphs.io import ler_dataset_bitcoin_alpha
    from src.parte2.construcao import construir_grafo
    from src.parte2.painel import PainelParte2
    from src.solve import gerar_parte2
    import json

    caminho = args.dataset

    if os.path.isdir(caminho):
        caminho = os.path.join(
            caminho, "soc-sign-bitcoinalpha.csv"
        )

    if not os.path.isfile(caminho):
        print(f"Dataset nao encontrado: {caminho}")
        return 2

    if args.benchmark:
        destino = gerar_parte2(
            dataset=caminho,
            pasta=args.out
        )

        print(f"Relatorio gerado: {destino}")
        return 0

    if not args.alg:
        print("Informe --alg ou --benchmark.")
        return 2

    if args.source is None or args.target is None:
        print("Informe --source e --target.")
        return 2

    grafo = construir_grafo(
        ler_dataset_bitcoin_alpha(caminho)
    )

    print(f"Dataset: {caminho}")
    print(f"Vertices: {len(grafo)}")
    print(f"Arcos: {sum(len(v) for v in grafo.values())}")
    print(f"Algoritmo: {args.alg}")
    print(f"Origem: {args.source}")
    print(f"Destino: {args.target}")

    painel = PainelParte2(dataset=caminho)

    try:
        resultado = painel.rodar(
            args.alg,
            args.source,
            args.target
        )
    except ValueError as erro:
        print(f"Erro: {erro}")
        return 2

    print(json.dumps(
        resultado,
        indent=2,
        ensure_ascii=False
    ))

    os.makedirs(args.out, exist_ok=True)

    destino = os.path.join(
        args.out,
        f"{args.alg.lower()}_resultado.json"
    )

    with open(destino, "w", encoding="utf-8") as arquivo:
        json.dump(
            resultado,
            arquivo,
            indent=2,
            ensure_ascii=False
        )

    print(f"Resultado salvo em: {destino}")

    return 0

def main(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m src.cli",
        description="Labirinto com chaves: grafo de estados e algoritmos.")
    p.add_argument("--mapa", help="caminho de um mapa .txt")
    p.add_argument("--dataset", help="pasta do dataset da Parte 2")
    p.add_argument("--alg", choices=["BFS", "DFS", "DIJKSTRA", "BELLMAN_FORD"],
                   help="algoritmo a rodar")
    p.add_argument("--fonte", choices=["infinita", "consumivel"], default="infinita",
                   help="tratamento da fonte '*' (padrao: infinita)")
    # [IA] Claude Code – opcao --fonte-consumivel (nome do enunciado) e --gpos
    p.add_argument("--fonte-consumivel", dest="fonte", action="store_const", const="consumivel",
                   help="correcao do m06: a fonte '*' vale -2 so na primeira vez")
    p.add_argument("--gpos", action="store_true",
                   help="rodar o algoritmo no grafo de posicoes (G_pos), com '+' valendo -4 fixo")
    p.add_argument("--armadilhas", action="store_true",
                   help="listar os estados-armadilha")
    p.add_argument("--graus", action="store_true",
                   help="maior grau de entrada/saida e becos")
    p.add_argument("--metricas", action="store_true",
                   help="ordem, tamanho, densidade, teto teorico")
    p.add_argument("--caminho", action="store_true",
                   help="imprimir o percurso estado a estado")
    p.add_argument("--interactive", action="store_true",
                   help="gerar o labirinto_interativo.html")
    p.add_argument("--figuras", action="store_true",
                   help="gerar as figuras da Secao 8")
    p.add_argument("--source", help="Parte 2: vertice de origem")
    p.add_argument("--target", help="Parte 2: vertice de destino")
    p.add_argument("--benchmark", action="store_true", help="Parte 2: medir tempos")
    p.add_argument("--out", default="out/parte1/", help="pasta de saida")
    args = p.parse_args(argv)

    if args.dataset:
        return comando_dataset(args)

    if args.interactive or args.figuras:
        from src import viz
        os.makedirs(args.out, exist_ok=True)
        if args.interactive:
            destino, dados = viz.gerar_html(
                [args.mapa] if args.mapa else None,
                os.path.join(args.out, "labirinto_interativo.html"))
            print(f"gerado {destino} ({len(dados)} mapa(s))")
        if args.figuras:
            for f in viz.gerar_figuras():
                print(f"gerado {f}")
        return 0

    if not args.mapa:
        p.error("informe --mapa (ou --dataset)")

    if not os.path.exists(args.mapa):
        print(f"mapa nao encontrado: {args.mapa}", file=sys.stderr)
        return 2

    try:
        grade = ler_mapa(args.mapa)
    except ValueError as erro:
        print(f"mapa invalido: {erro}", file=sys.stderr)
        return 2

    print(f"mapa    {args.mapa}")
    print(f"grade   {len(grade)} x {len(grade[0])}")
    print(f"fonte   {args.fonte}")

    grafo = None
    if args.metricas or not (args.alg or args.armadilhas or args.graus):
        grafo = comando_metricas(grade, args.fonte)
    if grafo is None:
        grafo = construir_g_est(grade, fonte=args.fonte)

    codigo = 0
    if args.alg and args.gpos:
        codigo |= comando_algoritmo_gpos(grade, args.alg)
    elif args.alg:
        codigo |= comando_algoritmo(grafo, grade, args.alg, args.fonte, args.caminho)
    if args.graus:
        codigo |= comando_graus(grafo)
    if args.armadilhas:
        codigo |= comando_armadilhas(grafo)
    return codigo


if __name__ == "__main__":
    sys.exit(main())
