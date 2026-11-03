"""
estados.py  -  Construcao do grafo de posicoes (G_pos) e do grafo de estados (G_est).

PACOTE P1. NAO PODE SER ESCRITO POR IA (ver DECLARACAO_IA).

Responsabilidades deste arquivo:
  - G_pos: um no por casa livre; arcos pela geometria (paredes e esteiras)
  - G_est: um no por estado (linha, coluna, chaves, bonus consumidos)
      * construido por EXPLORACAO a partir do estado inicial (so alcancaveis)
      * vizinhos sempre na ordem N, L, S, O
      * custo do movimento = custo da casa de DESTINO
      * estados em G nao tem arcos de saida
      * no virtual ALVO, com arco de custo 0 saindo de todo estado em G
  - rotulo do estado no formato obrigatorio: (3,5)|ab|{0,2}
      sem chaves -> '-' ; sem bonus -> '{}'
  - teto teorico = casas livres * 2^(n chaves) * 2^(n bonus)
"""
