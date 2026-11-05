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
                     

        return caracteres


def obter_custo(caract):
      if caract in CUSTOS:
            return CUSTOS[caract]
      else :
            return 1

      
      

      

      



          
    
    





    