"""
io.py  -  Leitura e validacao dos mapas .txt e do dataset da Parte 2.

PACOTE P1. NAO PODE SER ESCRITO POR IA (ver DECLARACAO_IA).

Responsabilidades deste arquivo:
  - ler um arquivo de mapa, ignorando linhas que comecam com ';'
  - validar: grade retangular, exatamente um 'S', pelo menos um 'G',
    nenhum simbolo desconhecido -> erro com mensagem clara
  - expor a tabela de custos dos simbolos (. 1 | , 3 | ~ 5 | + -4 depois 1 | * -2)
  - ler o dataset da Parte 2 (arestas origem,destino,peso)
"""
