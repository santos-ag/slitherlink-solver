#!/usr/bin/env python3
"""Gera uma figura antes/subtour/depois para uma instancia Slitherlink."""

import argparse
from html import escape
from pathlib import Path

from solver_runner import SOLVERS, solve_with_subtour_elimination


def draw_grid(axis, rows, cols, grid, active_h=None, active_v=None, edge_color="#172554"):
    active_h = active_h or set()
    active_v = active_v or set()

    for row in range(rows + 1):
        axis.plot([0, cols], [-row, -row], color="#d1d5db", linewidth=0.6, zorder=0)
    for col in range(cols + 1):
        axis.plot([col, col], [0, -rows], color="#d1d5db", linewidth=0.6, zorder=0)

    for row in range(rows):
        for col in range(cols):
            clue = grid[row][col]
            if clue is not None:
                axis.text(
                    col + 0.5,
                    -row - 0.5,
                    str(clue),
                    ha="center",
                    va="center",
                    fontsize=12,
                    color="#4b5563",
                )

    for row, col in active_h:
        axis.plot(
            [col, col + 1],
            [-row, -row],
            color=edge_color,
            linewidth=3.2,
            solid_capstyle="round",
            zorder=3,
        )
    for row, col in active_v:
        axis.plot(
            [col, col],
            [-row, -row - 1],
            color=edge_color,
            linewidth=3.2,
            solid_capstyle="round",
            zorder=3,
        )

    for row in range(rows + 1):
        axis.scatter(range(cols + 1), [-row] * (cols + 1), s=12, color="#111827", zorder=4)

    axis.set_aspect("equal")
    axis.set_xlim(-0.2, cols + 0.2)
    axis.set_ylim(-rows - 0.2, 0.2)
    axis.axis("off")


def generate_figure(result, output_path):
    if result.status != "SAT" or result.solution is None:
        raise ValueError("A visualizacao exige uma instancia SAT com solucao final.")

    output = Path(output_path)
    if output.suffix.lower() == ".svg":
        generate_svg(result, output)
        return

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "Matplotlib nao esta disponivel. Use uma saida .svg ou instale requirements.txt."
        ) from exc

    rows, cols, grid, active_h, active_v = result.solution
    panels = 3 if result.first_rejected is not None else 2
    figure, axes = plt.subplots(1, panels, figsize=(5.2 * panels, 5.4))
    axes = list(axes)

    draw_grid(axes[0], rows, cols, grid)
    axes[0].set_title("Instancia", fontsize=14, fontweight="bold")

    final_axis = axes[-1]
    if result.first_rejected is not None:
        _, _, _, rejected_h, rejected_v = result.first_rejected
        draw_grid(axes[1], rows, cols, grid, rejected_h, rejected_v, edge_color="#b91c1c")
        axes[1].set_title("Modelo com subtours", fontsize=14, fontweight="bold")

    draw_grid(final_axis, rows, cols, grid, active_h, active_v, edge_color="#1d4ed8")
    final_axis.set_title(
        f"Laco final ({result.iterations} iteracoes)",
        fontsize=14,
        fontweight="bold",
    )

    figure.suptitle(
        f"Slitherlink {rows}x{cols} - {result.solver}",
        fontsize=17,
        fontweight="bold",
    )
    figure.tight_layout(rect=(0, 0, 1, 0.93))
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(figure)


def _svg_panel(parts, offset, title, rows, cols, grid, active_h, active_v, edge_color):
    cell = min(55, 310 / max(rows, cols))
    left = offset + (400 - cols * cell) / 2
    top = 115 + (310 - rows * cell) / 2
    parts.append(
        f'<text x="{offset + 200}" y="75" text-anchor="middle" '
        f'font-size="20" font-weight="700" fill="#111827">{escape(title)}</text>'
    )

    for row in range(rows + 1):
        y = top + row * cell
        parts.append(
            f'<line x1="{left}" y1="{y}" x2="{left + cols * cell}" y2="{y}" '
            'stroke="#d1d5db" stroke-width="1"/>'
        )
    for col in range(cols + 1):
        x = left + col * cell
        parts.append(
            f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + rows * cell}" '
            'stroke="#d1d5db" stroke-width="1"/>'
        )

    for row in range(rows):
        for col in range(cols):
            clue = grid[row][col]
            if clue is not None:
                parts.append(
                    f'<text x="{left + (col + 0.5) * cell}" '
                    f'y="{top + (row + 0.5) * cell + 6}" text-anchor="middle" '
                    f'font-size="18" fill="#4b5563">{clue}</text>'
                )

    for row, col in active_h:
        y = top + row * cell
        parts.append(
            f'<line x1="{left + col * cell}" y1="{y}" '
            f'x2="{left + (col + 1) * cell}" y2="{y}" '
            f'stroke="{edge_color}" stroke-width="6" stroke-linecap="round"/>'
        )
    for row, col in active_v:
        x = left + col * cell
        parts.append(
            f'<line x1="{x}" y1="{top + row * cell}" x2="{x}" '
            f'y2="{top + (row + 1) * cell}" stroke="{edge_color}" '
            'stroke-width="6" stroke-linecap="round"/>'
        )

    for row in range(rows + 1):
        for col in range(cols + 1):
            parts.append(
                f'<circle cx="{left + col * cell}" cy="{top + row * cell}" '
                'r="3" fill="#111827"/>'
            )


def generate_svg(result, output_path):
    rows, cols, grid, active_h, active_v = result.solution
    panels = 3 if result.first_rejected is not None else 2
    width = panels * 400
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="490" '
        f'viewBox="0 0 {width} 490">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="32" text-anchor="middle" font-size="24" '
        f'font-weight="700" fill="#0f172a">Slitherlink {rows}x{cols} - '
        f'{escape(result.solver)}</text>',
    ]
    _svg_panel(parts, 0, "Instancia", rows, cols, grid, set(), set(), "#172554")

    final_offset = (panels - 1) * 400
    if result.first_rejected is not None:
        _, _, _, rejected_h, rejected_v = result.first_rejected
        _svg_panel(
            parts,
            400,
            "Modelo com subtours",
            rows,
            cols,
            grid,
            rejected_h,
            rejected_v,
            "#b91c1c",
        )
    _svg_panel(
        parts,
        final_offset,
        f"Laco final ({result.iterations} iteracoes)",
        rows,
        cols,
        grid,
        active_h,
        active_v,
        "#1d4ed8",
    )
    parts.append("</svg>")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(parts), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance", type=Path)
    parser.add_argument("--solver", choices=SOLVERS, default="kissat")
    parser.add_argument("--output", type=Path, default=Path("resultados/solucao.svg"))
    return parser.parse_args()


def main():
    args = parse_args()
    result = solve_with_subtour_elimination(
        args.solver,
        SOLVERS[args.solver],
        args.instance,
    )
    generate_figure(result, args.output)
    print(f"Visualizacao salva em {args.output}")


if __name__ == "__main__":
    main()
