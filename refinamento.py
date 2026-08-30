"""Deteccao de subtours e geracao de cortes para o refinamento SAT."""


def detectar_componentes_conexos(arestas_ativas):
    adjacencias = {}
    for origem, destino in arestas_ativas:
        adjacencias.setdefault(origem, set()).add(destino)
        adjacencias.setdefault(destino, set()).add(origem)

    componentes = []
    visitados = set()
    for inicio in adjacencias:
        if inicio in visitados:
            continue
        componente = set()
        pilha = [inicio]
        visitados.add(inicio)
        while pilha:
            atual = pilha.pop()
            componente.add(atual)
            for vizinho in adjacencias[atual]:
                if vizinho not in visitados:
                    visitados.add(vizinho)
                    pilha.append(vizinho)
        componentes.append(componente)
    return componentes


def gerar_clausula_bloqueio(componente, arestas_ativas, var_por_aresta):
    arestas_componente = [
        aresta
        for aresta in arestas_ativas
        if aresta[0] in componente and aresta[1] in componente
    ]
    if not arestas_componente:
        raise ValueError("O componente informado nao possui arestas ativas.")

    try:
        return [-var_por_aresta[aresta] for aresta in arestas_componente]
    except KeyError as exc:
        raise ValueError(f"Aresta sem variavel SAT: {exc.args[0]!r}.") from exc


def menor_componente(componentes):
    if not componentes:
        raise ValueError("Nenhum componente conexo foi encontrado.")
    return min(componentes, key=lambda componente: (len(componente), sorted(componente)))
