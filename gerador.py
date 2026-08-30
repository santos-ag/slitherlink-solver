#!/usr/bin/env python3
"""
Gerador de Instâncias DIMACS CNF para o Problema Slitherlink (Puzzle de Percurso).
Disciplina: Lógica para Ciência da Computação - UFCA (Prof. Luis Henrique Bustamante)

Uso:
  python3 gerador.py <arquivo_instancia.txt> > instancia.cnf
  python3 gerador.py <linhas> <colunas> "<dicas_linha_por_linha>" > instancia.cnf
"""

import os
import sys


EMPTY_TOKENS = {".", "_", "-"}

class SlitherlinkCNF:
    def __init__(self, rows, cols, grid):
        """
        rows: número de linhas de células
        cols: número de colunas de células
        grid: matriz rows x cols com inteiros 0, 1, 2, 3, 4 ou None para célula vazia
        """
        self._validate_grid(rows, cols, grid)
        self.R = rows
        self.C = cols
        self.grid = grid
        
        # Total de arestas horizontais: (R+1) * C
        # Total de arestas verticais: R * (C+1)
        self.num_h = (self.R + 1) * self.C
        self.num_v = self.R * (self.C + 1)
        self.num_vars = self.num_h + self.num_v
        
        self.clauses = []
        self._build_cnf()

    @staticmethod
    def _validate_grid(rows, cols, grid):
        if not isinstance(rows, int) or not isinstance(cols, int) or rows <= 0 or cols <= 0:
            raise ValueError("As dimensoes da grade devem ser inteiros positivos.")
        if len(grid) != rows or any(len(row) != cols for row in grid):
            raise ValueError(f"A grade deve possuir exatamente {rows} linhas e {cols} colunas.")
        for row in grid:
            for clue in row:
                if clue is not None and (not isinstance(clue, int) or not 0 <= clue <= 4):
                    raise ValueError(f"Dica invalida: {clue!r}. Use apenas valores de 0 a 4 ou '.'.")

    def var_h(self, r, c):
        """ Retorna a variável 1-based para a aresta horizontal na linha r, coluna c """
        assert 0 <= r <= self.R and 0 <= c < self.C
        return 1 + r * self.C + c

    def var_v(self, r, c):
        """ Retorna a variável 1-based para a aresta vertical na linha r, coluna c """
        assert 0 <= r < self.R and 0 <= c <= self.C
        return 1 + self.num_h + r * (self.C + 1) + c

    def _build_cnf(self):
        # 1. Restrições de Células
        for r in range(self.R):
            for c in range(self.C):
                clue = self.grid[r][c]
                if clue is None:
                    continue
                
                # 4 arestas da célula
                e_top = self.var_h(r, c)
                e_bottom = self.var_h(r + 1, c)
                e_left = self.var_v(r, c)
                e_right = self.var_v(r, c + 1)
                edges = [e_top, e_bottom, e_left, e_right]

                if clue == 0:
                    for e in edges:
                        self.clauses.append([-e])
                elif clue == 1:
                    # Ao menos 1
                    self.clauses.append(edges)
                    # No máximo 1 (combinações de 2)
                    for i in range(4):
                        for j in range(i + 1, 4):
                            self.clauses.append([-edges[i], -edges[j]])
                elif clue == 2:
                    # Ao menos 2 (combinações de 3 devem ter ao menos uma verdadeira)
                    for i in range(4):
                        for j in range(i + 1, 4):
                            for k in range(j + 1, 4):
                                self.clauses.append([edges[i], edges[j], edges[k]])
                    # No máximo 2 (combinações de 3 não podem ser todas verdadeiras)
                    for i in range(4):
                        for j in range(i + 1, 4):
                            for k in range(j + 1, 4):
                                self.clauses.append([-edges[i], -edges[j], -edges[k]])
                elif clue == 3:
                    # Ao menos 3 (combinações de 2)
                    for i in range(4):
                        for j in range(i + 1, 4):
                            self.clauses.append([edges[i], edges[j]])
                    # No máximo 3
                    self.clauses.append([-e for e in edges])
                elif clue == 4:
                    for e in edges:
                        self.clauses.append([e])

        # 2. Restrições de Grau dos Vértices (Grau 0 ou 2)
        for vr in range(self.R + 1):
            for vc in range(self.C + 1):
                inc = []
                if vr > 0: inc.append(self.var_v(vr - 1, vc))      # Cima
                if vr < self.R: inc.append(self.var_v(vr, vc))      # Baixo
                if vc > 0: inc.append(self.var_h(vr, vc - 1))      # Esquerda
                if vc < self.C: inc.append(self.var_h(vr, vc))      # Direita

                d = len(inc)
                if d == 2:
                    # Grau 0 ou 2 -> inc[0] == inc[1]
                    self.clauses.append([-inc[0], inc[1]])
                    self.clauses.append([inc[0], -inc[1]])
                elif d == 3:
                    # Grau 0 ou 2 -> proibir grau 1 e grau 3
                    # Proibir grau 1 (1 verdadeiro, 2 falsos)
                    self.clauses.append([-inc[0], inc[1], inc[2]])
                    self.clauses.append([inc[0], -inc[1], inc[2]])
                    self.clauses.append([inc[0], inc[1], -inc[2]])
                    # Proibir grau 3 (3 verdadeiros)
                    self.clauses.append([-inc[0], -inc[1], -inc[2]])
                elif d == 4:
                    # Grau 0 ou 2 -> proibir grau 1, 3 e 4
                    # Proibir grau 1 (1 v, 3 f)
                    self.clauses.append([-inc[0], inc[1], inc[2], inc[3]])
                    self.clauses.append([inc[0], -inc[1], inc[2], inc[3]])
                    self.clauses.append([inc[0], inc[1], -inc[2], inc[3]])
                    self.clauses.append([inc[0], inc[1], inc[2], -inc[3]])
                    # Proibir grau 3 (3 v, 1 f)
                    self.clauses.append([-inc[0], -inc[1], -inc[2], inc[3]])
                    self.clauses.append([-inc[0], -inc[1], inc[2], -inc[3]])
                    self.clauses.append([-inc[0], inc[1], -inc[2], -inc[3]])
                    self.clauses.append([inc[0], -inc[1], -inc[2], -inc[3]])
                    # Proibir grau 4 (4 v)
                    self.clauses.append([-inc[0], -inc[1], -inc[2], -inc[3]])

        # 3. Um Slitherlink sempre possui um laco nao vazio.
        self.clauses.append(list(range(1, self.num_vars + 1)))

    def validate(self):
        """Verifica limites das variaveis e a estrutura das clausulas geradas."""
        expected_vars = 2 * self.R * self.C + self.R + self.C
        if self.num_vars != expected_vars:
            raise ValueError(
                f"Numero de variaveis inconsistente: {self.num_vars} != {expected_vars}."
            )
        for index, clause in enumerate(self.clauses, start=1):
            if not clause:
                raise ValueError(f"Clausula vazia inesperada na posicao {index}.")
            for literal in clause:
                if not isinstance(literal, int) or literal == 0 or abs(literal) > self.num_vars:
                    raise ValueError(f"Literal invalido na clausula {index}: {literal!r}.")

    def generate_dimacs(self):
        self.validate()
        header = f"p cnf {self.num_vars} {len(self.clauses)}"
        lines = [f"c Instancia Slitherlink {self.R}x{self.C}", header]
        for c in self.clauses:
            lines.append(" ".join(map(str, c)) + " 0")
        output = "\n".join(lines)
        validate_dimacs(output)
        return output


