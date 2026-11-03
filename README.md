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
# PARTE 1 (labirintos)
python -m src.cli --mapa ./data/mapas/m03_tres_chaves.txt --alg BFS          --out ./out/parte1/
python -m src.cli --mapa ./data/mapas/m03_tres_chaves.txt --alg DIJKSTRA     --out ./out/parte1/
python -m src.cli --mapa ./data/mapas/m05_bonus.txt       --alg BELLMAN_FORD --out ./out/parte1/
python -m src.cli --mapa ./data/mapas/m06_fonte.txt       --alg BELLMAN_FORD --fonte consumivel --out ./out/parte1/
python -m src.cli --mapa ./data/mapas/m04_esteiras.txt    --armadilhas       --out ./out/parte1/
python -m src.cli --mapa ./data/mapas/m03_tres_chaves.txt --interactive      --out ./out/parte1/

# PARTE 2 (dataset maior)
python -m src.cli --dataset ./data/dataset_parte2/ --alg DIJKSTRA --source A --target Z --out ./out/parte2/
python -m src.cli --dataset ./data/dataset_parte2/ --benchmark --out ./out/parte2/
```

## Testes

```bash
pytest
```

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

## Uso de IA

Este projeto segue as diretrizes da disciplina. Todo trecho feito com apoio de IA está
marcado no código com `# [IA] <ferramenta> – <finalidade>` e registrado em
`docs/DECLARACAO_IA.pdf`.
