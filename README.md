# Trabalho de Lógica para Ciência da Computação (2026.1)
**Professor**: Luis Henrique Bustamante (luis.bustamante@ufca.edu.br)  
**Problema Selecionado**: Problema 11 - Slitherlink (Puzzles de Percurso)  

---

## Estrutura do Repositório

```text
trabalho/
├── gerador.py            # Gerador CLI de instâncias no formato DIMACS CNF
├── solver_runner.py      # Automação do benchmark e reconstrução ASCII das soluções
├── relatorio.md          # Relatório completo do trabalho em formato Markdown
├── relatorio.pdf          # Relatório completo do trabalho compilado em PDF
├── Makefile              # Automação para execução dos testes e compilação
├── instancias/           # Instâncias de teste (.txt e .cnf)
│   ├── instancia1_3x3_sat.cnf
│   ├── instancia2_4x4_sat.cnf
│   ├── instancia3_5x5_sat.cnf
│   ├── instancia4_6x6_sat.cnf
│   ├── instancia5_3x3_unsat.cnf
│   └── problema11_base.cnf
└── solvers/              # Executáveis compilados dos SAT Solvers
    ├── cadical
    └── kissat
```

---

## Como Executar

### 1. Gerar Instância no Formato DIMACS CNF
Para gerar o arquivo `.cnf` a partir de um arquivo de especificações da grade:
```bash
python3 gerador.py instancias/instancia1_3x3_sat.txt > instancias/instancia1_3x3_sat.cnf
```

### 2. Executar os SAT Solvers e o Benchmark
Para rodar a automação de testes com os solvers **CaDiCaL** e **Kissat** sobre todas as instâncias e visualizar as soluções reconstruídas em ASCII:
```bash
python3 solver_runner.py
```
ou via `Makefile`:
```bash
make test
```

### 3. Executar o SAT Solver Diretamente via Linha de Comando
```bash
./solvers/cadical instancias/instancia1_3x3_sat.cnf
./solvers/kissat instancias/instancia1_3x3_sat.cnf
```

---

## Requisitos
- Python 3.8+
- Compilador C/C++ (`gcc` / `g++`) e `make` (caso deseje recompilar os solvers em `solvers/`)
