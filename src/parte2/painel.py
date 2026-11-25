# [IA] Claude Code – front/UX (orquestracao da Parte 2 para o servidor local)
"""
painel.py  -  dados da Parte 2 para o front (src/web/index.html).


Este modulo NAO implementa algoritmo nenhum. Ele:
  - monta o grafo com as funcoes do grupo (io.ler_dataset_bitcoin_alpha +
    parte2.construcao.construir_grafo);
  - chama as funcoes de src/graphs/algorithms.py (bfs, dfs_distancias,
    dijkstra, bellman_ford) e so formata a saida para a pagina;
  - le os resultados que ja estao em out/parte2/parte2_report.json;
  - le a pergunta de pesquisa e a lista de figuras de AVD do notebook do grupo.

Usado pelo src/servidor.py (rotas /api/parte2/...).
"""

import json
import os
import threading
from time import perf_counter

from src.graphs import graph as gr
from src.graphs.algorithms import bellman_ford, bfs, dfs_distancias, dijkstra
from src.graphs.io import ler_dataset_bitcoin_alpha
from src.parte2.construcao import construir_grafo
from src.parte2.exportar_figuras import FIGURAS, NOTEBOOK
from src.viz import _reconstruir

DATASET = os.path.join("data", "dataset_parte2", "soc-sign-bitcoinalpha.csv")
RELATORIO = os.path.join("out", "parte2", "parte2_report.json")
PASTA_FIGURAS = os.path.join("out", "parte2")
# [IA] Claude Code – front/UX (aba AVD: celulas 22, 23, 24, 32 e 54 = exploratoria; 63 e 65 = explanatoria)
CELULAS_EXPLANATORIA = {63, 65}

# nome na pagina -> funcao do grupo
ALGORITMOS = {
    "BFS": bfs,
    "DFS": dfs_distancias,
    "DIJKSTRA": dijkstra,
    "BELLMAN_FORD": bellman_ford,
}

# o que o numero "distancia" significa em cada algoritmo (so rotulo para a pagina)
MEDIDA = {
    "BFS": "distância (nº de arcos)",
    "DFS": "custo do caminho na árvore DFS (soma dos pesos)",
    "DIJKSTRA": "custo mínimo (soma dos pesos)",
    "BELLMAN_FORD": "custo mínimo (soma dos pesos)",
}

INF = float("inf")


def pergunta_de_pesquisa(notebook=NOTEBOOK):
    """Texto da pergunta, copiado da secao "Pergunta de Pesquisa" do notebook (sem os marcadores ** e >)."""
    with open(notebook, encoding="utf-8") as arquivo:
        celulas = json.load(arquivo)["cells"]
    for celula in celulas:
        if celula.get("cell_type") != "markdown":
            continue
        linhas = "".join(celula.get("source", [])).split("\n")
        if not any(l.strip().lstrip("#").strip() == "Pergunta de Pesquisa" for l in linhas):
            continue
        for linha in linhas:
            if linha.strip().startswith(">"):
                return linha.strip().lstrip(">").strip().replace("**", "")
    return None


