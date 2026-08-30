# Slitherlink em SAT

Trabalho da disciplina **Logica para Ciencia da Computacao (2026.1)** da Universidade Federal do Cariri. O projeto formaliza o Problema 11, Slitherlink, em CNF, resolve as instancias com CaDiCaL e Kissat e elimina ciclos desconectados por refinamento iterativo.

Repositorio: <https://github.com/santos-ag/slitherlink-solver>

## Integrantes

| Integrante | Responsabilidade principal |
| --- | --- |
| Arthur Oliveira | Variaveis proposicionais, restricoes de celulas e vertices, gerador DIMACS |
| Joao Caique | Deteccao de componentes, clausulas de bloqueio e refinamento CEGAR |
| Gustavo Alexandre dos Santos | Instancias, experimentos, visualizacao e consolidacao do relatorio |

## Requisitos

- Python 3.10 ou superior;
- Linux x86-64 para usar os binarios empacotados de CaDiCaL e Kissat;
- `matplotlib`, apenas para saida grafica PNG ou PDF;
- Chromium, opcionalmente, para recompilar `relatorio.pdf`.

Instale a dependencia visual com:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

A saida SVG funciona sem dependencias Python externas.

## Estrutura

```text
gerador.py                 Gerador e validador DIMACS CNF
refinamento.py             Componentes conexos e cortes de subtours
solver_runner.py           Benchmark com CaDiCaL e Kissat
visualizar.py              Visualizacao antes/subtour/depois
instancias/                Entradas TXT e CNFs base
resultados/benchmark.csv   Metricas reproduziveis
relatorio/                 Fontes HTML e LaTeX do relatorio
apresentacao/              Fonte HTML dos slides
tests/                     Testes unitarios e de integracao
```

## Gerar CNF

```bash
python3 gerador.py instancias/instancia1_3x3_sat.txt > /tmp/instancia.cnf
```

O formato de entrada comeca com `R C`, seguido por exatamente `R` linhas de `C` dicas. Use `.` para celulas vazias. Valores fora de `0..4` sao rejeitados.

O gerador verifica explicitamente a contagem declarada no cabecalho `p cnf N M`, o intervalo dos literais e o terminador de cada clausula.

Tambem e possivel informar as dimensoes e as dicas diretamente:

```bash
python3 gerador.py 3 3 $'3 . .\n. 2 .\n. . 3' > /tmp/instancia.cnf
```

## Resolver e medir

Execute os dois solvers em todas as instancias:

```bash
python3 solver_runner.py --csv resultados/benchmark.csv
```

Execute somente uma combinacao:

```bash
python3 solver_runner.py --solver cadical --instance instancias/instancia3_5x5_sat.txt
```

O CNF gerado inicialmente codifica dicas, graus e a existencia de um laco. A conectividade global e garantida pelo runner: cada modelo com multiplos ciclos recebe uma clausula de bloqueio e e resolvido novamente. Portanto, para validar completamente uma instancia Slitherlink, use `solver_runner.py`, nao apenas uma chamada direta ao CNF base.

## Visualizar

SVG sem dependencias externas:

```bash
python3 visualizar.py instancias/instancia3_5x5_sat.txt \
  --solver kissat \
  --output resultados/instancia3_5x5_refinamento.svg
```

Com `matplotlib` instalado, informe uma saida `.png` para gerar imagem rasterizada.

## Testar

```bash
python3 -m unittest discover -v
```

Ou use os alvos:

```bash
make test
make benchmark
make visualize
make report
make presentation
```

## Resultados resumidos

- `instancia1_3x3_sat`: SAT em uma iteracao;
- `instancia3_5x5_sat`: SAT e requer refinamento, com duas iteracoes no CaDiCaL e tres no Kissat no experimento registrado;
- quatro instancias UNSAT, incluindo o `problema11_base`.

Os tempos e as contagens completas estao em `resultados/benchmark.csv` e no relatorio.
