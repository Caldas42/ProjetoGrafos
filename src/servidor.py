"""
servidor.py  -  front do projeto (Parte 1 e Parte 2) com upload de mapas novos.

[IA] Claude Code – servidor local (so orquestracao/UX, nenhum algoritmo aqui).

Sobe um servidor web NA PROPRIA MAQUINA (127.0.0.1) que:
  - [IA] Claude Code – front/UX: serve o front unico (src/web/index.html) com a
    home, a Parte 1 (o labirinto abaixo, embutido) e a Parte 2 (Bitcoin Alpha);
  - [IA] Claude Code – front/UX: na Parte 2, monta o grafo com io.py + construcao.py
    e chama as funcoes de algorithms.py do grupo (rota POST /api/parte2/rodar);
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
from src.parte2.painel import PASTA_FIGURAS, PainelParte2   # [IA] Claude Code – front/UX (Parte 2 no front unico)

PASTA_ENVIADOS = os.path.join("out", "parte1", "mapas_enviados")
LIMITE_BYTES = 200_000          # um mapa de texto nunca chega perto disso
LIMITE_CASAS = 60 * 60          # protege contra mapa gigante travar o servidor

# [IA] Claude Code – front/UX (front unico: home + Parte 1 + Parte 2)
PASTA_WEB = viz.PASTA_WEB
PASTA_VENDOR = os.path.join(PASTA_WEB, "vendor")
TIPOS = {".js": "text/javascript; charset=utf-8", ".png": "image/png"}

# Quando a Parte 1 abre DENTRO do front unico (iframe), o servidor acrescenta este
# trecho ao labirinto: esconde o "Inicio" e o botao de tema proprios (o front ja tem
# os dele) e segue o tema escolhido no front. O arquivo gerado pelo
# "python -m src.viz" (out/parte1/labirinto_interativo.html) NAO recebe este trecho.
COLA_PARTE1 = """
<!-- [IA] Claude Code – front/UX (Parte 1 embutida no front unico; so aparece via src/servidor.py) -->
<style>
  .icone.voltar, button[aria-label="Alternar tema claro/escuro"]{display:none!important}