class PainelParte2:
    def __init__(self, dataset=DATASET, relatorio=RELATORIO):
        self.dataset = dataset
        self.caminho_relatorio = relatorio
        self._grafo = None
        self._relatorio = None
        self._cache = {}                    # (algoritmo, origem) -> (saida, tempo_s)
        self._trava_grafo = threading.Lock()
        self._trava_execucao = threading.Lock()

    # ------------------------------------------------------------ grafo do grupo
    def grafo(self):
        with self._trava_grafo:
            if self._grafo is None:
                self._grafo = construir_grafo(ler_dataset_bitcoin_alpha(self.dataset))
            return self._grafo

    def _peso(self, u, v):
        for destino, peso in self.grafo()[u]:
            if destino == v:
                return peso
        return None

    def resumo(self):
        g = self.grafo()
        pesos = [p for vizinhos in g.values() for _, p in vizinhos]
        return {
            "dataset": "Bitcoin Alpha (soc-sign-bitcoinalpha)",
            "vertices": gr.ordem(g),
            "arestas": gr.tamanho(g),
            "dirigido": True,
            "ponderado": True,
            "peso_min": min(pesos),
            "peso_max": max(pesos),
            "pergunta": pergunta_de_pesquisa(),
        }

    def dados_grafo(self):
        """Vertices (com graus) e arcos, para a pagina desenhar."""
        g = self.grafo()
        entrada = gr.graus_entrada(g)
        nos = [[v, entrada.get(v, 0), gr.grau_saida(g, v)] for v in g]
        arcos = [[u, v, p] for u, vizinhos in g.items() for v, p in vizinhos]
        return {"nos": nos, "arcos": arcos}

    # ------------------------------------------------------------ resultados ja salvos
    def relatorio(self):
        """Resumo do parte2_report.json (sem as listas enormes de ordem/pais/arcos)."""
        if self._relatorio is None:
            with open(self.caminho_relatorio, encoding="utf-8") as arquivo:
                r = json.load(arquivo)
            res = r["resultados"]
            bfs_linhas = []
            for item in res.get("BFS", []):
                camadas = sorted(((int(n), len(vs)) for n, vs in item["camadas"].items()))
                bfs_linhas.append({
                    "fonte": item["fonte"],
                    "vertices_visitados": item["vertices_visitados"],
                    "n_camadas": len(camadas),
                    "camadas": [qtd for _, qtd in camadas],
                    "tempo_medio_s": item["tempo_medio_s"],
                    "tempos_s": item["tempos_s"],
                })
            dfs_linhas = [{
                "fonte": item["fonte"],
                "vertices_visitados": item["vertices_visitados"],
                "classificacao_arcos": item["classificacao_arcos"],
                "tem_ciclo": item["tem_ciclo"],
                "tempo_medio_s": item["tempo_medio_s"],
                "tempos_s": item["tempos_s"],
            } for item in res.get("DFS", [])]
            bf = {}
            for nome, caso in res.get("BELLMAN_FORD", {}).items():
                bf[nome] = {k: v for k, v in caso.items()
                            if k not in ("distancias", "pais") or len(v) <= 20}
            self._relatorio = {
                "dataset": r.get("dataset"),
                "vertices": r.get("vertices"),
                "arestas": r.get("arestas"),
                "BFS": bfs_linhas,
                "DFS": dfs_linhas,
                "BELLMAN_FORD": bf,
            }
        return self._relatorio

    def figuras(self):
        # [IA] Claude Code – front/UX (secao de cada figura na aba AVD, pela celula do notebook)
        return [{"arquivo": nome, "titulo": titulo, "celula": indice,
                 "secao": "explanatoria" if indice in CELULAS_EXPLANATORIA else "exploratoria",
                 "existe": os.path.exists(os.path.join(PASTA_FIGURAS, nome))}
                for nome, titulo, _trecho, indice in FIGURAS]

    # ------------------------------------------------------------ rodar um algoritmo do grupo
    def _executar(self, algoritmo, origem):
        """Chama a funcao do grupo (com cache: o Bellman-Ford no grafo inteiro leva ~30 s)."""
        chave = (algoritmo, origem)
        if chave in self._cache:
            saida, tempo = self._cache[chave]
            return saida, tempo, True
        inicio = perf_counter()
        saida = ALGORITMOS[algoritmo](self.grafo(), origem)
        tempo = perf_counter() - inicio
        if len(self._cache) >= 16:
            self._cache.pop(next(iter(self._cache)))
        self._cache[chave] = (saida, tempo)
        return saida, tempo, False

    def rodar(self, algoritmo, origem, destino):
        algoritmo = str(algoritmo).upper()
        if algoritmo not in ALGORITMOS:
            raise ValueError(f"algoritmo desconhecido: {algoritmo}")
        g = self.grafo()
        try:
            origem, destino = int(origem), int(destino)
        except (TypeError, ValueError):
            raise ValueError("origem e destino precisam ser números de vértice")
        for nome, v in (("origem", origem), ("destino", destino)):
            if v not in g:
                raise ValueError(f"o vértice {v} ({nome}) não existe no grafo")

        base = {"algoritmo": algoritmo, "origem": origem, "destino": destino,
                "medida": MEDIDA[algoritmo]}
        with self._trava_execucao:
            try:
                saida, tempo, em_cache = self._executar(algoritmo, origem)
            except ValueError as erro:          # Dijkstra do grupo recusa peso negativo
                # [IA] Claude Code – front/UX (recusa e o comportamento exigido: so status + mensagem do grupo)
                return {**base, "status": "RECUSA", "mensagem": str(erro)}

        dist, pais = saida[0], saida[1]
        ciclo = saida[2] if len(saida) > 2 else None
        alcancados = sum(1 for d in dist.values() if d != INF)
        base.update({"tempo_s": tempo, "em_cache": em_cache, "alcancados": alcancados})

        if ciclo:
            pesos = [self._peso(u, v) for u, v in zip(ciclo, ciclo[1:])]
            return {**base, "status": "CICLO_NEGATIVO", "ciclo": ciclo,
                    "pesos_ciclo": pesos, "custo_ciclo": sum(pesos)}

        if dist.get(destino, INF) == INF:
            return {**base, "status": "SEM_CAMINHO"}

        caminho = _reconstruir(pais, destino)
        if not caminho or caminho[0] != origem:
            return {**base, "status": "SEM_CAMINHO"}
        pesos = [self._peso(u, v) for u, v in zip(caminho, caminho[1:])]
        resultado = {**base, "status": "OK", "distancia": dist[destino], "caminho": caminho,
                     "pesos_caminho": pesos, "n_arcos": len(caminho) - 1, "soma_pesos": sum(pesos)}
        if algoritmo == "BFS":
            # sugestoes de destino: os vertices do ultimo nivel que a bfs do grupo devolveu
            fundo = max(dist.values())
            resultado["mais_distantes"] = sorted(v for v, d in dist.items() if d == fundo)[:6]
            resultado["nivel_maximo"] = fundo
        return resultado
