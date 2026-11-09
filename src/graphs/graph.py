def ordem(g):
    return len(g)


def tamanho(g):
    total = 0
    for vizinhos in g.values():
        total += len(vizinhos)
    return total


def grau_saida(g, no):
    return len(g[no])


def densidade(g):
    v = ordem(g)
    if v < 2:
        return 0.0
    return tamanho(g) / (v * (v - 1))


def grau_entrada(g, no):
    total = 0
    for vizinhos in g.values():
        for destino, _ in vizinhos:
            if destino == no:
                total += 1
    return total


def graus_entrada(g):
    graus = {}
    for no in g:
        graus[no] = 0
    for vizinhos in g.values():
        for destino, _ in vizinhos:
            graus[destino] = graus.get(destino, 0) + 1
    return graus


def transposto(g):
    t = {}
    for no in g:
        t[no] = []
    for origem, vizinhos in g.items():
        for destino, peso in vizinhos:
            t.setdefault(destino, []).append((origem, peso))
    return t


def subgrafo_induzido(g, nos):
    manter = set(nos)
    sub = {}
    for no in g:
        if no in manter:
            sub[no] = []
            for destino, peso in g[no]:
                if destino in manter:
                    sub[no].append((destino, peso))
    return sub