def validate_dimacs(content):
    """Confere se cabecalho, clausulas e variaveis de um DIMACS sao consistentes."""
    header = None
    clauses = []

    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("c"):
            continue
        if line.startswith("p"):
            if header is not None:
                raise ValueError("O DIMACS possui mais de um cabecalho.")
            parts = line.split()
            if len(parts) != 4 or parts[:2] != ["p", "cnf"]:
                raise ValueError(f"Cabecalho DIMACS invalido na linha {line_number}.")
            try:
                header = int(parts[2]), int(parts[3])
            except ValueError as exc:
                raise ValueError(f"Cabecalho DIMACS invalido na linha {line_number}.") from exc
            continue

        if header is None:
            raise ValueError("Foi encontrada uma clausula antes do cabecalho DIMACS.")
        try:
            literals = [int(token) for token in line.split()]
        except ValueError as exc:
            raise ValueError(f"Literal nao inteiro na linha {line_number}.") from exc
        if not literals or literals[-1] != 0 or 0 in literals[:-1]:
            raise ValueError(f"Clausula DIMACS invalida na linha {line_number}.")
        clauses.append(literals[:-1])

    if header is None:
        raise ValueError("Cabecalho DIMACS ausente.")
    num_vars, declared_clauses = header
    if num_vars <= 0 or declared_clauses < 0:
        raise ValueError("Contagens negativas ou nulas no cabecalho DIMACS.")
    if declared_clauses != len(clauses):
        raise ValueError(
            f"Numero de clausulas inconsistente: cabecalho declara {declared_clauses}, "
            f"mas foram geradas {len(clauses)}."
        )
    for clause in clauses:
        for literal in clause:
            if literal == 0 or abs(literal) > num_vars:
                raise ValueError(f"Literal fora do intervalo 1..{num_vars}: {literal}.")
    return num_vars, declared_clauses


