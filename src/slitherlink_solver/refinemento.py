import networkx as nx
from pysat.solvers import Glucose3

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


def gerar_clausula_bloqueio(componente, arestas_ativas, var_por_aresta):
    clausula = []

    arestas_componente = [
        aresta
        for aresta in arestas_ativas
        if aresta[0] in componente and aresta[1] in componente
    ]

    for aresta in arestas_componente:
        variavel_sat = var_por_aresta[aresta]
        clausula.append(-variavel_sat)

    return clausula


def resolver_com_refinamento(clausulas, var_por_aresta, max_iteracoes=50):
    aresta_por_var = {var: aresta for aresta, var in var_por_aresta.items()}

    iteracoes = 0

    with Glucose3() as solver:
        for clausula in clausulas:
            solver.add_clause(clausula)

        while iteracoes < max_iteracoes:
            print(f"iteração: {iteracoes}")
            iteracoes += 1

            if not solver.solve():
                print("problema sem solução")
                return None, iteracoes

            modelo = solver.get_model()
            arestas_ativas = [
                aresta_por_var[v] for v in modelo if v > 0 and v in aresta_por_var
            ]

            componentes = detectar_componentes_conexos(arestas_ativas)

            if len(componentes) == 1:
                print("apena um ciclo encontrado. válido")
                return arestas_ativas, iteracoes

            menor_componente = min(componentes, key=len)
            clausula_bloqueio = gerar_clausula_bloqueio(
                menor_componente, arestas_ativas, var_por_aresta
            )

            print(f"subciclos encontrados: {len(componentes)}")
            print(f"cláusula de bloqueio adicionada: {clausula_bloqueio}")

            solver.add_clause(clausula_bloqueio)

    return None, iteracoes


if __name__ == "__main__":
    componentes = detectar_componentes_conexos(solucao)

    if len(componentes) > 1:
        menor_componente = min(componentes, key=len)
        clausula_bloqueio = gerar_clausula_bloqueio(
            menor_componente, solucao, var_por_aresta
        )

        print(f"subciclos detectados: {len(componentes)}")
        print(f"nós do menor componente: {menor_componente}")
        print(f"cláusula do bloqueio gerada: {clausula_bloqueio}")
    else:
        print("solução válida: 1 loop detectado.")
