#!/usr/bin/env python3
"""Executa CaDiCaL e Kissat com eliminacao iterativa de subtours."""

import argparse
import csv
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from gerador import SlitherlinkCNF, parse_grid_file
from refinamento import (
    detectar_componentes_conexos,
    gerar_clausula_bloqueio,
    menor_componente,
)


BASE_DIR = Path(__file__).resolve().parent
INSTANCIAS_DIR = BASE_DIR / "instancias"
SOLVERS = {
    "cadical": BASE_DIR / "solvers" / "cadical",
    "kissat": BASE_DIR / "solvers" / "kissat",
}


@dataclass
class SolveResult:
    instance: str
    solver: str
    status: str
    elapsed_ms: float
    variables: int
    base_clauses: int
    cuts: int
    final_clauses: int
    iterations: int
    solution: tuple | None = None
    first_rejected: tuple | None = None


def run_solver(solver_bin, cnf_path, timeout_seconds=30):
    solver_path = Path(solver_bin)
    if not solver_path.is_file() or not os.access(solver_path, os.X_OK):
        raise RuntimeError(f"Solver nao encontrado ou nao executavel: {solver_path}")

    start_time = time.perf_counter()
    try:
        process = subprocess.run(
            [str(solver_path), str(cnf_path)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "TIMEOUT", timeout_seconds * 1000, []
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    output = f"{process.stdout}\n{process.stderr}"
    if "s SATISFIABLE" in output:
        model = []
        for line in output.splitlines():
            if line.startswith("v "):
                model.extend(int(value) for value in line.split()[1:] if value != "0")
        return "SAT", elapsed_ms, model
    if "s UNSATISFIABLE" in output:
        return "UNSAT", elapsed_ms, []
    return "UNKNOWN", elapsed_ms, []


def _active_edges(slither, model):
    active_vars = {value for value in model if value > 0}
    active_h = set()
    active_v = set()
    var_by_edge = {}
    edges = []

    for row in range(slither.R + 1):
        for col in range(slither.C):
            variable = slither.var_h(row, col)
            edge = ((row, col), (row, col + 1))
            var_by_edge[edge] = variable
            if variable in active_vars:
                active_h.add((row, col))
                edges.append(edge)

    for row in range(slither.R):
        for col in range(slither.C + 1):
            variable = slither.var_v(row, col)
            edge = ((row, col), (row + 1, col))
            var_by_edge[edge] = variable
            if variable in active_vars:
                active_v.add((row, col))
                edges.append(edge)

    return edges, var_by_edge, active_h, active_v


def solve_with_subtour_elimination(
    solver_name,
    solver_bin,
    txt_path,
    max_iterations=50,
    timeout_seconds=30,
):
    rows, cols, grid = parse_grid_file(txt_path)
    slither = SlitherlinkCNF(rows, cols, grid)
    base_clauses = len(slither.clauses)
    total_time = 0.0
    first_rejected = None

    for iteration in range(1, max_iterations + 1):
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".cnf",
                delete=False,
            ) as temporary:
                temporary.write(slither.generate_dimacs())
                temp_path = temporary.name

            status, elapsed, model = run_solver(
                solver_bin,
                temp_path,
                timeout_seconds=timeout_seconds,
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

        total_time += elapsed
        cuts = len(slither.clauses) - base_clauses
        if status != "SAT":
            return SolveResult(
                instance=Path(txt_path).stem,
                solver=solver_name,
                status=status,
                elapsed_ms=total_time,
                variables=slither.num_vars,
                base_clauses=base_clauses,
                cuts=cuts,
                final_clauses=len(slither.clauses),
                iterations=iteration,
                first_rejected=first_rejected,
            )

        edges, var_by_edge, active_h, active_v = _active_edges(slither, model)
        components = detectar_componentes_conexos(edges)
        solution_data = (rows, cols, grid, active_h, active_v)
        if len(components) == 1:
            return SolveResult(
                instance=Path(txt_path).stem,
                solver=solver_name,
                status="SAT",
                elapsed_ms=total_time,
                variables=slither.num_vars,
                base_clauses=base_clauses,
                cuts=cuts,
                final_clauses=len(slither.clauses),
                iterations=iteration,
                solution=solution_data,
                first_rejected=first_rejected,
            )
        if not components:
            raise RuntimeError("O gerador permitiu uma solucao sem arestas ativas.")

        if first_rejected is None:
            first_rejected = solution_data
        component = menor_componente(components)
        slither.clauses.append(gerar_clausula_bloqueio(component, edges, var_by_edge))

    return SolveResult(
        instance=Path(txt_path).stem,
        solver=solver_name,
        status="LIMIT",
        elapsed_ms=total_time,
        variables=slither.num_vars,
        base_clauses=base_clauses,
        cuts=len(slither.clauses) - base_clauses,
        final_clauses=len(slither.clauses),
        iterations=max_iterations,
        first_rejected=first_rejected,
    )


def render_ascii_solution(rows, cols, grid, active_h, active_v):
    lines = []
    for row in range(rows):
        horizontal = "".join(
            "+" + ("---" if (row, col) in active_h else "   ")
            for col in range(cols)
        ) + "+"
        lines.append(horizontal)

        vertical = "".join(
            ("|" if (row, col) in active_v else " ")
            + f" {grid[row][col] if grid[row][col] is not None else ' '} "
            for col in range(cols)
        )
        vertical += "|" if (row, cols) in active_v else " "
        lines.append(vertical)

    lines.append(
        "".join(
            "+" + ("---" if (rows, col) in active_h else "   ")
            for col in range(cols)
        )
        + "+"
    )
    return "\n".join(lines)


def write_csv(results, output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "instance",
        "solver",
        "variables",
        "base_clauses",
        "cuts",
        "final_clauses",
        "iterations",
        "status",
        "elapsed_ms",
    ]
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for result in results:
            row = {field: getattr(result, field) for field in fields}
            row["elapsed_ms"] = f"{result.elapsed_ms:.3f}"
            writer.writerow(row)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--solver",
        choices=["all", *SOLVERS],
        default="all",
        help="Solver a executar (padrao: ambos).",
    )
    parser.add_argument("--instance", type=Path, help="Executa somente uma instancia TXT.")
    parser.add_argument("--csv", type=Path, help="Salva as metricas em CSV.")
    parser.add_argument("--max-iterations", type=int, default=50)
    parser.add_argument("--timeout", type=float, default=30)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.max_iterations <= 0 or args.timeout <= 0:
        raise SystemExit("--max-iterations e --timeout devem ser positivos.")

    instances = [args.instance] if args.instance else sorted(INSTANCIAS_DIR.glob("*.txt"))
    selected_solvers = SOLVERS if args.solver == "all" else {args.solver: SOLVERS[args.solver]}

    print("=" * 111)
    print("BENCHMARK DE SAT SOLVERS - SLITHERLINK")
    print("=" * 111)
    print(
        f"{'Instancia':<25} | {'Solver':<8} | {'Vars':>4} | {'Base':>5} | "
        f"{'Cortes':>6} | {'Iter.':>5} | {'Resultado':<8} | {'Tempo (ms)':>10}"
    )
    print("-" * 111)

    results = []
    for instance in instances:
        if not instance or not instance.is_file():
            raise SystemExit(f"Instancia nao encontrada: {instance}")
        for solver_name, solver_bin in selected_solvers.items():
            result = solve_with_subtour_elimination(
                solver_name,
                solver_bin,
                instance,
                max_iterations=args.max_iterations,
                timeout_seconds=args.timeout,
            )
            results.append(result)
            print(
                f"{result.instance:<25} | {result.solver:<8} | {result.variables:>4} | "
                f"{result.base_clauses:>5} | {result.cuts:>6} | {result.iterations:>5} | "
                f"{result.status:<8} | {result.elapsed_ms:>10.3f}"
            )

    print("=" * 111)
    print("\nSOLUCOES RECONSTRUIDAS (SAT):")
    shown = set()
    for result in results:
        if result.solution is not None and result.instance not in shown:
            shown.add(result.instance)
            rows, cols, grid, active_h, active_v = result.solution
            print(f"\n--- {result.instance} ({rows}x{cols}) ---")
            print(render_ascii_solution(rows, cols, grid, active_h, active_v))

    if args.csv:
        write_csv(results, args.csv)
        print(f"\nMetricas salvas em {args.csv}")


if __name__ == "__main__":
    main()
