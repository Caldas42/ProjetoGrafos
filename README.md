# Projeto Final — Teoria dos Grafos + AVD (2026.2)
## Labirinto com Chaves (Grafo de Estados) + Comparação de Algoritmos

> **TODO do grupo:** preencher turma, número do grupo e integrantes.

- **Turma:** 5A / 5B
- **Grupo nº:**
- **Integrantes:**

## O que é este projeto

Transformamos mapas de labirinto em texto num **grafo de estados** — onde cada nó é
`(posição, chaves que o jogador possui, bônus já consumidos)` — e rodamos BFS, DFS,
Dijkstra e Bellman-Ford (implementações próprias) sobre ele. Na Parte 2 aplicamos os
mesmos algoritmos a um dataset dirigido e ponderado maior.

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Como executar

```bash
# metricas do grafo de um mapa
python -m src.cli --mapa ./data/mapas/m03_tres_chaves.txt

# os quatro algoritmos
python -m src.cli --mapa ./data/mapas/m03_tres_chaves.txt --alg BFS
python -m src.cli --mapa ./data/mapas/m03_tres_chaves.txt --alg DIJKSTRA --caminho
python -m src.cli --mapa ./data/mapas/m05_bonus.txt       --alg BELLMAN_FORD
python -m src.cli --mapa ./data/mapas/m03_tres_chaves.txt --alg DFS

# Dijkstra recusa grafo com peso negativo
python -m src.cli --mapa ./data/mapas/m05_bonus.txt --alg DIJKSTRA

# correcao de regra da fonte: o ciclo negativo do m06 desaparece
python -m src.cli --mapa ./data/mapas/m06_fonte.txt --alg BELLMAN_FORD
python -m src.cli --mapa ./data/mapas/m06_fonte.txt --alg BELLMAN_FORD --fonte consumivel

# estados-armadilha e graus
python -m src.cli --mapa ./data/mapas/m04_esteiras.txt --armadilhas
python -m src.cli --mapa ./data/mapas/m07_impossivel.txt --armadilhas
python -m src.cli --mapa ./data/mapas/m08_grande.txt --graus

# visualizacoes
python -m src.cli --interactive --out ./out/parte1/
python -m src.cli --figuras     --out ./out/parte1/
python -m src.viz                                    # html + figuras de uma vez
```

## Testar um mapa novo

**Pelo terminal** (qualquer arquivo `.txt`):

```bash
python -m src.cli --mapa caminho/do/mapa_novo.txt --alg BFS
python -m src.cli --mapa caminho/do/mapa_novo.txt --alg BELLMAN_FORD --caminho
```

**Pela página, com upload:**

```bash
python -m src.servidor          # abre http://127.0.0.1:8765 no navegador
```

Na Parte 1, use o botão **Carregar mapa** e escolha o `.txt`. O servidor roda localmente
(na própria máquina, sem internet) e calcula o mapa com o mesmo código do CLI
(`io.py`, `estados.py`, `algorithms.py`); a página só desenha o resultado. Mapas inválidos
são recusados com a mensagem de validação. Os mapas enviados ficam em
`out/parte1/mapas_enviados/`. Abrindo o `labirinto_interativo.html` direto (dois cliques),
a página funciona normalmente, mas sem o botão de upload.

<!-- [IA] Claude Code – front/UX (secao do front unico) -->
## Front do projeto (Parte 1 + Parte 2)

```bash
python -m src.parte2.exportar_figuras   # copia os gráficos de AVD do notebook para out/parte2/
python -m src.servidor                  # home em http://127.0.0.1:8765 (#parte1 / #parte2)
```

- **Home:** switch Parte 1 / Parte 2; a escolha fica no endereço (`#parte1`, `#parte2`, `#parte2/avd`).
- **Parte 1:** a mesma página do labirinto (`src/web/labirinto.html`), embutida no front.
- **Parte 2:** resumo do dataset e pergunta de pesquisa (lida do notebook), desenho do grafo
  inteiro (sigma.js, WebGL), painel para rodar BFS/DFS/Dijkstra/Bellman-Ford entre dois vértices,
  destaque do ciclo negativo, resultados do `out/parte2/parte2_report.json` e aba de AVD.
  Os algoritmos rodam no Python (`POST /api/parte2/rodar` chama `algorithms.py` do grupo);
  a página só desenha. As bibliotecas JS ficam em `src/web/vendor/` (funciona sem internet).

