# Projeto de Teoria dos Grafos + Análise e Visualização de Dados (AVD) 2026.2

## Sobre o projeto

Projeto final interdisciplinar de Teoria dos Grafos e Análise e Visualização de Dados (AVD), desenvolvido em Python. O objetivo é aplicar e comparar os algoritmos BFS, DFS, Dijkstra e Bellman-Ford em dois contextos distintos:

- **Parte 1 — Labirinto com chaves e portas:** construção de grafos de posições (G_pos) e de estados (G_est), considerando terrenos, chaves, portas, esteiras, bônus consumíveis e fontes de energia. São estudados caminhos, custos, métricas, camadas, estados-armadilha e ciclos negativos.
- **Parte 2 — Bitcoin Alpha:** modelagem de uma rede real de confiança entre usuários, com arestas dirigidas e pesos positivos e negativos. São realizadas comparações de comportamento, desempenho e escalabilidade dos algoritmos, além da análise exploratória e explanatória dos dados.

Os algoritmos são implementados em `src/graphs/algorithms.py` e utilizados nas duas partes. O projeto conta com uma interface web interativa e uma interface de linha de comando (CLI).

## Integrantes

- Eduardo Malheiros Leal Jácome
- George Almerio Alves Neto
- João Danilo Correia Jota
- Pedro da Costa Carvalho Caldas
- Ramsés Cordeiro Filgueiras Esperia

## Obter o projeto

Clone o repositório utilizando o Git:

```bash
git clone https://github.com/Caldas42/ProjetoGrafos.git
cd ProjetoGrafos
```

Alternativamente, baixe o ZIP pelo botão **Code > Download ZIP** do GitHub, extraia o conteúdo e abra o terminal na pasta extraída.

Todos os comandos a seguir devem ser executados na raiz do projeto (pasta que contém `requirements.txt` e `src/`), com o ambiente virtual ativo após o setup. Os mapas, o dataset e os resultados já gerados estão incluídos no repositório.

## Setup

Requer **Python 3.11 a 3.15**. Confira a sua versão antes de começar:

| Sistema | Verificar versão |
| --- | --- |
| macOS / Linux | `python3 --version` |
| Windows | `py --version` |

### 1. Criar e ativar o ambiente virtual

O nome do comando do Python muda por sistema (em muitas máquinas `python` nem existe). Use a linha do seu sistema:

| Sistema | Criar | Ativar |
| --- | --- | --- |
| macOS / Linux | `python3 -m venv .venv` | `source .venv/bin/activate` |
| Windows (PowerShell) | `py -m venv .venv` | `.venv\Scripts\Activate.ps1` |
| Windows (cmd) | `py -m venv .venv` | `.venv\Scripts\activate.bat` |

Se você tem várias versões instaladas, escolha uma compatível, por exemplo `python3.12 -m venv .venv` (macOS/Linux) ou `py -3.12 -m venv .venv` (Windows).

Com o ambiente ativo, o terminal mostra `(.venv)` no início da linha. **A partir daqui os comandos são iguais em todos os sistemas**, porque dentro do venv `python` e `pip` sempre existem.

### 2. Instalar

```bash
python -m pip install -r requirements.txt
```

### Problemas comuns