def _tokenize_row(line):
    return line.split() if any(char.isspace() for char in line) else list(line)


def _parse_clue(token):
    if token in EMPTY_TOKENS:
        return None
    if token in {"0", "1", "2", "3", "4"}:
        return int(token)
    raise ValueError(f"Dica invalida: {token!r}. Use apenas valores de 0 a 4 ou '.'.")


def parse_grid_lines(lines):
    cleaned = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]
    if not cleaned:
        raise ValueError("A instancia esta vazia.")

    first_tokens = cleaned[0].split()
    has_dimensions = len(first_tokens) == 2 and all(token.isdigit() for token in first_tokens)
    if has_dimensions:
        rows, cols = map(int, first_tokens)
        raw_rows = cleaned[1:]
        if rows <= 0 or cols <= 0:
            raise ValueError("As dimensoes da grade devem ser positivas.")
        if len(raw_rows) != rows:
            raise ValueError(f"Esperadas {rows} linhas de celulas, recebidas {len(raw_rows)}.")
    else:
        raw_rows = cleaned
        rows = len(raw_rows)
        cols = len(_tokenize_row(raw_rows[0]))

    grid = []
    for row_number, raw_row in enumerate(raw_rows, start=1):
        tokens = _tokenize_row(raw_row)
        if len(tokens) != cols:
            raise ValueError(
                f"Linha {row_number} possui {len(tokens)} celulas; eram esperadas {cols}."
            )
        grid.append([_parse_clue(token) for token in tokens])

    return rows, cols, grid


def parse_grid_file(filepath):
    with open(filepath, "r", encoding="utf-8") as instance_file:
        return parse_grid_lines(instance_file)

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 gerador.py <arquivo_instancia.txt>", file=sys.stderr)
        print("Ou:   python3 gerador.py <linhas> <colunas> <dicas_string>", file=sys.stderr)
        sys.exit(1)

    try:
        if os.path.isfile(sys.argv[1]):
            rows, cols, grid = parse_grid_file(sys.argv[1])
        elif len(sys.argv) == 4:
            rows = int(sys.argv[1])
            cols = int(sys.argv[2])
            inline_lines = [f"{rows} {cols}", *sys.argv[3].splitlines()]
            rows, cols, grid = parse_grid_lines(inline_lines)
        else:
            raise ValueError("Instancia invalida ou arquivo nao encontrado.")

        print(SlitherlinkCNF(rows, cols, grid).generate_dimacs())
    except (OSError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(2)

if __name__ == '__main__':
    main()