## Testes

```bash
pytest -q
```

Os testes marcados como `skipped` apontam o que ainda falta implementar:
`classificar_arcos()` na DFS, e o calculo a mao do mapa minimo em
`tests/test_estados.py`.

## Estrutura do projeto

```
projeto-grafos/
├─ README.md
├─ requirements.txt
├─ docs/
│  └─ DECLARACAO_IA.pdf      # declaração de uso de IA assinada por todos
├─ data/
│  ├─ mapas/                 # m01 a m08 (fornecidos)
│  ├─ mapas_grupo/           # 2 mapas criados pelo grupo
│  └─ dataset_parte2/        # dataset maior (ou script de download)
├─ out/
│  ├─ parte1/
│  └─ parte2/
├─ src/
│  ├─ cli.py                 # interface de linha de comando
│  ├─ solve.py               # orquestração e geração das saídas
│  ├─ graphs/
│  │  ├─ io.py               # leitura e validação dos mapas e do dataset
│  │  ├─ estados.py          # grafo de posições e grafo de estados
│  │  ├─ graph.py            # lista de adjacência DIRIGIDA
│  │  └─ algorithms.py       # BFS, DFS, Dijkstra, Bellman-Ford (próprios)
│  ├─ parte2/                # construção do grafo do dataset; painel e figuras do front
│  ├─ web/                   # index.html (front único), labirinto.html e vendor/ (bibliotecas JS)
│  ├─ servidor.py            # servidor local do front
│  └─ viz.py                 # visualizações / UX
└─ tests/                    # pytest
```

## Símbolos dos mapas

| Símbolo | Significado | Custo de entrar |
|---|---|---|
| `#` | Parede (intransponível) | — |
| `.` | Chão | 1 |
| `S` | Início (exatamente um por mapa) | 1 |
| `G` | Saída (o jogo termina ao entrar) | 1 |
| `,` | Lama | 3 |
| `~` | Água | 5 |
| `a`–`d` | Chave (fica com o jogador para sempre) | 1 |
| `A`–`D` | Porta (só com a chave minúscula correspondente) | 1 |
| `>` `<` `^` `v` | Esteira (só se sai na direção da seta) | 1 |
| `+` | Bônus consumível (vale só na 1ª vez) | −4, depois 1 |
| `*` | Fonte de energia (vale toda vez) | −2 |

Regras de movimento: 4 direções sempre na ordem **N, L, S, O**; custo do movimento =
custo da casa de **destino**; estados em `G` não têm arcos de saída.

## Divisão de pacotes de trabalho

> **TODO do grupo:** preencher dono e revisor de cada pacote.

| Pacote | Escopo | Dono | Revisor |
|---|---|---|---|
| P1 | Modelagem e grafo de estados (`io.py`, `estados.py`, arestas, `test_io`, `test_estados`) | | |
| P2 | Algoritmos e testes (BFS, DFS, Dijkstra, Bellman-Ford, transposto) | | |
| P3 | Análises da Parte 1 (métricas, camadas, comparação de modelagens, m05, m06, mapas do grupo) | | |
| P4 | Parte 2 (dataset, pesos negativos, casos obrigatórios, benchmark, escalabilidade) | | |
| P5 | Visualização e comunicação (figuras, HTML interativo, AVD, README, PDF) | | |

## Saídas

| arquivo | conteúdo |
|---|---|
| `out/parte1/labirinto_interativo.html` | percurso animado, camadas, armadilhas |
| `out/parte1/percurso_m03.png` · `percurso_m08.png` | caminho sobre o mapa, cor por camada |
| `out/parte1/camadas_m02.png` | grafo de estados em camadas |
| `out/parte1/arvore_bfs_m02.png` | árvore BFS com os níveis |
| `out/parte1/heatmap_m08.png` | multiplicidade das casas |

## Uso de IA

Este projeto segue as diretrizes da disciplina. Todo trecho feito com apoio de IA está
marcado no código com `# [IA] <ferramenta> – <finalidade>` e registrado em
`docs/DECLARACAO_IA.pdf`.