</style>
<script>
(function(){
  var desejado = new URLSearchParams(location.search).get("tema");
  function aplicar(){
    if (desejado && document.documentElement.getAttribute("data-theme") !== desejado)
      document.documentElement.setAttribute("data-theme", desejado);
  }
  new MutationObserver(aplicar).observe(document.documentElement, {attributes:true, attributeFilter:["data-theme"]});
  aplicar();
  window.addEventListener("message", function(e){
    if (e.origin === location.origin && e.data && e.data.tema){ desejado = e.data.tema; aplicar(); }
  });
  function ficarNaParte1(){ if (location.hash !== "#parte1") location.replace("#parte1"); }
  window.addEventListener("hashchange", ficarNaParte1);
  ficarNaParte1();
})();
</script>
"""


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
        self.parte2 = PainelParte2()     # [IA] Claude Code – front/UX (Parte 2)

    def carregar_mapas_do_projeto(self):
        # mesmos mapas e mesma coleta do "python -m src.viz html"
        _, self.dados = viz.gerar_html(None, os.path.join("out", "parte1", "labirinto_interativo.html"))
        self.projeto = set(self.dados)

    def pagina(self):
        with self.trava:
            return viz._montar_pagina(self.dados)

    # [IA] Claude Code – front/UX (front unico)
    def pagina_embutida(self):
        """Labirinto da Parte 1 com o trecho que o encaixa no front unico."""
        html = self.pagina()
        corte = html.rfind("</body>")
        return html[:corte] + COLA_PARTE1 + html[corte:]

    def front(self):
        with open(os.path.join(PASTA_WEB, "index.html"), encoding="utf-8") as arquivo:
            return arquivo.read()

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

        # [IA] Claude Code – front/UX (arquivos estaticos: bibliotecas e figuras de AVD)
        def _arquivo(self, pasta, nome, permitidos):
            if nome not in permitidos:          # so nomes da lista: nada de "../"
                self._json(404, {"erro": "não encontrado"})
                return
            with open(os.path.join(pasta, nome), "rb") as arquivo:
                dados = arquivo.read()
            self.send_response(200)
            self.send_header("Content-Type", TIPOS.get(os.path.splitext(nome)[1], "application/octet-stream"))
            self.send_header("Content-Length", str(len(dados)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(dados)

        def do_GET(self):
            caminho = self.path.split("?")[0]
            # [IA] Claude Code – front/UX (front unico na raiz; o labirinto sozinho continua em /labirinto_interativo.html)
            if caminho in ("/", "/index.html"):
                self._responder(200, servidor.front(), "text/html; charset=utf-8")
            elif caminho == "/labirinto_interativo.html":
                self._responder(200, servidor.pagina(), "text/html; charset=utf-8")
            elif caminho == "/parte1":
                self._responder(200, servidor.pagina_embutida(), "text/html; charset=utf-8")
            elif caminho.startswith("/vendor/"):
                self._arquivo(PASTA_VENDOR, caminho[len("/vendor/"):], set(os.listdir(PASTA_VENDOR)))
            elif caminho.startswith("/parte2/figuras/"):
                nomes = {f["arquivo"] for f in servidor.parte2.figuras() if f["existe"]}
                self._arquivo(PASTA_FIGURAS, caminho[len("/parte2/figuras/"):], nomes)
            elif caminho == "/api/ping":
                self._json(200, {"ok": True, "mapas": len(servidor.dados)})
            elif caminho == "/api/parte2/resumo":
                self._json(200, servidor.parte2.resumo())
            elif caminho == "/api/parte2/grafo":
                self._json(200, servidor.parte2.dados_grafo())
            elif caminho == "/api/parte2/relatorio":
                try:
                    self._json(200, servidor.parte2.relatorio())
                except FileNotFoundError:
                    self._json(404, {"erro": "out/parte2/parte2_report.json não existe (gere as saídas da Parte 2)"})
            elif caminho == "/api/parte2/figuras":
                self._json(200, servidor.parte2.figuras())
            else:
                self._json(404, {"erro": "não encontrado"})

        # [IA] Claude Code – front/UX (Parte 2: chama um algoritmo do grupo no grafo do dataset)
        def _rodar_parte2(self):
            tamanho = int(self.headers.get("Content-Length") or 0)
            try:
                pedido = json.loads(self.rfile.read(tamanho).decode("utf-8")) if 0 < tamanho < 10_000 else None
            except ValueError:
                pedido = None
            if not isinstance(pedido, dict):
                self._json(400, {"erro": "pedido inválido"})
                return
            try:
                resultado = servidor.parte2.rodar(pedido.get("algoritmo"), pedido.get("origem"), pedido.get("destino"))
            except ValueError as erro:
                self._json(400, {"erro": str(erro)})
                return
            except Exception as erro:
                self._json(500, {"erro": f"{type(erro).__name__}: {erro}"})
                return
            print(f"  parte 2: {resultado['algoritmo']} {resultado['origem']} -> {resultado['destino']}: {resultado['status']}")
            self._json(200, resultado)

        def do_POST(self):
            if self.path.split("?")[0] == "/api/parte2/rodar":    # [IA] Claude Code – front/UX (Parte 2)
                self._rodar_parte2()
                return
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
                                description="Front do projeto (Parte 1 e Parte 2) com upload de mapas (servidor local).")
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
    # [IA] Claude Code – front/UX (abre a home do front unico)
    print(f"\nfront do projeto em {endereco}  (Parte 1: {endereco}#parte1 · Parte 2: {endereco}#parte2)")
    print("use o botao 'Carregar mapa' na Parte 1. Ctrl+C para desligar.\n")
    if not args.sem_navegador:
        threading.Timer(0.6, lambda: webbrowser.open(endereco)).start()
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        print("\nservidor desligado.")
    finally:
        http.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