- **`python: command not found` / `python` não é reconhecido:** use `python3` (macOS/Linux) ou `py` (Windows) só para criar o venv; depois de ativado, `python` funciona.
- **Linux (Debian/Ubuntu): `ensurepip is not available` ou `No module named venv`:** instale `sudo apt install python3-venv` (ou `python3.X-venv` para a sua versão).
- **Windows: "a execução de scripts foi desabilitada" ao ativar no PowerShell:** rode uma vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, ou use o cmd.
- **Python fora de 3.11–3.15:** instale uma versão compatível em [python.org](https://www.python.org/downloads/) e crie o venv com ela, como no exemplo acima.
- **Erro de certificado no `pip install` (macOS, Python do python.org):** rode `Install Certificates.command`, na pasta Python 3.X em Aplicativos.

## Como executar

### Interface web (recomendado)

Após concluir o setup, execute:

```bash
python -m src.servidor
```

O servidor local será iniciado e o navegador será aberto automaticamente em [http://127.0.0.1:8765/](http://127.0.0.1:8765/). Caso não abra, acesse esse endereço manualmente.

A página inicial permite acessar as duas partes do projeto:

- **Parte 1:** seleção de mapas e algoritmos, animação dos percursos, visualização de camadas, estados-armadilha, métricas e carregamento de novos mapas TXT.
- **Parte 2:** exploração da rede Bitcoin Alpha, execução de algoritmos com origem e destino selecionados, consulta aos resultados e às visualizações de desempenho e de AVD.

Não é necessário instalar Node.js: as bibliotecas JavaScript utilizadas pela interface estão em `src/web/vendor/`.

Caso a porta padrão esteja ocupada, execute `python -m src.servidor --porta 9000` e acesse http://127.0.0.1:9000/. Para iniciar sem abrir o navegador automaticamente, utilize `python -m src.servidor --sem-navegador`.

Para encerrar o servidor, pressione `Ctrl+C` no terminal.

### Parte 1 — Labirintos pelo terminal

Os oito mapas fornecidos estão em `data/mapas/` e os dois mapas elaborados pelo grupo em `data/mapas_grupo/`.

**Executar os quatro algoritmos:**

```bash
python -m src.cli --mapa data/mapas/m03_tres_chaves.txt --alg BFS --caminho
python -m src.cli --mapa data/mapas/m03_tres_chaves.txt --alg DFS
python -m src.cli --mapa data/mapas/m03_tres_chaves.txt --alg DIJKSTRA --caminho
python -m src.cli --mapa data/mapas/m05_bonus.txt --alg BELLMAN_FORD --caminho
```

| Algoritmo | Resultado apresentado |
| --- | --- |
| BFS | Caminho com menor número de passos |
| DFS | Estados visitados, classificação dos arcos e indicação de ciclos |
| Dijkstra | Caminho de menor custo em grafos sem pesos negativos |
| Bellman-Ford | Caminho de menor custo ou detecção de ciclo negativo alcançável |

**Consultar métricas, graus e estados-armadilha:**

```bash
python -m src.cli --mapa data/mapas/m04_esteiras.txt --metricas --graus --armadilhas
python -m src.cli --mapa data/mapas/m07_impossivel.txt --alg BFS --armadilhas
```

**Comparar o grafo de posições e o grafo de estados no m05:**

```bash
python -m src.cli --mapa data/mapas/m05_bonus.txt --alg BELLMAN_FORD --gpos
python -m src.cli --mapa data/mapas/m05_bonus.txt --alg BELLMAN_FORD --caminho
```

**Executar o m06 com a fonte infinita e com a fonte consumível:**

```bash
python -m src.cli --mapa data/mapas/m06_fonte.txt --alg BELLMAN_FORD
python -m src.cli --mapa data/mapas/m06_fonte.txt --alg BELLMAN_FORD --fonte-consumivel --caminho
```

A opção `--fonte-consumivel` faz com que o custo negativo da fonte de energia seja aplicado apenas na primeira entrada na respectiva casa.

**Executar os mapas do grupo:**

```bash
python -m src.cli --mapa data/mapas_grupo/g01_tres_chaves.txt --alg BELLMAN_FORD --caminho
python -m src.cli --mapa data/mapas_grupo/g02_porao.txt --alg BFS --metricas --armadilhas
```

#### Carregar um novo mapa

É possível executar qualquer mapa TXT válido substituindo o caminho informado em `--mapa`. Na interface web, utilize o botão **Carregar mapa** da Parte 1. Os mapas enviados pela interface são salvos em `out/parte1/mapas_enviados/`.

O arquivo deve conter uma grade retangular de caracteres, exatamente um `S` (início) e pelo menos um `G` (saída). Linhas iniciadas por `;` e linhas em branco são ignoradas.

| Símbolo | Significado | Custo de entrada |
| --- | --- | --- |
| `#` | Parede | Intransponível |
| `.`, `S`, `G` | Chão, início e saída | 1 |
| `,` | Lama | 3 |
| `~` | Água | 5 |
| `a` a `d` | Chaves | 1 |
| `A` a `D` | Portas (exigem a chave correspondente) | 1 |
| `^`, `>`, `v`, `<` | Esteiras (restringem a direção de saída) | 1 |
| `+` | Bônus consumível | -4 na primeira entrada; 1 nas demais |
| `*` | Fonte de energia | -2 a cada entrada no modo padrão |

O carregamento pela interface web possui limite de 3.600 casas. Para mapas maiores, utilize a CLI, observando o custo computacional da construção do grafo de estados.

#### Regenerar os resultados e visualizações da Parte 1

```bash
python -m src.solve
python -m src.viz
```

O primeiro comando gera os arquivos CSV e JSON referentes a todos os mapas fornecidos e aos mapas do grupo. O segundo gera as figuras PNG e o HTML interativo em `out/parte1/`.

Também é possível gerar apenas o HTML ou apenas as figuras:

```bash
python -m src.viz html
python -m src.viz figuras
```

Para visualizar os labirintos sem iniciar o servidor, abra `out/parte1/labirinto_interativo.html` diretamente no navegador. Para gerar o HTML de um único mapa, use:

```bash
python -m src.cli --mapa data/mapas/m03_tres_chaves.txt --interactive --out out/parte1/
```

Esse comando substitui o HTML da pasta de saída pelo conteúdo referente ao mapa selecionado. Para voltar à visualização de todos os mapas, execute `python -m src.viz html`.

### Parte 2 — Bitcoin Alpha pelo terminal

O dataset utilizado é o [Bitcoin Alpha Trust Weighted Signed Network](https://snap.stanford.edu/data/soc-sign-bitcoin-alpha.html), disponibilizado pelo Stanford Network Analysis Project (SNAP).

- Arquivo: `data/dataset_parte2/soc-sign-bitcoinalpha.csv`.
- Grafo dirigido e ponderado, com 3.783 vértices e 24.186 arestas.
- Cada linha do CSV contém origem, destino, avaliação de confiança (rating, de -10 a +10) e timestamp.
- O dataset está incluído no repositório e não exige download adicional.

**Executar os algoritmos:**

```bash
python -m src.cli --dataset data/dataset_parte2/ --alg BFS --source 7188 --target 2 --out out/parte2/
python -m src.cli --dataset data/dataset_parte2/ --alg DFS --source 7188 --target 2 --out out/parte2/
python -m src.cli --dataset data/dataset_parte2/ --alg DIJKSTRA --source 7188 --target 1 --out out/parte2/
python -m src.cli --dataset data/dataset_parte2/ --alg BELLMAN_FORD --source 7188 --target 1 --out out/parte2/
```

Os parâmetros `--source` e `--target` representam os identificadores dos vértices de origem e destino. Os resultados são apresentados no terminal e salvos em `out/parte2/`, em arquivos `<algoritmo>_resultado.json`.

No grafo original, Dijkstra retorna uma mensagem de recusa devido à presença de pesos negativos. Bellman-Ford pode retornar um ciclo negativo em vez de um caminho de custo mínimo. Esses comportamentos fazem parte das verificações do projeto. Na Parte 2, a DFS apresenta o caminho encontrado na árvore de busca, sem garantia de custo mínimo.

**Gerar o benchmark e os gráficos de desempenho:**

```bash
python -m src.cli --dataset data/dataset_parte2/ --benchmark --out out/parte2/
python -m src.parte2.visualizacoes
```

O benchmark gera `out/parte2/parte2_report.json`, incluindo os resultados de BFS e DFS a partir de três fontes, os casos de Bellman-Ford com e sem ciclo negativo, a recusa de Dijkstra no grafo original e as medições de tempo, memória e escalabilidade em recortes de 10%, 50% e 100% dos vértices.

O segundo comando utiliza o JSON para produzir as seis figuras `alg_*.png` em `out/parte2/`. A execução do benchmark pode demorar, principalmente nas repetições de Bellman-Ford. Os valores de desempenho variam conforme o computador utilizado.

### Análise e Visualização de Dados (AVD)

As análises exploratória e explanatória estão disponíveis no [notebook do projeto](docs/Analise_Exploratoria_e_Explanatoria_do_Dataset_Bitcoin_Alpha_Trust_Weight_Signed_Network.ipynb), na pasta `docs/`.

Para visualizar o notebook, abra-o no GitHub ou em um editor compatível com Jupyter Notebook. Para executar as células localmente, utilize, por exemplo, o VS Code com a extensão Jupyter e selecione o kernel Python do ambiente `.venv` criado no setup. Confira o caminho do CSV na célula de carregamento: a partir de `docs/`, o caminho relativo é `../data/dataset_parte2/soc-sign-bitcoinalpha.csv`; a partir da raiz do projeto, é `data/dataset_parte2/soc-sign-bitcoinalpha.csv`. Ajuste o caminho, se necessário, conforme o diretório de execução do kernel.

Para exportar as sete figuras de AVD já armazenadas nas saídas do notebook e disponibilizá-las na interface web:

```bash
python -m src.parte2.exportar_figuras
```

O script extrai as imagens PNG salvas no notebook, sem executar as células novamente. As figuras são gravadas em `out/parte2/` com o prefixo `avd_`. Não é necessário executar o notebook para utilizar a interface com os resultados incluídos no repositório.

### Ajuda da CLI

Para consultar todos os parâmetros disponíveis:

```bash
python -m src.cli --help
```

## Testes automatizados

Após instalar as dependências, execute a suíte de testes com:

```bash
python -m pytest -v
```

Os testes estão na pasta `tests/` e incluem BFS, DFS, Dijkstra, Bellman-Ford, construção dos estados, validação dos mapas e verificação dos mapas elaborados pelo grupo.

## Estrutura do projeto

```text
ProjetoGrafos/
├── README.md
├── requirements.txt
├── data/
│   ├── mapas/                    # Mapas m01 a m08
│   ├── mapas_grupo/              # Mapas g01 e g02
│   └── dataset_parte2/           # CSV Bitcoin Alpha
├── docs/                         # Relatório e notebook de AVD
├── out/
│   ├── parte1/                  # CSV, JSON, PNG e HTML dos labirintos
│   └── parte2/                  # JSON e PNG da rede Bitcoin Alpha
├── src/
│   ├── cli.py                    # Interface de linha de comando
│   ├── solve.py                  # Geração de resultados e benchmarks
│   ├── viz.py                    # Visualizações da Parte 1
│   ├── servidor.py               # Servidor web local
│   ├── graphs/
│   │   ├── io.py                # Leitura e validação de dados
│   │   ├── estados.py           # Construção de G_pos e G_est
│   │   ├── graph.py             # Operações sobre grafos dirigidos
│   │   └── algorithms.py        # BFS, DFS, Dijkstra e Bellman-Ford
│   ├── parte2/
│   │   ├── construcao.py        # Construção do grafo Bitcoin Alpha
│   │   ├── painel.py            # Integração da Parte 2 com a interface
│   │   ├── visualizacoes.py     # Gráficos de comparação dos algoritmos
│   │   └── exportar_figuras.py   # Exportação das figuras do notebook
│   └── web/                     # Interface HTML e bibliotecas JavaScript
└── tests/                        # Testes automatizados
```

## Arquivos de saída

| Arquivo ou conjunto de arquivos | Conteúdo |
| --- | --- |
| `out/parte1/arestas_<mapa>.csv` | Arestas geradas para cada mapa |
| `out/parte1/graus_<mapa>.csv` | Graus de entrada e saída por estado |
| `out/parte1/metricas_global.json` e `camadas.json` | Métricas globais e por camada |
| `out/parte1/comparacao_modelagem.csv` | Comparação entre modelagens |
| `out/parte1/solucoes.csv` e `dfs_classificacao.csv` | Resultados dos algoritmos e classificação dos arcos |
| `out/parte1/percurso_m03.json` | Percurso estado a estado |
| `out/parte1/m05_gpos_vs_gest.json` | Comparação do m05 |
| `out/parte1/ciclo_negativo_m06.json` e `m06_fonte_consumivel.json` | Ciclo negativo e resultado com fonte consumível |
| `out/parte1/armadilhas_m04.csv` e `armadilhas_m07.csv` | Estados-armadilha |
| `out/parte1/*.png` | Percursos, camadas, árvore BFS e heatmap |
| `out/parte1/labirinto_interativo.html` | Visualização interativa dos labirintos |
| `out/parte2/parte2_report.json` | Resultados e métricas do benchmark |
| `out/parte2/*_resultado.json` | Resultados individuais dos algoritmos |
| `out/parte2/alg_*.png` | Gráficos de comparação de algoritmos |
| `out/parte2/avd_*.png` | Figuras de análise exploratória e explanatória |

## Documentação

- [Relatório técnico do projeto](docs/Relatorio.pdf).
- [Notebook de análise exploratória e explanatória](docs/Analise_Exploratoria_e_Explanatoria_do_Dataset_Bitcoin_Alpha_Trust_Weight_Signed_Network.ipynb).
- [Fonte do dataset Bitcoin Alpha (SNAP)](https://snap.stanford.edu/data/soc-sign-bitcoin-alpha.html).
