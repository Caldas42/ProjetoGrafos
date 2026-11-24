"""
servidor.py  -  pagina interativa com upload de mapas novos.

[IA] Claude Code – servidor local (so orquestracao/UX, nenhum algoritmo aqui).

Sobe um servidor web NA PROPRIA MAQUINA (127.0.0.1) que:
  - serve o labirinto interativo com todos os mapas de data/mapas e data/mapas_grupo;
  - recebe um mapa .txt enviado pela pagina (botao "Carregar mapa"), roda nele
    o mesmo viz.coletar() de sempre - ou seja, io.py + estados.py + algorithms.py
    do grupo - e devolve o resultado para a pagina desenhar.

Uso:
    python -m src.servidor              # abre http://127.0.0.1:8765
    python -m src.servidor --porta 9000
    python -m src.servidor --sem-navegador

Os mapas enviados ficam salvos em out/parte1/mapas_enviados/, para poderem
ser rodados tambem pelo CLI (python -m src.cli --mapa ...).
"""

import argparse
import json
import os
import re
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src import viz

PASTA_ENVIADOS = os.path.join("out", "parte1", "mapas_enviados")
LIMITE_BYTES = 200_000          # um mapa de texto nunca chega perto disso
LIMITE_CASAS = 60 * 60          # protege contra mapa gigante travar o servidor


def _nome_seguro(nome, existentes):
    """Nome do arquivo sem caminho/extensao, so com caracteres simples, sem colidir com os mapas do projeto."""
    base = os.path.splitext(os.path.basename(nome or "mapa"))[0]
    base = re.sub(r"[^A-Za-z0-9_-]+", "_", base).strip("_") or "mapa"
    base = base[:40]
    return base if base not in existentes else base + "_enviado"


class Servidor:
    def __init__(self):
        self.dados = {}
        self.trava = threading.Lock()

    def carregar_mapas_do_projeto(self):
        # mesmos mapas e mesma coleta do "python -m src.viz html"
        _, self.dados = viz.gerar_html(None, os.path.join("out", "parte1", "labirinto_interativo.html"))
        self.projeto = set(self.dados)

    def pagina(self):
        with self.trava:
            return viz._montar_pagina(self.dados)

    def receber_mapa(self, nome, texto):
        texto = texto.replace("\r\n", "\n").replace("\r", "\n")
        linhas = [l for l in texto.split("\n") if l.strip()]
        if not linhas:
            raise ValueError("o arquivo está vazio")
        if len(linhas) * max(len(l) for l in linhas) > LIMITE_CASAS:
            raise ValueError(f"mapa grande demais para a página (limite de {LIMITE_CASAS} casas)")

        nome = _nome_seguro(nome, self.projeto)
        os.makedirs(PASTA_ENVIADOS, exist_ok=True)
        caminho = os.path.join(PASTA_ENVIADOS, nome + ".txt")
        with open(caminho, "w", encoding="ascii", errors="replace", newline="\n") as arquivo:
            arquivo.write(texto if texto.endswith("\n") else texto + "\n")

        try:
            info = viz.coletar(caminho)    # io.ler_mapa valida; os algoritmos sao os do grupo
        except Exception:
            os.remove(caminho)             # mapa recusado nao fica salvo
            raise
        info["nome"] = nome
        info["enviado"] = True
        with self.trava:
            self.dados[nome] = info
        return info


def criar_handler(servidor):
    class Handler(BaseHTTPRequestHandler):
        def _responder(self, codigo, corpo, tipo):
            dados = corpo.encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dados)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(dados)

        def _json(self, codigo, obj):
            self._responder(codigo, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

        def do_GET(self):
            caminho = self.path.split("?")[0]
            if caminho in ("/", "/index.html", "/labirinto_interativo.html"):
                self._responder(200, servidor.pagina(), "text/html; charset=utf-8")
            elif caminho == "/api/ping":
                self._json(200, {"ok": True, "mapas": len(servidor.dados)})
            else:
                self._json(404, {"erro": "não encontrado"})

        def do_POST(self):
            if self.path.split("?")[0] != "/api/mapa":
                self._json(404, {"erro": "não encontrado"})
                return
            tamanho = int(self.headers.get("Content-Length") or 0)
            if tamanho <= 0 or tamanho > LIMITE_BYTES:
                self._json(400, {"erro": "arquivo vazio ou grande demais"})
                return
            try:
                pedido = json.loads(self.rfile.read(tamanho).decode("utf-8"))
                info = servidor.receber_mapa(str(pedido.get("nome", "")), str(pedido.get("texto", "")))
            except ValueError as erro:          # mapa invalido: mensagem do io.py
                self._json(400, {"erro": str(erro)})
                return
            except Exception as erro:
                self._json(500, {"erro": f"{type(erro).__name__}: {erro}"})
                return
            print(f"  mapa recebido: {info['nome']} ({info['linhas']}x{info['colunas']})")
            self._json(200, info)

        def log_message(self, formato, *args):    # silencia o log de cada requisicao
            pass

    return Handler


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m src.servidor",
                                description="Labirinto interativo com upload de mapas (servidor local).")
    p.add_argument("--porta", type=int, default=8765)
    p.add_argument("--sem-navegador", action="store_true", help="nao abrir o navegador sozinho")
    args = p.parse_args(argv)

    servidor = Servidor()
    print("calculando os mapas do projeto...")
    servidor.carregar_mapas_do_projeto()

    try:
        http = ThreadingHTTPServer(("127.0.0.1", args.porta), criar_handler(servidor))
    except OSError:
        print(f"a porta {args.porta} ja esta em uso; tente --porta 9000", file=sys.stderr)
        return 1

    endereco = f"http://127.0.0.1:{args.porta}/"
    print(f"\nlabirinto interativo em {endereco}")
    print("use o botao 'Carregar mapa' na Parte 1. Ctrl+C para desligar.\n")
    if not args.sem_navegador:
        threading.Timer(0.6, lambda: webbrowser.open(endereco + "#parte1")).start()
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        print("\nservidor desligado.")
    finally:
        http.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
