#!/usr/bin/env python3

import networkx as nx
from pysat.solvers import Solver


def construir_grafo_solucao(modelo, var_por_aresta):
    ativos = {lit for lit in modelo if lit > 0}
    grafo = nx.Graph()
    for aresta, var in var_por_aresta.items():
        if var in ativos:
            ponto_a, ponto_b = aresta
            grafo.add_edge(ponto_a, ponto_b, var=var)
    return grafo


def detectar_subciclos(grafo):
    componentes = []
    for nos in nx.connected_components(grafo):
        subgrafo = grafo.subgraph(nos)
        variaveis = [dados["var"] for _, _, dados in subgrafo.edges(data=True)]
        componentes.append(variaveis)
    return componentes


def clausula_bloqueio(variaveis_subciclo):
    return [-v for v in variaveis_subciclo]


def resolver_com_refinamento(
    clausulas, var_por_aresta, max_iteracoes=50, solver_name="cadical195"
):

    aresta_por_var = {var: aresta for aresta, var in var_por_aresta.items()}
    todas_variaveis_aresta = list(var_por_aresta.values())

    clausulas_atuais = list(clausulas)

    for iteracao in range(1, max_iteracoes + 1):
        with Solver(name=solver_name, bootstrap_with=clausulas_atuais) as solver:
            se_satisfazivel = solver.solve()
            if not se_satisfazivel:
                return "UNSAT", iteracao
            modelo = solver.get_model()

        grafo = construir_grafo_solucao(modelo, var_por_aresta)

        if grafo.number_of_edges() == 0:
            # Grade sem nenhuma aresta ativa satisfaz grau 0-ou-2 mas nao e um
            # laco valido: forca ao menos uma aresta a ser ativa e tenta de novo.
            clausulas_atuais.append(list(todas_variaveis_aresta))
            continue

        subciclos = detectar_subciclos(grafo)

        if len(subciclos) == 1:
            variaveis_laco = subciclos[0]
            return [aresta_por_var[v] for v in variaveis_laco], iteracao

        menor_subciclo = min(subciclos, key=len)
        clausulas_atuais.append(clausula_bloqueio(menor_subciclo))

    return None, max_iteracoes
