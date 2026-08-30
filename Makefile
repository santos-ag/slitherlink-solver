.PHONY: all install test benchmark visualize report presentation clean

all: test benchmark

install:
	python3 -m pip install -r requirements.txt

test:
	python3 -m unittest discover -v

benchmark:
	python3 solver_runner.py --csv resultados/benchmark.csv

visualize:
	python3 visualizar.py instancias/instancia3_5x5_sat.txt --solver kissat --output resultados/instancia3_5x5_refinamento.svg

report:
	chromium --headless --no-sandbox --disable-gpu --no-pdf-header-footer --print-to-pdf=relatorio.pdf file://$(CURDIR)/relatorio/relatorio.html

presentation:
	chromium --headless --no-sandbox --disable-gpu --no-pdf-header-footer --print-to-pdf=apresentacao.pdf file://$(CURDIR)/apresentacao/apresentacao.html

clean:
	rm -f instancias/*.tmp.cnf
