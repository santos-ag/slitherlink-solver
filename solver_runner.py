#!/usr/bin/env python3
"""
Resolve as instâncias do Slitherlink com PySAT (CaDiCaL e Kissat embutidos) usando
refinamento iterativo (refinamento.py) para eliminar subtours, registra métricas de
tempo, número de variáveis/cláusulas/iterações e reconstrói a solução em ASCII.
"""

import os
import time
from gerador import parse_grid_file, SlitherlinkCNF
from refinamento import resolver_com_refinamento

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCIAS_DIR = os.path.join(BASE_DIR, "instancias")
MAX_ITERACOES = 50

# Nomes de solver do PySAT (pysat.solvers.SolverNames) - ambos resolvidos em
# processo, sem subprocess nem arquivos .cnf intermediários.
SOLVERS = {
    "cadical": "cadical195",
    "kissat": "kissat404",
}


def build_var_por_aresta(slither):
    """
    Traduz a numeração de variáveis de SlitherlinkCNF (var_h/var_v) para o
    formato de interface combinado do grupo: {aresta ((r,c),(r,c')): variavel}.
    """
    var_por_aresta = {}
    for r in range(slither.R + 1):
        for c in range(slither.C):
            var_por_aresta[((r, c), (r, c + 1))] = slither.var_h(r, c)
    for r in range(slither.R):
        for c in range(slither.C + 1):
            var_por_aresta[((r, c), (r + 1, c))] = slither.var_v(r, c)
    return var_por_aresta


def solve_instance(txt_path, solver_name):
    R, C, grid = parse_grid_file(txt_path)
    slither = SlitherlinkCNF(R, C, grid)
    var_por_aresta = build_var_por_aresta(slither)

    start_time = time.perf_counter()
    solucao_final, iteracoes = resolver_com_refinamento(
        slither.clauses, var_por_aresta, max_iteracoes=MAX_ITERACOES, solver_name=solver_name
    )
    elapsed = (time.perf_counter() - start_time) * 1000  # em ms

    if solucao_final == "UNSAT":
        status, sol_data = "UNSAT", None
    elif solucao_final is None:
        status, sol_data = "LIMITE_ITER", None
    else:
        active_h, active_v = set(), set()
        for ponto_a, ponto_b in solucao_final:
            if ponto_a[0] == ponto_b[0]:
                active_h.add(ponto_a)
            else:
                active_v.add(ponto_a)
        status, sol_data = "SAT", (R, C, grid, active_h, active_v)

    return status, elapsed, slither.num_vars, len(slither.clauses), iteracoes, sol_data


def render_ascii_solution(R, C, grid, active_h, active_v):
    lines = []
    for r in range(R):
        # Linha de arestas horizontais e vértices
        h_line = ""
        for c in range(C):
            h_line += "+"
            h_line += "---" if (r, c) in active_h else "   "
        h_line += "+"
        lines.append(h_line)

        # Linha de arestas verticais e células
        v_line = ""
        for c in range(C):
            v_line += "|" if (r, c) in active_v else " "
            clue_str = str(grid[r][c]) if grid[r][c] is not None else " "
            v_line += f" {clue_str} "
        v_line += "|" if (r, C) in active_v else " "
        lines.append(v_line)

    # Última linha horizontal
    h_line = ""
    for c in range(C):
        h_line += "+"
        h_line += "---" if (R, c) in active_h else "   "
    h_line += "+"
    lines.append(h_line)
    return "\n".join(lines)

def main():
    txt_files = sorted([f for f in os.listdir(INSTANCIAS_DIR) if f.endswith(".txt")])

    print("=========================================================================================")
    print("                     BENCHMARK DE SAT SOLVERS - SLITHERLINK")
    print("=========================================================================================")
    print(f"{'Instância':<25} | {'Solver':<8} | {'Vars':<6} | {'Cláusulas':<9} | {'Resultado':<11} | {'Iterações':<9} | {'Tempo (ms)':<10}")
    print("-" * 100)

    results = []

    for txt in txt_files:
        txt_path = os.path.join(INSTANCIAS_DIR, txt)
        name = os.path.splitext(txt)[0]

        for s_name, s_solver in SOLVERS.items():
            status, elapsed, n_vars, n_clauses, iters, sol_data = solve_instance(txt_path, s_solver)
            print(f"{name:<25} | {s_name:<8} | {n_vars:<6} | {n_clauses:<9} | {status:<11} | {iters:<9} | {elapsed:<10.2f}")
            results.append({
                "name": name,
                "solver": s_name,
                "vars": n_vars,
                "clauses": n_clauses,
                "status": status,
                "time": elapsed,
                "iterations": iters,
                "sol_data": sol_data
            })

    print("=========================================================================================\n")

    print("SOLUÇÕES RECONSTRUÍDAS (SAT):")
    seen_solutions = set()
    for res in results:
        if res["status"] == "SAT" and res["sol_data"] is not None and res["name"] not in seen_solutions:
            seen_solutions.add(res["name"])
            R, C, grid, active_h, active_v = res["sol_data"]
            print(f"\n--- Instância: {res['name']} ({R}x{C}) — {res['iterations']} iteração(ões) ---")
            print(render_ascii_solution(R, C, grid, active_h, active_v))

if __name__ == '__main__':
    main()
