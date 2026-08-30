#!/usr/bin/env python3
"""
Executa CaDiCaL e Kissat nas instâncias DIMACS CNF do Slitherlink,
registra métricas de tempo, número de variáveis/cláusulas e reconstrói a solução em ASCII.
"""

import os
import sys
import time
import subprocess
from gerador import parse_grid_file, SlitherlinkCNF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCIAS_DIR = os.path.join(BASE_DIR, "instancias")
SOLVERS = {
    "cadical": os.path.join(BASE_DIR, "solvers", "cadical"),
    "kissat": os.path.join(BASE_DIR, "solvers", "kissat")
}

def parse_dimacs_header(cnf_path):
    with open(cnf_path, 'r') as f:
        for line in f:
            if line.startswith("p cnf"):
                parts = line.split()
                return int(parts[2]), int(parts[3])
    return 0, 0

def run_solver(solver_bin, cnf_path):
    start_time = time.perf_counter()
    res = subprocess.run([solver_bin, cnf_path], capture_output=True, text=True)
    elapsed = (time.perf_counter() - start_time) * 1000 # em ms

    status = "UNKNOWN"
    model = []
    
    out = res.stdout
    if "s SATISFIABLE" in out:
        status = "SAT"
        for line in out.splitlines():
            if line.startswith("v "):
                parts = line.split()[1:]
                for p in parts:
                    if p != '0':
                        model.append(int(p))
    elif "s UNSATISFIABLE" in out:
        status = "UNSAT"
        
    return status, elapsed, model

def solve_with_subtour_elimination(solver_bin, txt_path):
    """
    Resolve a instância com eliminação iterativa de subtours (laço único).
    """
    R, C, grid = parse_grid_file(txt_path)
    slither = SlitherlinkCNF(R, C, grid)
    
    tmp_cnf = txt_path + ".tmp.cnf"
    iterations = 0
    total_time = 0
    
    while True:
        iterations += 1
        with open(tmp_cnf, 'w') as f:
            f.write(slither.generate_dimacs())
            
        status, elapsed, model = run_solver(solver_bin, tmp_cnf)
        total_time += elapsed
        
        if status != "SAT":
            if os.path.exists(tmp_cnf): os.remove(tmp_cnf)
            return status, total_time, slither.num_vars, len(slither.clauses), iterations, None
            
        # Analisar componentes conexos no modelo
        active_vars = set(val for val in model if val > 0)
        
        # Mapear arestas ativas
        active_h = set()
        active_v = set()
        for r in range(R + 1):
            for c in range(C):
                v = slither.var_h(r, c)
                if v in active_vars:
                    active_h.add((r, c))
                    
        for r in range(R):
            for c in range(C + 1):
                v = slither.var_v(r, c)
                if v in active_vars:
                    active_v.add((r, c))
                    
        # Se nenhuma aresta está ativa e não há dica exigindo, força ao menos 1 aresta
        if not active_h and not active_v:
            slither.clauses.append([slither.var_h(r, c) for r in range(R+1) for c in range(C)])
            continue
            
        # Construir grafo de vértices ativos
        adj = {}
        for r, c in active_h:
            v1, v2 = (r, c), (r, c + 1)
            adj.setdefault(v1, []).append((v2, slither.var_h(r, c)))
            adj.setdefault(v2, []).append((v1, slither.var_h(r, c)))
        for r, c in active_v:
            v1, v2 = (r, c), (r + 1, c)
            adj.setdefault(v1, []).append((v2, slither.var_v(r, c)))
            adj.setdefault(v2, []).append((v1, slither.var_v(r, c)))
            
        # Encontrar componentes
        visited = set()
        components = []
        for v in list(adj.keys()):
            if v not in visited:
                comp_nodes = []
                comp_edges = []
                q = [v]
                visited.add(v)
                while q:
                    curr = q.pop(0)
                    comp_nodes.append(curr)
                    for nxt, edge_var in adj[curr]:
                        comp_edges.append(edge_var)
                        if nxt not in visited:
                            visited.add(nxt)
                            q.append(nxt)
                # comp_edges tem cada aresta 2x
                comp_edges_unique = list(set(comp_edges))
                components.append((comp_nodes, comp_edges_unique))
                
        if len(components) <= 1:
            # Solução com laço único encontrada!
            if os.path.exists(tmp_cnf): os.remove(tmp_cnf)
            return "SAT", total_time, slither.num_vars, len(slither.clauses), iterations, (R, C, grid, active_h, active_v)
        else:
            # Adicionar cláusula de bloqueio para cada subtour (bloqueia o ciclo menor)
            for comp_nodes, comp_edges in components:
                # Bloquear a combinação de arestas do subtour
                slither.clauses.append([-e for e in comp_edges])

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
    print(f"{'Instância':<25} | {'Solver':<8} | {'Vars':<6} | {'Cláusulas':<9} | {'Resultado':<8} | {'Tempo (ms)':<10}")
    print("-" * 85)
    
    results = []
    
    for txt in txt_files:
        txt_path = os.path.join(INSTANCIAS_DIR, txt)
        name = os.path.splitext(txt)[0]
        
        for s_name, s_bin in SOLVERS.items():
            status, elapsed, n_vars, n_clauses, iters, sol_data = solve_with_subtour_elimination(s_bin, txt_path)
            print(f"{name:<25} | {s_name:<8} | {n_vars:<6} | {n_clauses:<9} | {status:<8} | {elapsed:<10.2f}")
            results.append({
                "name": name,
                "solver": s_name,
                "vars": n_vars,
                "clauses": n_clauses,
                "status": status,
                "time": elapsed,
                "sol_data": sol_data
            })
            
    print("=========================================================================================\n")
    
    print("SOLUÇÕES RECONSTRUÍDAS (SAT):")
    seen_solutions = set()
    for res in results:
        if res["status"] == "SAT" and res["sol_data"] is not None and res["name"] not in seen_solutions:
            seen_solutions.add(res["name"])
            R, C, grid, active_h, active_v = res["sol_data"]
            print(f"\n--- Instância: {res['name']} ({R}x{C}) ---")
            print(render_ascii_solution(R, C, grid, active_h, active_v))

if __name__ == '__main__':
    main()
