CHAVES_VALIDAS = {"a", "b", "c", "d"}
PORTAS_VALIDAS = {"A", "B", "C", "D"}
ESTEIRAS_VALIDAS = {"^", "v", "<", ">"}
TERRENOS_VALIDOS = {".", "#", ",", "~", "+", "*", "S", "G"}



SIMBOLOS_VALIDOS = TERRENOS_VALIDOS | CHAVES_VALIDAS | PORTAS_VALIDAS | ESTEIRAS_VALIDAS


CUSTOS = {
                ",":3,
                "~":5,
                "+":-4,
                "*":-2
        }


def ler_mapa(mapa):
    caracteres = []
    linhas = []

    with open(mapa) as arquivo:
        for linha in arquivo:
                 
                if not linha.startswith(";"):
                        linhas.append(linha.strip())
               
        
       
        for i in linhas:
                caracteres.append(list(i))
                     

        validar_mapa(caracteres)

        return caracteres


def obter_custo(caract):
      if caract in CUSTOS:
            return CUSTOS[caract]
      else :
            return 1


def achar_inicio(grade):
      for l , linha in enumerate(grade):
            for c , valor in enumerate(linha):
                  if valor == "S":
                        return (l , c)


def achar_saida(grade):
      saidas = []
      for l , linha in enumerate(grade):
                  for c , valor in enumerate(linha):
                         if valor =="G":
                                saidas.append((l , c))                        

      return saidas

      

def achar_chaves(grade):
    chaves = {}
    for l, linha in enumerate(grade):
        for c, valor in enumerate(linha):
            if valor in CHAVES_VALIDAS:
                chaves[valor] = (l, c)
    return chaves





def achar_portas(grade):
    portas = {}
    for l, linha in enumerate(grade):
        for c, valor in enumerate(linha):
            if valor in PORTAS_VALIDAS:
                portas.setdefault(valor, []).append((l, c))
    return portas




def achar_bonus(grade):
    bonus = {}
    contador = 0
    for l, linha in enumerate(grade):
        for c, valor in enumerate(linha):
            if valor == '+':
                bonus[(l, c)] = contador
                contador += 1
    return bonus

def validar_mapa(grade):

      

    
    if not grade:
        raise ValueError("Erro no Mapa: O arquivo de mapa está vazio.")

    largura = len(grade[0])
    qtd_inicio = 0
    qtd_saida = 0

    for l, linha in enumerate(grade):
        if len(linha) != largura:
            raise ValueError(
                f"Erro de Formatação: O mapa não é retangular. "
                f"A linha {l} tem {len(linha)} colunas, mas a linha 0 tem {largura}."
            )

        for c, char in enumerate(linha):
            if char not in SIMBOLOS_VALIDOS:
                raise ValueError(
                    f"Erro de Conteúdo: Símbolo inválido '{char}' encontrado na posição ({l}, {c})."
                )

            if char == 'S':
                qtd_inicio += 1
            elif char == 'G':
                qtd_saida += 1

    
    if qtd_inicio == 0:
        raise ValueError("Erro de Validação: Nenhum ponto de início ('S') foi encontrado no mapa.")
    if qtd_inicio > 1:
        raise ValueError(f"Erro de Validação: O mapa contém {qtd_inicio} pontos 'S'. É permitido apenas 1.")
    if qtd_saida == 0:
        raise ValueError("Erro de Validação: Nenhuma saída ('G') foi encontrada no mapa.")