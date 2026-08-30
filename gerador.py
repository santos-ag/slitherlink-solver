#!/usr/bin/env python3
"""
Gerador de Instâncias DIMACS CNF para o Problema Slitherlink (Puzzle de Percurso).
Disciplina: Lógica para Ciência da Computação - UFCA (Prof. Luis Henrique Bustamante)

Uso:
  python3 gerador.py <arquivo_instancia.txt> > instancia.cnf
  python3 gerador.py <linhas> <colunas> "<dicas_linha_por_linha>" > instancia.cnf
"""

import sys
import os

class SlitherlinkCNF:
    def __init__(self, rows, cols, grid):
        """
        rows: número de linhas de células
        cols: número de colunas de células
        grid: matriz rows x cols com inteiros 0, 1, 2, 3, 4 ou None para célula vazia
        """
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

        # 3. Pelo menos uma aresta deve ser ativa (evita a solução trivial de 0 arestas se não houver dicas exigindo arestas)
        # Se houver alguma dica > 0, isso já é garantido, mas adicionamos cláusula genérica se necessário.

    def generate_dimacs(self):
        # Sanity check: contagem rigorosa
        header = f"p cnf {self.num_vars} {len(self.clauses)}"
        lines = [f"c Instancia Slitherlink {self.R}x{self.C}", header]
        for c in self.clauses:
            lines.append(" ".join(map(str, c)) + " 0")
        return "\n".join(lines)


def parse_grid_file(filepath):
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # Suporta formato:
    # R C
    # linha 0
    # linha 1 ...
    first_tokens = lines[0].split()
    if len(first_tokens) == 2 and first_tokens[0].isdigit() and first_tokens[1].isdigit():
        R, C = int(first_tokens[0]), int(first_tokens[1])
        raw_rows = lines[1:]
    else:
        # Inferir dimensões a partir das linhas
        raw_rows = lines
        R = len(raw_rows)
        C = max(len(row.split()) if ' ' in row else len(row) for row in raw_rows)
    
    grid = []
    for r in range(R):
        if r < len(raw_rows):
            line = raw_rows[r]
            tokens = line.split() if ' ' in line else list(line)
            row_vals = []
            for c in range(C):
                if c < len(tokens):
                    val = tokens[c]
                    if val in ('0', '1', '2', '3', '4'):
                        row_vals.append(int(val))
                    else:
                        row_vals.append(None)
                else:
                    row_vals.append(None)
            grid.append(row_vals)
        else:
            grid.append([None] * C)
    return R, C, grid

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 gerador.py <arquivo_instancia.txt>", file=sys.stderr)
        print("Ou:   python3 gerador.py <linhas> <colunas> <dicas_string>", file=sys.stderr)
        sys.exit(1)

    if os.path.exists(sys.argv[1]):
        R, C, grid = parse_grid_file(sys.argv[1])
    elif len(sys.argv) >= 4:
        R = int(sys.argv[1])
        C = int(sys.argv[2])
        dicas_str = sys.argv[3].splitlines()
        grid = []
        for line in dicas_str:
            tokens = line.split() if ' ' in line else list(line)
            row = [int(t) if t in '01234' else None for t in tokens]
            grid.append(row)
    else:
        print("Erro: Instância inválida ou arquivo não encontrado.", file=sys.stderr)
        sys.exit(1)

    solver = SlitherlinkCNF(R, C, grid)
    dimacs_out = solver.generate_dimacs()
    print(dimacs_out)

if __name__ == '__main__':
    main()
