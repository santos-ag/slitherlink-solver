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
