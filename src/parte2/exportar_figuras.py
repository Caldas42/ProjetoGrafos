# [IA] Claude Code – front/UX (exportacao das figuras do notebook para a aba AVD)
"""
exportar_figuras.py  -  copia os graficos de AVD do notebook para out/parte2/.


Nao gera grafico nenhum: so le as imagens PNG que JA ESTAO salvas nas saidas
das celulas do notebook do grupo e grava cada uma num arquivo com nome
descritivo. Os graficos foram escolhidos pelo grupo; o mapeamento celula ->
arquivo foi confirmado pelo grupo (celulas 22, 23, 24, 32, 54, 63 e 65).

Cada figura e achada por um trecho do codigo da celula (o titulo do grafico),
e nao so pelo indice: se o notebook ganhar ou perder celulas, o script continua
achando a celula certa - e para com erro se o trecho sumir ou ficar ambiguo.

Uso:
    python -m src.parte2.exportar_figuras
"""

import base64
import json
import os
import sys

NOTEBOOK = os.path.join(
    "docs",
    "Analise_Exploratoria_e_Explanatoria_do_Dataset_Bitcoin_Alpha_Trust_Weight_Signed_Network.ipynb",
)
PASTA = os.path.join("out", "parte2")

# (arquivo de saida, titulo exibido na pagina, trecho unico do codigo da celula, indice confirmado)
FIGURAS = [
    ("avd_01_distribuicoes_variaveis_quantitativas.png",
     "Distribuições das variáveis quantitativas",
     "Distribuição das Variáveis Quantitativas", 22),
    ("avd_02_rating_countplot.png",
     "Distribuição de RATING (countplot)",
     "(Countplot)", 23),
    ("avd_03_rating_por_ano.png",
     "Distribuição de RATING por ano",
     "Distribuição de RATING Separada por Ano", 24),
    ("avd_04_ecdf_rating_por_ano.png",
     "ECDF de RATING acumulada por ano",
     "ECDF — Curva de RATING Acumulada por Ano", 32),
    ("avd_05_correlacao_spearman.png",
     "Matriz de correlação (Spearman) das variáveis quantitativas",
     "Matriz de Correlação (Spearman) — Variáveis Quantitativas", 54),
    ("avd_06_explanatoria_extremos_reputacao.png",
     "Visualização 1: Evolução da Confiança Máxima vs. Detecção de Risco (2011 - 2014)",
     "Evolução dos Extremos de Reputação", 63),
    ("avd_07_explanatoria_usuarios_mais_avaliados.png",
     "Visualização 2: Identificação de Membros-Chave e Assimetria de Reputação",
     "Os 8 Usuários Mais Avaliados", 65),
]


def _png_da_celula(celula):
    """Lista das imagens PNG (bytes) nas saidas de uma celula de codigo."""
    imagens = []
    for saida in celula.get("outputs", []):
        dado = saida.get("data", {}).get("image/png")
        if dado:
            texto = "".join(dado) if isinstance(dado, list) else dado
            imagens.append(base64.b64decode(texto))
    return imagens


def localizar(celulas, trecho):
    """Indice da UNICA celula de codigo com imagem cujo codigo contem `trecho`."""
    achadas = [
        i for i, c in enumerate(celulas)
        if c.get("cell_type") == "code"
        and trecho in "".join(c.get("source", []))
        and _png_da_celula(c)
    ]
    if len(achadas) != 1:
        raise ValueError(f"trecho {trecho!r}: esperado 1 celula com imagem, achadas {achadas}")
    return achadas[0]


def exportar(notebook=NOTEBOOK, pasta=PASTA):
    with open(notebook, encoding="utf-8") as arquivo:
        celulas = json.load(arquivo)["cells"]

    os.makedirs(pasta, exist_ok=True)
    gerados = []
    for nome, _titulo, trecho, indice_confirmado in FIGURAS:
        indice = localizar(celulas, trecho)
        if indice != indice_confirmado:
            print(f"  ! {nome}: a celula mudou de lugar ({indice_confirmado} -> {indice}); confira o notebook")
        imagens = _png_da_celula(celulas[indice])
        if len(imagens) != 1:
            raise ValueError(f"celula {indice}: esperada 1 imagem, achadas {len(imagens)}")
        destino = os.path.join(pasta, nome)
        with open(destino, "wb") as arquivo:
            arquivo.write(imagens[0])
        gerados.append((destino, indice))
    return gerados


def main():
    for destino, indice in exportar():
        print(f"{destino}  (celula {indice}, {os.path.getsize(destino) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
