import networkx as nx

solucao = [
    ((0, 0), (0, 1)),
    ((0, 1), (1, 1)),
    ((1, 1), (1, 0)),
    ((1, 0), (0, 0)),
    ((2, 2), (2, 3)),
    ((2, 3), (3, 3)),
    ((3, 3), (3, 2)),
    ((3, 2), (2, 2)),
]

var_por_aresta = {
    ((0, 0), (0, 1)): 1,
    ((0, 1), (1, 1)): 2,
    ((1, 1), (1, 0)): 3,
    ((1, 0), (0, 0)): 4,
    ((2, 2), (2, 3)): 5,
    ((2, 3), (3, 3)): 6,
    ((3, 3), (3, 2)): 7,
    ((3, 2), (2, 2)): 8,
}


def detectar_componentes_conexos(arestas_ativas):
    G = nx.Graph()
    G.add_edges_from(arestas_ativas)
    return list(nx.connected_components(G))
